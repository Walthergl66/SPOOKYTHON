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
    Sobreviviente,
    TipoZombie,
)
from navira.routing.dijkstra import PerfilCostos, Ruta, seleccionar_refugio
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
        snapshot, sobreviviente, grafo = self._obtener_contexto(solicitud)
        ruta = self._seleccionar_ruta(snapshot, grafo, sobreviviente)
        destino = ruta.siguiente_nodo if ruta is not None else None
        return DecisionPaso(destino or sobreviviente.nodo)

    def prever_ruta(self, solicitud: SolicitudPaso) -> tuple[str, ...]:
        """Devuelve ruta dirigida desde el mismo snapshot y filtro que `/paso`.

        Es una vista previa de decisión, no un movimiento confirmado ni una
        garantía de seguridad. Si no hay ruta, la recomendación es esperar en
        el nodo actual.
        """

        snapshot, sobreviviente, grafo = self._obtener_contexto(solicitud)
        ruta = self._seleccionar_ruta(snapshot, grafo, sobreviviente)
        if ruta is None:
            return (sobreviviente.nodo,)
        return (ruta.origen, *(calle.destino for calle in ruta.calles))

    def _obtener_contexto(self, solicitud: SolicitudPaso) -> tuple[SnapshotMundo, Sobreviviente, Grafo]:
        """Valida identidad temporal y carga el grafo antes de planificar."""

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

        return snapshot, sobreviviente, grafo

    def _seleccionar_ruta(
        self, snapshot: SnapshotMundo, grafo: Grafo, sobreviviente: Sobreviviente
    ) -> Ruta | None:
        """Usa exactamente los peligros observables de la recomendación HTTP."""

        nodos_bloqueados, aristas_peligrosas = peligros_visibles(snapshot, grafo)
        return seleccionar_refugio(
            grafo,
            sobreviviente.nodo,
            refugio_objetivo=sobreviviente.refugio_objetivo,
            aristas_cerradas=snapshot.aristas_cerradas | aristas_peligrosas,
            segmentos_cerrados=snapshot.segmentos_cerrados,
            nodos_bloqueados=frozenset(nodos_bloqueados),
            perfil=self._perfil,
        )

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


def peligros_visibles(
    snapshot: SnapshotMundo, grafo: Grafo
) -> tuple[set[str], frozenset[str]]:
    """Proyecta ocupación/horda y cruces visibles para decisión y panel.

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
    nodos.update(nodos_horda_visibles(snapshot, grafo))

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


def nodos_horda_visibles(snapshot: SnapshotMundo, grafo: Grafo) -> frozenset[str]:
    """Lista nodos ocupados o vecinos bloqueados por hordas ya visibles."""

    bloqueados: set[str] = set()
    for zombie in snapshot.partida.zombies:
        if zombie.estado is not EstadoZombie.ACTIVO or zombie.tipo is not TipoZombie.HORDA:
            continue
        bloqueados.add(zombie.nodo)
        bloqueados.update(
            calle.destino
            for calle in grafo.calles_desde(
                zombie.nodo,
                aristas_cerradas=snapshot.aristas_cerradas,
                segmentos_cerrados=snapshot.segmentos_cerrados,
            )
        )
        bloqueados.update(
            calle.origen
            for calle in grafo.mapa.calles
            if calle.destino == zombie.nodo
            and calle.id not in snapshot.aristas_cerradas
            and calle.segmento_id not in snapshot.segmentos_cerrados
        )
    return frozenset(bloqueados)
