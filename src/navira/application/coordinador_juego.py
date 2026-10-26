"""Integra las fases del modo juego sobre el mundo y resolutor compartidos."""

from __future__ import annotations

import math
from dataclasses import dataclass
from navira.application.decidir_paso import DecidirPaso, ProveedorMapas, SolicitudPaso
from navira.application.juego import UnirseAJuego
from navira.application.ordenes import OrdenHumana, RepositorioOrdenes
from navira.application.puerta_decisiones import PuertaDecisiones
from navira.application.snapshots import (
    RepositorioSnapshots,
    SnapshotObsoleto,
    abrir_siguiente_turno_persistido,
    preparar_turno_persistido,
    resolver_turno_persistido,
)
from navira.domain.modelo import (
    ControlSobreviviente,
    EstadoPartida,
    EstadoSobreviviente,
    FaseTurno,
    IntencionMovimiento,
    ModoPartida,
)
from navira.simulation.resolver import ConfiguracionReglas, ResultadoTurno
from navira.simulation.coordinador import SnapshotMundo


class JuegoIncompatible(RuntimeError):
    """La partida no está en un estado válido para la transición solicitada."""


@dataclass(frozen=True, slots=True)
class CoordinadorJuego:
    """Abre decisiones y resuelve órdenes humanas/NPC con CAS.

    `puerta_decisiones` debe compartirse con `RegistrarOrdenHumana`. El lock es
    local a un proceso; CAS sigue siendo la defensa de versión y no sustituye
    almacenamiento durable ni coordinación entre procesos.
    """

    snapshots: RepositorioSnapshots
    mapas: ProveedorMapas
    unirse: UnirseAJuego
    ordenes: RepositorioOrdenes
    decidir: DecidirPaso
    puerta_decisiones: PuertaDecisiones
    reglas: ConfiguracionReglas = ConfiguracionReglas()
    ventana_decisiones_s: float = 1.7

    def __post_init__(self) -> None:
        if not math.isfinite(self.ventana_decisiones_s) or self.ventana_decisiones_s <= 0:
            raise ValueError("La ventana de decisiones debe ser positiva y finita.")

    def preparar(
        self,
        run_id: str,
        *,
        version_esperada: int,
        inicio_turno_monotonic_s: float | None = None,
    ) -> SnapshotMundo:
        """Abre la fase de decisiones sin volver a mover zombies al reintentar."""

        with self.puerta_decisiones.lock:
            inicio = (
                self.puerta_decisiones.ahora()
                if inicio_turno_monotonic_s is None
                else inicio_turno_monotonic_s
            )
            snapshot = self._leer_juego(run_id, version_esperada)
            if snapshot.partida.fase is FaseTurno.RESUELTA:
                snapshot = abrir_siguiente_turno_persistido(
                    self.snapshots,
                    run_id,
                    version_esperada=snapshot.version,
                )
            if snapshot.partida.fase is FaseTurno.PREPARACION:
                # Las apariciones tardías se incorporan antes de cualquier
                # movimiento zombie y se confirman como snapshot completo.
                snapshot = self.unirse.incorporar_aparicion_pendiente(
                    run_id,
                    snapshot.version,
                )
                actual = self.snapshots.obtener(run_id)
                if actual is None:
                    raise JuegoIncompatible("La partida desapareció al preparar el turno.")
                snapshot = preparar_turno_persistido(
                    self.snapshots,
                    self._grafo(snapshot),
                    run_id,
                    version_esperada=actual.version,
                    configuracion=self.reglas,
                )
                self.puerta_decisiones.abrir(
                    run_id,
                    snapshot.partida.turno,
                    deadline_monotonic_s=inicio + self.ventana_decisiones_s,
                )
            if snapshot.partida.fase is not FaseTurno.DECISIONES:
                raise JuegoIncompatible("La partida no quedó abierta a decisiones.")
            return snapshot

    def resolver(
        self,
        run_id: str,
        *,
        version_esperada: int,
    ) -> tuple[SnapshotMundo, ResultadoTurno]:
        """Consume la última orden humana y decide NPC antes de una resolución."""

        with self.puerta_decisiones.lock:
            snapshot = self._leer_juego(run_id, version_esperada)
            if snapshot.partida.fase is not FaseTurno.DECISIONES:
                raise JuegoIncompatible("Solo se resuelve una fase de decisiones abierta.")
            if not self.puerta_decisiones.cerrar_si_vencida(run_id, snapshot.partida.turno):
                raise JuegoIncompatible("La ventana de decisiones todavía no venció.")
            grafo = self._grafo(snapshot)
            ultima_por_personaje = {
                orden.personaje_id: orden
                for orden in self.ordenes.obtener_turno(run_id, snapshot.partida.turno)
            }
            intenciones = tuple(
                self._intencion(snapshot, sobreviviente.id, sobreviviente.nodo, ultima_por_personaje.get(sobreviviente.id))
                for sobreviviente in snapshot.partida.sobrevivientes
                if sobreviviente.estado is EstadoSobreviviente.ACTIVO
            )
            resuelto, resultado = resolver_turno_persistido(
                self.snapshots,
                grafo,
                run_id,
                version_esperada=snapshot.version,
                intenciones=intenciones,
            )
            return resuelto, resultado

    def _intencion(
        self,
        snapshot: SnapshotMundo,
        personaje_id: str,
        nodo_actual: str,
        orden: OrdenHumana | None,
    ) -> IntencionMovimiento:
        partida = snapshot.partida
        personaje = next(item for item in partida.sobrevivientes if item.id == personaje_id)
        if personaje.control is ControlSobreviviente.HUMANO:
            # Sin orden confirmada se espera; la política automática no toma
            # el control silenciosamente cuando el jugador se desconecta.
            destino = orden.siguiente_nodo if orden is not None else nodo_actual
        else:
            decision = self.decidir.ejecutar(
                SolicitudPaso(personaje.id, personaje.nodo, partida.turno)
            )
            destino = decision.siguiente_nodo
        return IntencionMovimiento(
            run_id=partida.run_id,
            turno=partida.turno,
            fase=FaseTurno.DECISIONES,
            sobreviviente_id=personaje_id,
            destino=destino,
        )

    def _leer_juego(self, run_id: str, version_esperada: int) -> SnapshotMundo:
        snapshot = self.snapshots.obtener(run_id)
        if snapshot is None:
            raise JuegoIncompatible("La partida ya no existe.")
        if snapshot.version != version_esperada:
            raise SnapshotObsoleto("El snapshot del juego cambió antes de la transición.")
        if snapshot.partida.estado is not EstadoPartida.ACTIVA or snapshot.partida.modo is not ModoPartida.JUEGO:
            raise JuegoIncompatible("La transición requiere una partida activa en modo juego.")
        return snapshot

    def _grafo(self, snapshot: SnapshotMundo):
        grafo = self.mapas.obtener(snapshot.partida.map_version)
        if grafo is None:
            raise JuegoIncompatible("No está disponible el mapa versionado de la partida.")
        return grafo
