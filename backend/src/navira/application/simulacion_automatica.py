"""Caso de uso para completar un turno automático sobre snapshots CAS."""

from __future__ import annotations

from threading import RLock

from navira.application.decidir_paso import DecidirPaso, ProveedorMapas, SolicitudPaso
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
    Sobreviviente,
)
from navira.simulation.resolver import ConfiguracionReglas, ResultadoTurno


class SimulacionIncompatible(RuntimeError):
    """El estado no puede avanzar como una ronda automática."""


class EjecutarRondaAutomatica:
    """Avanza una partida de simulador a través de una resolución completa.

    Cada fase completa se confirma con CAS. Si el proceso se interrumpe tras
    abrir decisiones, el siguiente intento las retoma sin volver a mover los
    zombies. El repositorio actual es local en memoria y admite un solo proceso.
    """

    def __init__(
        self,
        snapshots: RepositorioSnapshots,
        mapas: ProveedorMapas,
        *,
        reglas: ConfiguracionReglas = ConfiguracionReglas(),
        decidir: DecidirPaso | None = None,
        bloqueo_operador: RLock | None = None,
    ) -> None:
        self._snapshots = snapshots
        self._mapas = mapas
        self._reglas = reglas
        self._decidir = decidir or DecidirPaso(snapshots, mapas)
        self._bloqueo_operador = bloqueo_operador or RLock()

    def ejecutar(self, run_id: str, *, version_esperada: int) -> ResultadoTurno:
        """Prepara si hace falta, decide para cada sobreviviente y resuelve."""

        # El operador escribe sobre el mismo snapshot; serializar la ronda
        # completa evita que una colocación válida invalide el CAS del reloj.
        with self._bloqueo_operador:
            return self._ejecutar_bajo_bloqueo(run_id, version_esperada=version_esperada)

    def _ejecutar_bajo_bloqueo(self, run_id: str, *, version_esperada: int) -> ResultadoTurno:

        snapshot = self._snapshots.obtener(run_id)
        if snapshot is None:
            raise KeyError(f"No existe una partida con run_id {run_id}.")
        if snapshot.version != version_esperada:
            raise SnapshotObsoleto("El snapshot vigente cambió antes de iniciar la ronda.")
        partida = snapshot.partida
        if partida.estado is not EstadoPartida.ACTIVA or partida.modo is not ModoPartida.SIMULADOR:
            raise SimulacionIncompatible("La ronda automática requiere una partida activa en modo simulador.")
        if any(
            survivor.estado is EstadoSobreviviente.ACTIVO
            and survivor.control is not ControlSobreviviente.AUTOMATICO
            for survivor in partida.sobrevivientes
        ):
            raise SimulacionIncompatible("El simulador automático no admite sobrevivientes humanos.")
        activa = self._snapshots.obtener_activa()
        if activa is None or activa.partida.run_id != run_id:
            raise SimulacionIncompatible("La partida no es el mundo activo del repositorio.")

        if partida.fase is FaseTurno.RESUELTA:
            snapshot = abrir_siguiente_turno_persistido(
                self._snapshots,
                run_id,
                version_esperada=snapshot.version,
            )
            partida = snapshot.partida
        if partida.fase is FaseTurno.PREPARACION:
            grafo = self._mapas.obtener(partida.map_version)
            if grafo is None:
                raise SimulacionIncompatible("No está disponible el mapa versionado de la partida.")
            snapshot = preparar_turno_persistido(
                self._snapshots,
                grafo,
                run_id,
                version_esperada=snapshot.version,
                configuracion=self._reglas,
            )
            partida = snapshot.partida
        if partida.fase is not FaseTurno.DECISIONES:
            raise SimulacionIncompatible("La partida no está abierta a decisiones automáticas.")

        grafo = self._mapas.obtener(partida.map_version)
        if grafo is None:
            raise SimulacionIncompatible("No está disponible el mapa versionado de la partida.")
        intenciones = tuple(
            self._intencion_automatica(sobreviviente, partida.run_id, partida.turno)
            for sobreviviente in partida.sobrevivientes
            if sobreviviente.estado is EstadoSobreviviente.ACTIVO
        )
        rutas_propuestas = {
            survivor.id: compromiso
            for survivor in partida.sobrevivientes
            if survivor.estado is EstadoSobreviviente.ACTIVO
            for compromiso in (
                self._decidir.proponer_compromiso_en_snapshot(snapshot, survivor.id, grafo),
            )
        }
        _, resultado = resolver_turno_persistido(
            self._snapshots,
            grafo,
            run_id,
            version_esperada=snapshot.version,
            intenciones=intenciones,
            rutas_propuestas=rutas_propuestas,
        )
        return resultado

    def _intencion_automatica(
        self, sobreviviente: Sobreviviente, run_id: str, turno: int
    ) -> IntencionMovimiento:
        if sobreviviente.control is not ControlSobreviviente.AUTOMATICO:
            raise SimulacionIncompatible("El simulador automático no admite control humano.")
        decision = self._decidir.ejecutar(
            SolicitudPaso(sobreviviente.id, sobreviviente.nodo, turno)
        )
        return IntencionMovimiento(
            run_id=run_id,
            turno=turno,
            fase=FaseTurno.DECISIONES,
            sobreviviente_id=sobreviviente.id,
            destino=decision.siguiente_nodo,
        )
