"""Ensamblaje explícito de un mundo local descartable para desarrollo.

El mapa cargado aquí es sintético y nunca debe usarse como representación de
Manta ni como escenario oficial de evaluación.
"""

from __future__ import annotations

import math
import random
import secrets
import uuid
from dataclasses import dataclass, replace
from pathlib import Path

from navira.adapters.mapas_memoria import CatalogoMapasMemoria
from navira.adapters.snapshots_memoria import AlmacenSnapshotsMemoria
from navira.application.decidir_paso import DecidirPaso, ProveedorMapas
from navira.application.snapshots import RepositorioSnapshots
from navira.domain.mapa import (
    Grafo,
    Refugio,
    MANTA_PLAYABLE_BOUNDS,
    cargar_mapa,
    mapa_con_refugios,
    nodos_protegidos_refugios,
    recortar_mapa,
)
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
from navira.simulation.escenarios import (
    ESCENARIOS,
    FRACCION_NODOS_POR_INTENSIDAD,
    IntensidadEscenario,
    crear_eventos_ciudad,
    crear_eventos_reto,
    crear_zombies,
)


MAPA_DEMO_POR_DEFECTO = Path(__file__).resolve().parents[2] / "data/maps/demo-sintetico.json"
MAPA_MANTA_POR_DEFECTO = Path(__file__).resolve().parents[2] / "data/maps/manta-hackathon-v1.json"

# El reto nombra estos cuatro sectores, pero no entrega polígonos ni cantidades
# por sector. Los puntos de referencia proceden de lugares OSM; el radio forma
# una zona local aproximada y sustituible si la organización publica límites.
SECTORES_SPAWN_RETO: tuple[tuple[str, float, float], ...] = (
    ("Tarqui", -0.9784464, -80.7243193),
    ("Los Esteros", -0.9585425, -80.6846573),
    ("Barbasquillo", -0.9515404, -80.7527254),
    ("Jocay", -0.9598756, -80.7161161),
)
RADIO_ZONA_SPAWN_RETO_M = 1_500.0
# Centro urbano aproximado en La Dolorosa; zona de concentración de amenazas
# para el Reto. No es un límite administrativo ni una fuente de riesgo oficial.
CENTRO_URBANO_RETO = (-0.9522745219919659, -80.72726572846808)
RADIO_FOCO_AMENAZAS_RETO_M = 3_500.0
PROPORCION_AMENAZAS_FOCO_RETO = 0.8

