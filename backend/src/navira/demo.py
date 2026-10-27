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
from typing import Literal

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
    EventoCierre,
    crear_snapshot_inicial,
    preparar_turno_versionado,
)


MAPA_DEMO_POR_DEFECTO = Path(__file__).resolve().parents[2] / "data/maps/demo-sintetico.json"
MAPA_MANTA_POR_DEFECTO = Path(__file__).resolve().parents[2] / "data/maps/manta-hackathon-v1.json"
IntensidadDemo = Literal["baja", "media", "alta"]
_FRACCION_NODOS_POR_INTENSIDAD: dict[str, float] = {"baja": 0.06, "media": 0.14, "alta": 0.25}
_COMPOSICION_POR_ESCENARIO: dict[str, tuple[tuple[TipoZombie, float], ...]] = {
    "libre": (),
    "caminantes": ((TipoZombie.CAMINANTE, 1.0),),
    "mixto": (
        (TipoZombie.CAMINANTE, 0.55),
        (TipoZombie.CORREDOR, 0.25),
        (TipoZombie.HORDA, 0.10),
        (TipoZombie.DORMIDO, 0.10),
    ),
    "horda": (
        (TipoZombie.CAMINANTE, 0.10),
        (TipoZombie.CORREDOR, 0.10),
        (TipoZombie.HORDA, 0.55),
        (TipoZombie.DORMIDO, 0.25),
    ),
}
ESCENARIOS_DEMO = _COMPOSICION_POR_ESCENARIO


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
    intensidad: IntensidadDemo = "media",
    eventos_ciudad: bool = False,
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
    if intensidad not in _FRACCION_NODOS_POR_INTENSIDAD:
        raise ValueError("La intensidad demo debe ser baja, media o alta.")
    if not isinstance(eventos_ciudad, bool):
        raise ValueError("La opción de incidentes de ciudad debe ser booleana.")
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
    coordenadas = {nodo.id: (nodo.lat, nodo.lng) for nodo in grafo.mapa.nodos}
    zombies = _crear_zombies_demo(
        escenario,
        nodos_inicio,
        posiciones,
        coordenadas,
        intensidad,
        rng,
    )
    eventos = _crear_eventos_ciudad(grafo, intensidad, rng) if eventos_ciudad else ()
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


def _crear_zombies_demo(
    escenario: str,
    nodos_elegibles: tuple[str, ...],
    posiciones_sobrevivientes: tuple[str, ...],
    coordenadas: dict[str, tuple[float, float]],
    intensidad: IntensidadDemo,
    rng: random.Random,
) -> tuple[Zombie, ...]:
    """Escala y dispersa amenazas en la red disponible con RNG privado.

    Los porcentajes son perfiles sintéticos locales, no una estimación de
    población real. La estratificación cubre sectores ocupados del mapa antes
    de volver a elegir un sector para los nodos restantes.
    """

    perfil = _COMPOSICION_POR_ESCENARIO.get(escenario)
    if perfil is None:
        raise ValueError(f"Escenario demo desconocido: {escenario}.")
    disponibles = tuple(
        nodo for nodo in nodos_elegibles if nodo not in set(posiciones_sobrevivientes)
    ) or nodos_elegibles
    if not perfil:
        return ()
    if not disponibles:
        raise ValueError("El mapa demo requiere nodos elegibles para ubicar zombies.")

    total = min(
        len(disponibles),
        max(1, round(len(disponibles) * _FRACCION_NODOS_POR_INTENSIDAD[intensidad])),
    )
    cantidad_por_tipo = _repartir_composicion(perfil, total)
    nodos = _seleccionar_nodos_estratificados(disponibles, total, coordenadas, rng)
    zombies: list[Zombie] = []
    posicion = 0
    prefijos = {
        TipoZombie.CAMINANTE: "CAM",
        TipoZombie.CORREDOR: "COR",
        TipoZombie.HORDA: "HOR",
        TipoZombie.DORMIDO: "DOR",
    }
    for tipo, cantidad in cantidad_por_tipo:
        for indice in range(1, cantidad + 1):
            zombies.append(
                Zombie(
                    f"Z-{prefijos[tipo]}-{indice:03d}",
                    tipo,
                    nodos[posicion],
                    estado=(EstadoZombie.DORMIDO if tipo is TipoZombie.DORMIDO else EstadoZombie.ACTIVO),
                    fase_movimiento=rng.randrange(2) if tipo is TipoZombie.CAMINANTE else 0,
                )
            )
            posicion += 1
    return tuple(zombies)


