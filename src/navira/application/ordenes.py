"""Registro autenticado de órdenes humanas por turno."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from typing import Protocol

from navira.application.decidir_paso import ProveedorMapas, nodos_horda_visibles
from navira.application.juego import EstadoSesion, RepositorioSesiones, SesionExpirada
from navira.application.puerta_decisiones import PuertaDecisiones
from navira.application.snapshots import RepositorioSnapshots
from navira.domain.modelo import (
    ControlSobreviviente,
    EstadoPartida,
    EstadoSobreviviente,
    FaseTurno,
    ModoPartida,
)


@dataclass(frozen=True, slots=True)
class OrdenHumana:
    """Orden aceptada, identificada por el turno y su secuencia de servidor."""

    run_id: str
    turno: int
    personaje_id: str
    accion_id: str
    siguiente_nodo: str
    secuencia: int = 0
    version_snapshot: int = 0


class RepositorioOrdenes(Protocol):
    def buscar_accion(self, run_id: str, personaje_id: str, accion_id: str) -> OrdenHumana | None: ...
    def obtener_ultima(self, run_id: str, personaje_id: str) -> OrdenHumana | None: ...
    def registrar(self, orden: OrdenHumana) -> OrdenHumana: ...
    def obtener_turno(self, run_id: str, turno: int) -> tuple[OrdenHumana, ...]: ...


class SesionNoAutorizada(PermissionError):
    """La cookie no identifica una sesión activa propietaria."""


class OrdenIncompatible(ValueError):
    """La orden no coincide con el modo, fase, turno o posición confirmada."""


class OrdenIdempotenciaConflict(ValueError):
    """Una clave de idempotencia fue reutilizada con un cuerpo distinto."""


@dataclass(frozen=True, slots=True)
class RegistrarOrdenHumana:
    """Autoriza y registra el próximo destino; nunca mueve el personaje."""

    snapshots: RepositorioSnapshots
    mapas: ProveedorMapas
    sesiones: RepositorioSesiones
    ordenes: RepositorioOrdenes
    puerta_decisiones: PuertaDecisiones | None = None

    def ejecutar(
        self,
        token: str | None,
        *,
        run_id: str,
        turno: int,
        personaje_id: str,
        siguiente_nodo: str,
        accion_id: str,
    ) -> OrdenHumana:
        # La misma puerta debe proteger la resolución para que una orden que
        # compita con el cierre quede inequívocamente antes o después de ella.
        puerta = self.puerta_decisiones
        with puerta.lock if puerta is not None else nullcontext():
            return self._ejecutar(
                token,
                run_id=run_id,
                turno=turno,
                personaje_id=personaje_id,
                siguiente_nodo=siguiente_nodo,
                accion_id=accion_id,
            )

    def _ejecutar(
        self,
        token: str | None,
        *,
        run_id: str,
        turno: int,
        personaje_id: str,
        siguiente_nodo: str,
        accion_id: str,
    ) -> OrdenHumana:
        puerta = self.puerta_decisiones
        if not token:
            raise SesionNoAutorizada("Se requiere la sesión propietaria.")
        sesion = self.sesiones.obtener(token)
        if sesion is None and self.sesiones.expirada(token):
            raise SesionExpirada("La sesión venció; esta partida no admite otro personaje humano.")
        if (
            sesion is None
            or sesion.estado is not EstadoSesion.ACTIVO
            or sesion.run_id != run_id
            or sesion.sobreviviente_id != personaje_id
        ):
            raise SesionNoAutorizada("La sesión no controla este personaje.")

        propuesta = OrdenHumana(
            run_id=run_id,
            turno=turno,
            personaje_id=personaje_id,
            accion_id=accion_id,
            siguiente_nodo=siguiente_nodo,
        )
        anterior = self.ordenes.buscar_accion(run_id, personaje_id, accion_id)
        if anterior is not None:
            if _contenido(anterior) != _contenido(propuesta):
                raise OrdenIdempotenciaConflict("accionId ya fue usado con otro contenido.")
            return anterior

        if puerta is not None and not puerta.acepta(run_id, turno):
            raise OrdenIncompatible("La ventana de decisiones de este turno está cerrada.")

        snapshot = self.snapshots.obtener(run_id)
        if snapshot is None:
            raise OrdenIncompatible("La partida ya no existe.")
        partida = snapshot.partida
        if (
            partida.estado is not EstadoPartida.ACTIVA
            or partida.modo is not ModoPartida.JUEGO
            or partida.fase is not FaseTurno.DECISIONES
            or partida.turno != turno
        ):
            raise OrdenIncompatible("La partida no acepta órdenes en este turno o fase.")
        personaje = next((item for item in partida.sobrevivientes if item.id == personaje_id), None)
        if (
            personaje is None
            or personaje.control is not ControlSobreviviente.HUMANO
            or personaje.estado is not EstadoSobreviviente.ACTIVO
        ):
            raise SesionNoAutorizada("El personaje ya no está activo o la sesión no lo controla.")
        grafo = self.mapas.obtener(partida.map_version)
        if grafo is None:
            raise OrdenIncompatible("No está disponible la versión del mapa de la partida.")
        partida.validar_mapa(grafo.mapa)
        if siguiente_nodo not in grafo.mapa.nodos_por_id:
            raise OrdenIncompatible("El destino no pertenece al mapa de la partida.")
        if siguiente_nodo != personaje.nodo:
            calles_habilitadas = grafo.calles_desde(
                personaje.nodo,
                aristas_cerradas=snapshot.aristas_cerradas,
                segmentos_cerrados=snapshot.segmentos_cerrados,
            )
            if not any(calle.destino == siguiente_nodo for calle in calles_habilitadas):
                raise OrdenIncompatible("El destino debe ser espera o un vecino por calle abierta.")
            if siguiente_nodo in nodos_horda_visibles(snapshot, grafo):
                raise OrdenIncompatible("La horda bloquea ese destino.")

        return self.ordenes.registrar(
            OrdenHumana(
                run_id=run_id,
                turno=turno,
                personaje_id=personaje_id,
                accion_id=accion_id,
                siguiente_nodo=siguiente_nodo,
                version_snapshot=snapshot.version,
            )
        )


def _contenido(orden: OrdenHumana) -> tuple[str, int, str, str]:
    """Campos que identifican el mismo contenido idempotente."""

    return (orden.run_id, orden.turno, orden.personaje_id, orden.siguiente_nodo)