IntensidadDemo = IntensidadEscenario
ESCENARIOS_DEMO = ESCENARIOS


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
    cantidad_zombies: int | None = None,
    intensidad: IntensidadDemo = "media",
    eventos_ciudad: bool = False,
    modo: ModoPartida = ModoPartida.SIMULADOR,
    preparar_inicial: bool = True,
    refugios: tuple[Refugio, ...] | None = None,
    ronda_reto: int | None = None,
    mundo_vacio: bool = False,
) -> ContextoDemo:
    """Crea una partida con estado inicial aleatorio y expone dependencias.

    Sin semilla explícita, obtiene una semilla de la entropía del sistema.
    Los perfiles son fixtures; no representan distribuciones oficiales.
    """

    cantidad_sobrevivientes_valida = (
        isinstance(cantidad_sobrevivientes, int)
        and not isinstance(cantidad_sobrevivientes, bool)
        and ((cantidad_sobrevivientes == 0 and mundo_vacio) or 1 <= cantidad_sobrevivientes <= 200)
    )
    if not cantidad_sobrevivientes_valida:
        raise ValueError("La población debe ser un entero entre 1 y 200, salvo al crear un mundo operador vacío.")
    if mundo_vacio and (cantidad_zombies != 0 or ronda_reto is not None or eventos_ciudad):
        raise ValueError("El mundo operador vacío no admite zombies iniciales, eventos ni preset Reto.")
    if semilla is not None and (isinstance(semilla, bool) or not isinstance(semilla, int)):
        raise ValueError("La semilla debe ser un entero o None.")
    if not isinstance(modo, ModoPartida):
        raise ValueError("El modo demo no es válido.")
    mapa = cargar_mapa(ruta_mapa)
    # Only the real Manta OSM fixture uses the urban play area. Synthetic maps
    # remain unchanged so unit fixtures and local scenarios keep their topology.
    if mapa.version.startswith("manta-osm-"):
        mapa = recortar_mapa(mapa, MANTA_PLAYABLE_BOUNDS)
    if mundo_vacio:
        # El operador elige los refugios sobre un grafo que conserva sus calles.
        mapa = replace(mapa, version=f"{mapa.version}+operador-vacio", refugios=())
    elif refugios is not None:
        mapa = mapa_con_refugios(mapa, tuple(refugios))
    grafo = Grafo(mapa)
    if ronda_reto is not None:
        if ronda_reto not in (1, 2, 3):
            raise ValueError("La ronda del reto debe ser 1, 2 o 3.")
        escenario = {1: "caminantes", 2: "reto_medianoche", 3: "mixto"}[ronda_reto]
        cantidad_sobrevivientes = {1: 20, 2: 80, 3: 200}[ronda_reto]
        intensidad = "media"
        eventos_ciudad = False
    if escenario not in ESCENARIOS_DEMO:
        opciones = ", ".join(sorted(ESCENARIOS_DEMO))
        raise ValueError(f"Escenario demo desconocido: {escenario}. Opciones: {opciones}.")
    if intensidad not in FRACCION_NODOS_POR_INTENSIDAD:
        raise ValueError("La intensidad demo debe ser baja, media o alta.")
    minimo_zombies = 0 if mundo_vacio else 1
    if cantidad_zombies is not None and (
        isinstance(cantidad_zombies, bool)
        or not isinstance(cantidad_zombies, int)
        or not minimo_zombies <= cantidad_zombies <= 200
    ):
        raise ValueError("La cantidad de zombies debe ser un entero entre 1 y 200.")
    if not isinstance(eventos_ciudad, bool):
        raise ValueError("La opción de incidentes de ciudad debe ser booleana.")
    semilla_real = secrets.randbits(64) if semilla is None else semilla
    rng = random.Random(semilla_real)
    nodos_refugio = {refugio.nodo for refugio in grafo.mapa.refugios}
    nodos_inicio = _nodos_inicio_elegibles(grafo, nodos_refugio)
    if not nodos_inicio and not mundo_vacio:
        raise ValueError("El mapa demo requiere un nodo transitable con ruta a algún refugio.")
    if mundo_vacio:
        posiciones = ()
    elif ronda_reto is not None and grafo.mapa.version.startswith("manta-osm-"):
        posiciones = _posiciones_iniciales_reto(
            grafo,
            nodos_inicio,
            cantidad_sobrevivientes,
            rng,
        )
    elif cantidad_sobrevivientes <= len(nodos_inicio):
        posiciones = tuple(rng.sample(nodos_inicio, cantidad_sobrevivientes))
    else:
        posiciones = tuple(rng.choice(nodos_inicio) for _ in range(cantidad_sobrevivientes))
    coordenadas = {nodo.id: (nodo.lat, nodo.lng) for nodo in grafo.mapa.nodos}
    nodos_zombie_elegibles = nodos_inicio
    if grafo.mapa.version.startswith("manta-osm-"):
        nodos_protegidos = nodos_protegidos_refugios(grafo)
        nodos_zombie_elegibles = tuple(
            nodo for nodo in nodos_inicio if nodo not in nodos_protegidos
        )
    zombies = () if mundo_vacio else crear_zombies(
        escenario,
        nodos_zombie_elegibles,
        posiciones,
        coordenadas,
        intensidad,
        rng,
        cantidad_total=cantidad_zombies,
        nodos_foco=(
            _nodos_en_foco_urbano(grafo, nodos_zombie_elegibles)
            if ronda_reto is not None and grafo.mapa.version.startswith("manta-osm-")
            else None
        ),
        proporcion_foco=PROPORCION_AMENAZAS_FOCO_RETO,
    )
    eventos = () if mundo_vacio else (
        crear_eventos_reto(
            grafo,
            ronda_reto,
            rng,
            segmentos_foco=(
                _segmentos_en_foco_urbano(grafo)
                if grafo.mapa.version.startswith("manta-osm-")
                else None
            ),
        )
        if ronda_reto is not None
        else crear_eventos_ciudad(grafo, intensidad, rng) if eventos_ciudad else ()
    )
    run_id = f"navira-demo-{uuid.uuid4().hex}"
    partida = Partida(
        run_id=run_id,
        modo=modo,
        escenario=(f"reto-ronda-{ronda_reto}-{escenario}" if ronda_reto is not None else f"demo-sintetico-{escenario}"),
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
    inicial = crear_snapshot_inicial(partida, grafo, rng=rng, eventos=eventos)
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
    intensidad: IntensidadDemo = "media",
) -> ContextoDemo:
    """Prepara un juego sintético en PREPARACION para la entrada humana."""

    return crear_contexto_demo(
        ruta_mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=cantidad_sobrevivientes,
        intensidad=intensidad,
        modo=ModoPartida.JUEGO,
        preparar_inicial=False,
    )