def _repartir_composicion(
    perfil: tuple[tuple[TipoZombie, float], ...], total: int
) -> tuple[tuple[TipoZombie, int], ...]:
    """Distribuye un total entero por porcentajes con restos mayores primero."""

    cantidades = [int(total * fraccion) for _, fraccion in perfil]
    faltantes = total - sum(cantidades)
    orden_restos = sorted(
        range(len(perfil)),
        key=lambda indice: (-(total * perfil[indice][1] - cantidades[indice]), indice),
    )
    for indice in orden_restos[:faltantes]:
        cantidades[indice] += 1
    return tuple(
        (tipo, cantidad)
        for (tipo, _), cantidad in zip(perfil, cantidades, strict=True)
        if cantidad > 0
    )


def _seleccionar_nodos_estratificados(
    disponibles: tuple[str, ...],
    cantidad: int,
    coordenadas: dict[str, tuple[float, float]],
    rng: random.Random,
) -> tuple[str, ...]:
    """Muestrea en celdas lat/lng para repartir focos por el grafo disponible."""

    filas = columnas = 4
    latitudes = [coordenadas[nodo][0] for nodo in disponibles]
    longitudes = [coordenadas[nodo][1] for nodo in disponibles]
    lat_min, lat_max = min(latitudes), max(latitudes)
    lng_min, lng_max = min(longitudes), max(longitudes)

    def celda(valor: float, minimo: float, maximo: float, divisiones: int) -> int:
        if maximo == minimo:
            return 0
        return min(divisiones - 1, int((valor - minimo) / (maximo - minimo) * divisiones))

    sectores: dict[tuple[int, int], list[str]] = {}
    for nodo in disponibles:
        lat, lng = coordenadas[nodo]
        clave = (celda(lat, lat_min, lat_max, filas), celda(lng, lng_min, lng_max, columnas))
        sectores.setdefault(clave, []).append(nodo)
    sectores_disponibles = list(sectores.values())
    rng.shuffle(sectores_disponibles)
    for nodos_sector in sectores_disponibles:
        rng.shuffle(nodos_sector)

    seleccionados: list[str] = []
    ronda = 0
    while len(seleccionados) < cantidad:
        hubo_candidato = False
        for nodos_sector in sectores_disponibles:
            if ronda < len(nodos_sector):
                seleccionados.append(nodos_sector[ronda])
                hubo_candidato = True
                if len(seleccionados) == cantidad:
                    break
        if not hubo_candidato:
            break
        ronda += 1
    return tuple(seleccionados)


def _crear_eventos_ciudad(
    grafo: Grafo,
    intensidad: IntensidadDemo,
    rng: random.Random,
) -> tuple[EventoCierre, ...]:
    """Programa cierres viales genéricos; no representa amenazas naturales."""

    cantidad = {"baja": 1, "media": 2, "alta": 3}[intensidad]
    segmentos = sorted({calle.segmento_id for calle in grafo.mapa.calles})
    if not segmentos:
        return ()
    seleccionados = rng.sample(segmentos, min(cantidad, len(segmentos)))
    turnos = (2, 5, 8)
    return tuple(
        EventoCierre(
            id=f"EV-CIUDAD-{indice:03d}",
            turno_objetivo=turnos[indice - 1],
            segmentos=frozenset((segmento,)),
            causa="Incidente vial simulado",
        )
        for indice, segmento in enumerate(seleccionados, start=1)
    )
