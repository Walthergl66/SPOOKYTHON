"""Ensamblaje explícito de un mundo local descartable para desarrollo.

El mapa cargado aquí es sintético y nunca debe usarse como representación de
Manta ni como escenario oficial de evaluación.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from navira.adapters.mapas_memoria import CatalogoMapasMemoria
from navira.adapters.snapshots_memoria import AlmacenSnapshotsMemoria
from navira.application.decidir_paso import DecidirPaso, ProveedorMapas
from navira.application.snapshots import RepositorioSnapshots
from navira.domain.mapa import Grafo, cargar_mapa
from navira.domain.modelo import (
    EstadoPartida,
    EstadoZombie,
    FaseTurno,
    ModoPartida,
    Partida,
    Sobreviviente,
    TipoZombie,
    Zombie,
)
from navira.simulation.coordinador import (
    crear_snapshot_inicial,
    preparar_turno_versionado,
)


MAPA_DEMO_POR_DEFECTO = Path(__file__).resolve().parents[2] / "data/maps/demo-sintetico.json"
ESCENARIOS_DEMO: dict[str, tuple[Zombie, ...]] = {
    "libre": (),
    "caminantes": (
        Zombie("Z-CAM-001", TipoZombie.CAMINANTE, "D-003"),
    ),
    "mixto": (
        Zombie("Z-COR-001", TipoZombie.CORREDOR, "D-005"),
        Zombie("Z-DOR-001", TipoZombie.DORMIDO, "D-003", estado=EstadoZombie.DORMIDO),
    ),
    "horda": (
        Zombie("Z-HOR-001", TipoZombie.HORDA, "D-003"),
        Zombie("Z-DOR-002", TipoZombie.DORMIDO, "D-005", estado=EstadoZombie.DORMIDO),
    ),
}


@dataclass(frozen=True, slots=True)
class ContextoDemo:
    """Dependencias efímeras compartidas por API demo y ejecutor local."""

    grafo: Grafo
    snapshots: RepositorioSnapshots
    mapas: ProveedorMapas
    servicio_decision: DecidirPaso
    run_id: str


def crear_contexto_demo(
    ruta_mapa: str | Path = MAPA_DEMO_POR_DEFECTO,
    *,
    semilla: int = 31,
    escenario: str = "libre",
    cantidad_sobrevivientes: int = 1,
) -> ContextoDemo:
    """Crea una partida sintética reproducible y expone sus dependencias.

    Los perfiles solo se definen para el mapa demo incluido; no representan
    densidad, balance ni distribución de una ronda oficial.
    """

    if (
        isinstance(cantidad_sobrevivientes, bool)
        or not isinstance(cantidad_sobrevivientes, int)
        or not 1 <= cantidad_sobrevivientes <= 200
    ):
        raise ValueError("La población debe ser un entero entre 1 y 200.")
    grafo = Grafo(cargar_mapa(ruta_mapa))
    if escenario not in ESCENARIOS_DEMO:
        opciones = ", ".join(sorted(ESCENARIOS_DEMO))
        raise ValueError(f"Escenario demo desconocido: {escenario}. Opciones: {opciones}.")
    zombies = ESCENARIOS_DEMO[escenario]
    rng = random.Random(semilla)
    nodos_refugio = {refugio.nodo for refugio in grafo.mapa.refugios}
    nodos_inicio = tuple(
        nodo.id for nodo in grafo.mapa.nodos if nodo.id not in nodos_refugio
    )
    if not nodos_inicio:
        raise ValueError("El mapa demo requiere al menos un nodo que no sea refugio.")
    if cantidad_sobrevivientes == 1 and "D-001" in grafo.mapa.nodos_por_id:
        posiciones = ("D-001",)
    else:
        posiciones = tuple(rng.choice(nodos_inicio) for _ in range(cantidad_sobrevivientes))
    partida = Partida(
        run_id="navira-demo-local",
        modo=ModoPartida.SIMULADOR,
        escenario=f"demo-sintetico-{escenario}",
        map_version=grafo.mapa.version,
        sobrevivientes=tuple(
            Sobreviviente(f"S-DEMO-{indice:03d}", nodo)
            for indice, nodo in enumerate(posiciones, start=1)
        ),
        zombies=zombies,
        estado=EstadoPartida.ACTIVA,
        turno=0,
        fase=FaseTurno.PREPARACION,
    )
    inicial = crear_snapshot_inicial(partida, grafo, rng=rng)
    snapshots = AlmacenSnapshotsMemoria()
    if not snapshots.insertar_inicial(inicial):
        raise RuntimeError("No se pudo crear la partida demo inicial.")

    decisiones, _ = preparar_turno_versionado(
        inicial,
        grafo,
        version_esperada=inicial.version,
    )
    if not snapshots.guardar_si_version(
        partida.run_id,
        inicial.version,
        decisiones,
    ):
        raise RuntimeError("No se pudo confirmar la fase de decisiones demo.")

    mapas = CatalogoMapasMemoria((grafo,))
    return ContextoDemo(
        grafo=grafo,
        snapshots=snapshots,
        mapas=mapas,
        servicio_decision=DecidirPaso(snapshots, mapas),
        run_id=partida.run_id,
    )


def crear_servicio_demo(
    ruta_mapa: str | Path = MAPA_DEMO_POR_DEFECTO,
    *,
    semilla: int = 31,
    escenario: str = "libre",
    cantidad_sobrevivientes: int = 1,
) -> DecidirPaso:
    """Compatibilidad para API: crea el contexto y devuelve su planificador."""

    return crear_contexto_demo(
        ruta_mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=cantidad_sobrevivientes,
    ).servicio_decision
