"""Ensamblaje explícito de un mundo local descartable para desarrollo.

El mapa cargado aquí es sintético y nunca debe usarse como representación de
Manta ni como escenario oficial de evaluación.
"""

from __future__ import annotations

import random
import secrets
import uuid
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
MAPA_MANTA_POR_DEFECTO = Path(__file__).resolve().parents[2] / "data/maps/manta-hackathon-v1.json"
_COMPOSICION_ZOMBIES_DEMO: dict[str, tuple[tuple[str, TipoZombie, EstadoZombie], ...]] = {
    "libre": (),
    "caminantes": (("Z-CAM-001", TipoZombie.CAMINANTE, EstadoZombie.ACTIVO),),
    "mixto": (
        ("Z-COR-001", TipoZombie.CORREDOR, EstadoZombie.ACTIVO),
        ("Z-DOR-001", TipoZombie.DORMIDO, EstadoZombie.DORMIDO),
    ),
    "horda": (
        ("Z-HOR-001", TipoZombie.HORDA, EstadoZombie.ACTIVO),
        ("Z-DOR-002", TipoZombie.DORMIDO, EstadoZombie.DORMIDO),
    ),
}
ESCENARIOS_DEMO = _COMPOSICION_ZOMBIES_DEMO


@dataclass(frozen=True, slots=True)
class ContextoDemo:
    """Dependencias efímeras compartidas por API demo y ejecutor local."""

    grafo: Grafo
    snapshots: RepositorioSnapshots
    mapas: ProveedorMapas
    servicio_decision: DecidirPaso
    run_id: str
    semilla: int


def crear_contexto_demo(
    ruta_mapa: str | Path = MAPA_DEMO_POR_DEFECTO,
    *,
    semilla: int | None = None,
    escenario: str = "libre",
    cantidad_sobrevivientes: int = 1,
    modo: ModoPartida = ModoPartida.SIMULADOR,
    preparar_inicial: bool = True,
) -> ContextoDemo:
    """Crea una partida con estado inicial aleatorio y expone dependencias.

    Sin semilla explícita, obtiene una semilla de la entropía del sistema.
    Los perfiles son fixtures; no representan distribuciones oficiales.
    """

    if (
        isinstance(cantidad_sobrevivientes, bool)
        or not isinstance(cantidad_sobrevivientes, int)
        or not 1 <= cantidad_sobrevivientes <= 200
    ):
        raise ValueError("La población debe ser un entero entre 1 y 200.")
    if semilla is not None and (isinstance(semilla, bool) or not isinstance(semilla, int)):
        raise ValueError("La semilla debe ser un entero o None.")
    if not isinstance(modo, ModoPartida):
        raise ValueError("El modo demo no es válido.")
    grafo = Grafo(cargar_mapa(ruta_mapa))
    if escenario not in ESCENARIOS_DEMO:
        opciones = ", ".join(sorted(ESCENARIOS_DEMO))
        raise ValueError(f"Escenario demo desconocido: {escenario}. Opciones: {opciones}.")
    semilla_real = secrets.randbits(64) if semilla is None else semilla
    rng = random.Random(semilla_real)
    nodos_refugio = {refugio.nodo for refugio in grafo.mapa.refugios}
    nodos_inicio = _nodos_inicio_elegibles(grafo, nodos_refugio)
    if not nodos_inicio:
        raise ValueError("El mapa demo requiere un nodo transitable con ruta a algún refugio.")
    if cantidad_sobrevivientes <= len(nodos_inicio):
        posiciones = tuple(rng.sample(nodos_inicio, cantidad_sobrevivientes))
    else:
        posiciones = tuple(rng.choice(nodos_inicio) for _ in range(cantidad_sobrevivientes))
    zombies = _crear_zombies_demo(escenario, nodos_inicio, posiciones, rng)
    run_id = f"navira-demo-{uuid.uuid4().hex}"
    partida = Partida(
        run_id=run_id,
        modo=modo,
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

    if preparar_inicial:
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
        semilla=semilla_real,
    )


def crear_contexto_juego_demo(
    ruta_mapa: str | Path = MAPA_DEMO_POR_DEFECTO,
    *,
    semilla: int | None = None,
    escenario: str = "libre",
    cantidad_sobrevivientes: int = 1,
) -> ContextoDemo:
    """Prepara un juego sintético en PREPARACION para la entrada humana."""

    return crear_contexto_demo(
        ruta_mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=cantidad_sobrevivientes,
        modo=ModoPartida.JUEGO,
        preparar_inicial=False,
    )


def crear_servicio_demo(
    ruta_mapa: str | Path = MAPA_DEMO_POR_DEFECTO,
    *,
    semilla: int | None = None,
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


def _nodos_inicio_elegibles(grafo: Grafo, refugios: set[str]) -> tuple[str, ...]:
    """Devuelve nodos no-refugio desde los que existe ruta dirigida a refugio."""

    predecesores: dict[str, list[str]] = {nodo.id: [] for nodo in grafo.mapa.nodos}
    for calle in grafo.mapa.calles:
        predecesores[calle.destino].append(calle.origen)

    alcanzables = set(refugios)
    frontera = list(refugios)
    while frontera:
        destino = frontera.pop()
        for origen in predecesores[destino]:
            if origen not in alcanzables:
                alcanzables.add(origen)
                frontera.append(origen)

    return tuple(
        nodo.id
        for nodo in grafo.mapa.nodos
        if nodo.id not in refugios and nodo.id in alcanzables
    )


def _crear_zombies_demo(
    escenario: str,
    nodos_elegibles: tuple[str, ...],
    posiciones_sobrevivientes: tuple[str, ...],
    rng: random.Random,
) -> tuple[Zombie, ...]:
    """Muestrea ubicaciones y fases donde el prototipo ya tiene variación permitida.

    Las hordas conservan su regla provisional de inmovilidad y los perfiles no
    alteran cantidad ni composición, pendientes de P-07 y P-09.
    """

    composicion = _COMPOSICION_ZOMBIES_DEMO.get(escenario)
    if composicion is None:
        raise ValueError(f"Escenario demo desconocido: {escenario}.")
    disponibles = tuple(
        nodo for nodo in nodos_elegibles if nodo not in set(posiciones_sobrevivientes)
    ) or nodos_elegibles
    if composicion and not disponibles:
        raise ValueError("El mapa demo requiere nodos elegibles para ubicar zombies.")

    if len(composicion) <= len(disponibles):
        posiciones = rng.sample(disponibles, len(composicion))
    else:
        posiciones = [rng.choice(disponibles) for _ in composicion]

    return tuple(
        Zombie(
            identificador,
            tipo,
            nodo,
            estado=estado,
            fase_movimiento=rng.randrange(2) if tipo is TipoZombie.CAMINANTE else 0,
        )
        for (identificador, tipo, estado), nodo in zip(composicion, posiciones, strict=True)
    )
