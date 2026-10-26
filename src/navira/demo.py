"""Ensamblaje explícito de un mundo local descartable para desarrollo.

El mapa cargado aquí es sintético y nunca debe usarse como representación de
Manta ni como escenario oficial de evaluación.
"""

from __future__ import annotations

import random
from pathlib import Path

from navira.adapters.mapas_memoria import CatalogoMapasMemoria
from navira.adapters.snapshots_memoria import AlmacenSnapshotsMemoria
from navira.application.decidir_paso import DecidirPaso
from navira.domain.mapa import Grafo, cargar_mapa
from navira.domain.modelo import (
    EstadoPartida,
    FaseTurno,
    ModoPartida,
    Partida,
    Sobreviviente,
)
from navira.simulation.coordinador import (
    crear_snapshot_inicial,
    preparar_turno_versionado,
)


MAPA_DEMO_POR_DEFECTO = Path(__file__).resolve().parents[2] / "data/maps/demo-sintetico.json"


def crear_servicio_demo(
    ruta_mapa: str | Path = MAPA_DEMO_POR_DEFECTO,
    *,
    semilla: int = 31,
) -> DecidirPaso:
    """Crea una partida demo en decisiones sobre un snapshot versionado.

    Siembra un sobreviviente en D-001, confirma versión cero en preparación y
    aplica el coordinador una vez para abrir el turno de decisiones. Los
    repositorios viven solo mientras vive el proceso.
    """

    grafo = Grafo(cargar_mapa(ruta_mapa))
    partida = Partida(
        run_id="navira-demo-local",
        modo=ModoPartida.SIMULADOR,
        escenario="demo-sintetico",
        map_version=grafo.mapa.version,
        sobrevivientes=(Sobreviviente("S-DEMO-001", "D-001"),),
        estado=EstadoPartida.ACTIVA,
        turno=0,
        fase=FaseTurno.PREPARACION,
    )
    inicial = crear_snapshot_inicial(partida, grafo, rng=random.Random(semilla))
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
    return DecidirPaso(snapshots, mapas)
