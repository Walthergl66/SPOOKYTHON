"""Proyección de peligros visibles; excluye dormidos para no filtrarlos."""

from __future__ import annotations

from navira.domain.mapa import Grafo
from navira.domain.modelo import EstadoZombie, TipoZombie
from navira.domain.snapshot import SnapshotMundo


def peligros_visibles(
    snapshot: SnapshotMundo, grafo: Grafo
) -> tuple[set[str], frozenset[str]]:
    """Proyecta ocupación/horda y cruces visibles para decisión y panel.

    Solo considera zombies activos para no filtrar dormidos ocultos. Las hordas
    también bloquean todos sus vecinos topológicos, incluso si el tramo que
    los conecta está cerrado por un incidente.
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
                for calle in grafo.salientes(tramo.destino)
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
        bloqueados.update(calle.destino for calle in grafo.salientes(zombie.nodo))
        # La regla de horda es topológica: los cierres de incidentes no reducen
        # el perímetro que bloquea. La tabla entrante vacía se calcula una vez.
        bloqueados.update(grafo.entrantes_habilitadas(frozenset(), frozenset())[zombie.nodo])
    return frozenset(bloqueados)
