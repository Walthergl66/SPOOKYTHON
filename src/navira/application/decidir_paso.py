"""Política de ruta desde el único snapshot activo conocido por la aplicación."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from navira.domain.mapa import Grafo
from navira.domain.modelo import (
    EstadoPartida,
    EstadoSobreviviente,
    EstadoZombie,
    FaseTurno,
    Partida,
    TipoZombie,
)
from navira.routing.dijkstra import PerfilCostos, seleccionar_refugio
from navira.simulation.coordinador import SnapshotMundo


@dataclass(frozen=True, slots=True)
class SolicitudPaso:
    """Datos del sobreviviente recibidos para una decisión."""

    sobreviviente_id: str
    nodo_actual: str
    turno: int


@dataclass(frozen=True, slots=True)
class DecisionPaso:
    """Destino propuesto; el servidor resuelve y confirma el movimiento después."""

    siguiente_nodo: str


class PartidaNoDisponible(RuntimeError):
    """No existe un snapshot/mapa de partida vigente y usable."""


class PasoIncompatible(RuntimeError):
    """Turno, fase, personaje o posición no coinciden con el mundo vigente."""


class EntidadNoEncontrada(LookupError):
    """El personaje indicado no existe en la partida activa."""


class ProveedorSnapshotsActivos(Protocol):
    def obtener_activa(self) -> SnapshotMundo | None:
        """Devuelve la única partida activa o nada si no hay partida."""


class ProveedorMapas(Protocol):
    def obtener(self, version: str) -> Grafo | None:
        """Busca un grafo validado por su versión inmutable."""


class DecidirPaso:
    """Calcula una recomendación determinista sobre el estado server-side.

    Solo usa zombies activos, bloqueos y cruces observables en la fase actual.
    Dormidos no intervienen en la proyección de riesgo. Si no hay ruta segura
    conocida, devuelve espera; esto no equivale a una garantía de supervivencia.
    """

    def __init__(
        self,
        snapshots: ProveedorSnapshotsActivos,
        mapas: ProveedorMapas,
        *,
        perfil: PerfilCostos = PerfilCostos(),
    ) -> None:
        self._snapshots = snapshots
        self._mapas = mapas
        self._perfil = perfil

    def ejecutar(self, solicitud: SolicitudPaso) -> DecisionPaso:
        try:
            snapshot = self._snapshots.obtener_activa()
        except RuntimeError as error:
            raise PartidaNoDisponible("El repositorio no tiene una única partida activa.") from error
        if snapshot is None:
            raise PartidaNoDisponible("No hay una partida activa.")
        partida = snapshot.partida
        self._validar_turno(partida, solicitud)
        sobreviviente = next(
            (item for item in partida.sobrevivientes if item.id == solicitud.sobreviviente_id),
            None,
        )
        if sobreviviente is None:
            raise EntidadNoEncontrada("El sobreviviente no existe en la partida activa.")
        if sobreviviente.estado is not EstadoSobreviviente.ACTIVO:
            raise PasoIncompatible("El sobreviviente ya no puede tomar decisiones.")
        if sobreviviente.nodo != solicitud.nodo_actual:
            raise PasoIncompatible("El nodo indicado no coincide con la posición confirmada.")

        grafo = self._mapas.obtener(partida.map_version)
        if grafo is None:
            raise PartidaNoDisponible("No está disponible la versión de mapa de la partida.")
        partida.validar_mapa(grafo.mapa)
        nodos_bloqueados, aristas_peligrosas = _peligros_visibles(snapshot, grafo)
        ruta = seleccionar_refugio(
            grafo,
            sobreviviente.nodo,
            refugio_objetivo=sobreviviente.refugio_objetivo,
            aristas_cerradas=snapshot.aristas_cerradas | aristas_peligrosas,
            segmentos_cerrados=snapshot.segmentos_cerrados,
            nodos_bloqueados=frozenset(nodos_bloqueados),
            perfil=self._perfil,
        )
        destino = ruta.siguiente_nodo if ruta is not None else None
        return DecisionPaso(destino or sobreviviente.nodo)

    @staticmethod
    def _validar_turno(partida: Partida, solicitud: SolicitudPaso) -> None:
        if partida.estado is not EstadoPartida.ACTIVA:
            raise PartidaNoDisponible("La partida activa no está disponible para decisiones.")
        if partida.turno != solicitud.turno or partida.fase is not FaseTurno.DECISIONES:
            raise PasoIncompatible("La solicitud pertenece a otro turno o fase.")


class DecidirPasoEspera:
    """Respaldo local cuando todavía no se ensambla un estado de juego."""

    def ejecutar(self, solicitud: SolicitudPaso) -> DecisionPaso:
        """Espera válida del contrato; no afirma que el nodo sea seguro."""

        return DecisionPaso(siguiente_nodo=solicitud.nodo_actual)


def _peligros_visibles(
    snapshot: SnapshotMundo, grafo: Grafo
) -> tuple[set[str], frozenset[str]]:
    """Bloquea ocupación zombie actual y cruces conocidos de este turno.

    Solo considera zombies activos para no filtrar dormidos ocultos. Las hordas
    también bloquean vecinos entrantes/salientes según cierres vigentes.
    """

    partida = snapshot.partida
    nodos: set[str] = set()
    aristas_cruzadas: set[str] = set()
    for zombie in partida.zombies:
        if zombie.estado is not EstadoZombie.ACTIVO:
            continue
        nodos.add(zombie.nodo)
        if zombie.tipo is TipoZombie.HORDA:
            nodos.update(
                calle.destino
                for calle in grafo.calles_desde(
                    zombie.nodo,
                    aristas_cerradas=snapshot.aristas_cerradas,
                    segmentos_cerrados=snapshot.segmentos_cerrados,
                )
            )
            nodos.update(
                calle.origen
                for calle in grafo.mapa.calles
                if calle.destino == zombie.nodo
                and calle.id not in snapshot.aristas_cerradas
                and calle.segmento_id not in snapshot.segmentos_cerrados
            )

    for movimiento in snapshot.movimientos_zombies:
        for tramo in movimiento.tramos:
            aristas_cruzadas.update(
                calle.id
                for calle in grafo.mapa.calles
                if calle.segmento_id == tramo.segmento_id
                and calle.origen == tramo.destino
                and calle.destino == tramo.origen
            )
    return nodos, frozenset(aristas_cruzadas)