def crear_servicio_demo(
    ruta_mapa: str | Path = MAPA_DEMO_POR_DEFECTO,
    *,
    semilla: int | None = None,
    escenario: str = "libre",
    cantidad_sobrevivientes: int = 1,
    intensidad: IntensidadDemo = "media",
) -> DecidirPaso:
    """Compatibilidad para API: crea el contexto y devuelve su planificador."""

    return crear_contexto_demo(
        ruta_mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=cantidad_sobrevivientes,
        intensidad=intensidad,
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


def _posiciones_iniciales_reto(
    grafo: Grafo,
    nodos_elegibles: tuple[str, ...],
    cantidad: int,
    rng: random.Random,
) -> tuple[str, ...]:
    """Reparte el inicio de Reto entre sus cuatro zonas geográficas.

    La ronda reparte la población de forma equilibrada (diferencia máxima de
    una persona) y el RNG de la partida elige nodos distintos dentro de radios
    locales. Solo entran nodos viales alcanzables desde un refugio y fuera de
    los refugios; Simulador libre conserva su muestreo de ciudad completa.
    """

    coordenadas = {nodo.id: (nodo.lat, nodo.lng) for nodo in grafo.mapa.nodos}
    candidatos_por_sector: list[list[str]] = [[] for _ in SECTORES_SPAWN_RETO]
    for nodo_id in nodos_elegibles:
        coordenada = coordenadas[nodo_id]
        distancias = tuple(
            _distancia_metros(coordenada, (lat, lng))
            for _, lat, lng in SECTORES_SPAWN_RETO
        )
        sector = min(range(len(distancias)), key=distancias.__getitem__)
        if distancias[sector] <= RADIO_ZONA_SPAWN_RETO_M:
            candidatos_por_sector[sector].append(nodo_id)

    if any(not candidatos for candidatos in candidatos_por_sector):
        faltantes = [
            SECTORES_SPAWN_RETO[indice][0]
            for indice, candidatos in enumerate(candidatos_por_sector)
            if not candidatos
        ]
        raise ValueError(
            "El mapa no contiene nodos elegibles en todos los sectores de Reto: "
            + ", ".join(faltantes)
        )

    base, sobrantes = divmod(cantidad, len(SECTORES_SPAWN_RETO))
    orden_resto = list(range(len(SECTORES_SPAWN_RETO)))
    rng.shuffle(orden_resto)
    cuotas = [base] * len(SECTORES_SPAWN_RETO)
    for indice in orden_resto[:sobrantes]:
        cuotas[indice] += 1

    posiciones: list[str] = []
    for indice, cuota in enumerate(cuotas):
        candidatos = candidatos_por_sector[indice]
        if cuota > len(candidatos):
            raise ValueError(
                f"El sector {SECTORES_SPAWN_RETO[indice][0]} no tiene nodos "
                f"suficientes para ubicar {cuota} sobrevivientes de Reto."
            )
        posiciones.extend(rng.sample(candidatos, cuota))
    return tuple(posiciones)


def _nodos_en_foco_urbano(grafo: Grafo, nodos: tuple[str, ...]) -> tuple[str, ...]:
    """Elige intersecciones jugables dentro del radio central provisional."""

    return tuple(
        nodo
        for nodo in nodos
        if _distancia_metros(
            (grafo.mapa.nodos_por_id[nodo].lat, grafo.mapa.nodos_por_id[nodo].lng),
            CENTRO_URBANO_RETO,
        ) <= RADIO_FOCO_AMENAZAS_RETO_M
    )


def _segmentos_en_foco_urbano(grafo: Grafo) -> tuple[str, ...]:
    """Devuelve calles cuyo punto medio cae en el radio central del Reto."""

    puntos: dict[str, list[tuple[float, float]]] = {}
    for calle in grafo.mapa.calles:
        origen = grafo.mapa.nodos_por_id[calle.origen]
        destino = grafo.mapa.nodos_por_id[calle.destino]
        puntos.setdefault(calle.segmento_id, []).append(
            ((origen.lat + destino.lat) / 2, (origen.lng + destino.lng) / 2)
        )
    return tuple(
        segmento
        for segmento, coordenadas in puntos.items()
        if _distancia_metros(
            (
                sum(lat for lat, _ in coordenadas) / len(coordenadas),
                sum(lng for _, lng in coordenadas) / len(coordenadas),
            ),
            CENTRO_URBANO_RETO,
        ) <= RADIO_FOCO_AMENAZAS_RETO_M
    )


def _distancia_metros(
    origen: tuple[float, float], destino: tuple[float, float]
) -> float:
    """Distancia Haversine entre coordenadas WGS84, expresada en metros."""

    lat1, lon1 = map(math.radians, origen)
    lat2, lon2 = map(math.radians, destino)
    delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 6_371_000 * 2 * math.asin(math.sqrt(a))
