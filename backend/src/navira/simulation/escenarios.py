"""Generación de escenarios sintéticos: dormidos y eventos de ciudad.

Recibe el RNG como argumento y no guarda semilla ni estado propio. No lo deben
importar `api/`, `routing/` ni la proyección observable: los dormidos son
información privada del mundo.
"""

from __future__ import annotations

import random
from typing import Literal

from navira.domain.mapa import Grafo, TipoCalle
from navira.domain.modelo import EstadoZombie, TipoZombie, Zombie
from navira.domain.snapshot import EventoCierre


IntensidadEscenario = Literal["baja", "media", "alta"]
# Fracción de nodos elegibles con amenaza. Calibrada para el fixture de caja
# completa (8366 nodos): 18, 42 y 75 amenazas, las mismas cifras que con 1500
# nodos, para no multiplicar los zombies al crecer la red.
FRACCION_NODOS_POR_INTENSIDAD: dict[str, float] = {"baja": 0.0022, "media": 0.0050, "alta": 0.0090}
ESCENARIOS: dict[str, tuple[tuple[TipoZombie, float], ...]] = {
    "libre": (),
    "caminantes": ((TipoZombie.CAMINANTE, 1.0),),
    "mixto": (
        (TipoZombie.CAMINANTE, 0.55),
        (TipoZombie.CORREDOR, 0.25),
        (TipoZombie.HORDA, 0.10),
        (TipoZombie.DORMIDO, 0.10),
    ),
    # Porcentajes de amenaza provisionales: el enunciado fija los tipos, no su
    # proporción. La composición de cada run se reproduce con su semilla.
    "reto_medianoche": (
        (TipoZombie.CAMINANTE, 0.60),
        (TipoZombie.CORREDOR, 0.25),
        (TipoZombie.HORDA, 0.15),
    ),
    "horda": (
        (TipoZombie.CAMINANTE, 0.10),
        (TipoZombie.CORREDOR, 0.10),
        (TipoZombie.HORDA, 0.55),
        (TipoZombie.DORMIDO, 0.25),
    ),
}


def crear_zombies(
    escenario: str,
    nodos_elegibles: tuple[str, ...],
    posiciones_sobrevivientes: tuple[str, ...],
    coordenadas: dict[str, tuple[float, float]],
    intensidad: IntensidadEscenario,
    rng: random.Random,
    *,
    cantidad_total: int | None = None,
    nodos_foco: tuple[str, ...] | None = None,
    proporcion_foco: float = 0.8,
) -> tuple[Zombie, ...]:
    """Escala y dispersa amenazas en la red disponible con RNG privado.

    Los porcentajes son perfiles sintéticos locales, no una estimación de
    población real. La estratificación cubre sectores ocupados del mapa antes
    de volver a elegir un sector para los nodos restantes.
    """

    perfil = ESCENARIOS.get(escenario)
    if perfil is None:
        raise ValueError(f"Escenario demo desconocido: {escenario}.")
    disponibles = tuple(
        nodo for nodo in nodos_elegibles if nodo not in set(posiciones_sobrevivientes)
    ) or nodos_elegibles
    if not perfil:
        return ()
    if not disponibles:
        raise ValueError("El mapa demo requiere nodos elegibles para ubicar zombies.")

    if not 0 < proporcion_foco <= 1:
        raise ValueError("La proporción del foco debe estar entre 0 y 1.")
    # La demo libre permite pedir un conteo exacto; los presets y herramientas
    # existentes mantienen su escala porcentual cuando no se proporciona.
    if cantidad_total is not None and (
        isinstance(cantidad_total, bool) or not isinstance(cantidad_total, int) or cantidad_total < 1
    ):
        raise ValueError("La cantidad de zombies debe ser un entero positivo.")
    total = min(
        len(disponibles),
        cantidad_total if cantidad_total is not None else max(
            1, round(len(disponibles) * FRACCION_NODOS_POR_INTENSIDAD[intensidad])
        ),
    )
    cantidad_por_tipo = _repartir_composicion(perfil, total)
    nodos_restantes = list(disponibles)
    nodos_globales = (
        _seleccionar_nodos_estratificados(disponibles, total, coordenadas, rng)
        if not nodos_foco
        else ()
    )
    posicion_global = 0
    zombies: list[Zombie] = []
    prefijos = {
        TipoZombie.CAMINANTE: "CAM",
        TipoZombie.CORREDOR: "COR",
        TipoZombie.HORDA: "HOR",
        TipoZombie.DORMIDO: "DOR",
    }
    for tipo, cantidad in cantidad_por_tipo:
        if nodos_foco:
            nodos_tipo = _seleccionar_nodos_focalizados(
                tuple(nodos_restantes), cantidad, nodos_foco, proporcion_foco, rng
            )
        else:
            # Conserva exactamente el muestreo global del Simulador libre.
            nodos_tipo = nodos_globales[posicion_global : posicion_global + cantidad]
            posicion_global += cantidad
        nodos_restantes = [nodo for nodo in nodos_restantes if nodo not in set(nodos_tipo)]
        for indice in range(1, cantidad + 1):
            zombies.append(
                Zombie(
                    f"Z-{prefijos[tipo]}-{indice:03d}",
                    tipo,
                    nodos_tipo[indice - 1],
                    estado=(EstadoZombie.DORMIDO if tipo is TipoZombie.DORMIDO else EstadoZombie.ACTIVO),
                    fase_movimiento=rng.randrange(2) if tipo is TipoZombie.CAMINANTE else 0,
                )
            )
    return tuple(zombies)


def _seleccionar_nodos_focalizados(
    disponibles: tuple[str, ...],
    cantidad: int,
    nodos_foco: tuple[str, ...],
    proporcion_foco: float,
    rng: random.Random,
) -> tuple[str, ...]:
    """Muestrea una cuota de cada tipo de amenaza dentro del foco urbano.

    El remanente mantiene amenazas por el resto del mapa. Si un área no tiene
    candidatos suficientes, la cuota se completa con nodos de la otra área.
    """

    foco = set(nodos_foco)
    centrales = [nodo for nodo in disponibles if nodo in foco]
    exteriores = [nodo for nodo in disponibles if nodo not in foco]
    cantidad_central = min(len(centrales), round(cantidad * proporcion_foco))
    cantidad_exterior = min(len(exteriores), cantidad - cantidad_central)
    cantidad_central = min(len(centrales), cantidad - cantidad_exterior)
    elegidos = rng.sample(centrales, cantidad_central) + rng.sample(exteriores, cantidad_exterior)
    rng.shuffle(elegidos)
    return tuple(elegidos)


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


def crear_eventos_ciudad(
    grafo: Grafo,
    intensidad: IntensidadEscenario,
    rng: random.Random,
) -> tuple[EventoCierre, ...]:
    """Sorts 1–10 closures once, then spaces them three turns apart.

    Intensity stays in the signature for callers that share scenario settings,
    but incident count is independent of zombie intensity. Segment selection,
    count, and therefore the schedule are reproducible from the private RNG.
    This is a generic road closure, not a model of a real crash or natural hazard.
    """

    segmentos = sorted({calle.segmento_id for calle in grafo.mapa.calles})
    if not segmentos:
        return ()
    cantidad = rng.randint(1, min(10, len(segmentos)))
    seleccionados = rng.sample(segmentos, cantidad)
    return tuple(
        EventoCierre(
            id=f"EV-CIUDAD-{indice:03d}",
            turno_objetivo=2 + 3 * (indice - 1),
            segmentos=frozenset((segmento,)),
            causa="Incidente vial simulado",
        )
        for indice, segmento in enumerate(seleccionados, start=1)
    )


def crear_eventos_reto(
    grafo: Grafo,
    ronda: int,
    rng: random.Random,
    *,
    segmentos_foco: tuple[str, ...] | None = None,
) -> tuple[EventoCierre, ...]:
    """Genera el evento exigido por ronda; selección reproducible y turnos provisionales.

    El reto no especifica ubicación ni turno. Se usa turno 50 (100 s) para el
    evento de ronda 2 y turnos 50/100 para ronda 3. En Manta se exige que el
    puente exista en el grafo; no se sustituye silenciosamente por otra calle.
    """

    if ronda == 1:
        return ()
    segmentos_por_id = {calle.segmento_id: calle for calle in grafo.mapa.calles}
    if ronda == 2:
        puentes = sorted(
            segmento_id
            for segmento_id, calle in segmentos_por_id.items()
            if calle.tipo is TipoCalle.PUENTE
        )
        puentes_en_foco = [segmento for segmento in puentes if segmento in set(segmentos_foco or ())]
        if puentes_en_foco:
            puentes = puentes_en_foco
        if not puentes:
            raise ValueError("El mapa de la ronda 2 no contiene un segmento etiquetado como puente.")
        return (
            EventoCierre(
                id="EV-RETO-R2-PUENTE",
                turno_objetivo=50,
                segmentos=frozenset((rng.choice(puentes),)),
                causa="Colapso de puente del reto",
            ),
        )
    if ronda == 3:
        segmentos = sorted(segmentos_por_id)
        segmentos_en_foco = [segmento for segmento in segmentos if segmento in set(segmentos_foco or ())]
        if len(segmentos_en_foco) >= 2:
            segmentos = segmentos_en_foco
        if len(segmentos) < 2:
            raise ValueError("El mapa de la ronda 3 requiere dos segmentos distintos para bloquear.")
        elegidos = rng.sample(segmentos, 2)
        return tuple(
            EventoCierre(
                id=f"EV-RETO-R3-CALLE-{indice}",
                turno_objetivo=50 * indice,
                segmentos=frozenset((segmento_id,)),
                causa="Calle bloqueada del reto",
            )
            for indice, segmento_id in enumerate(elegidos, start=1)
        )
    raise ValueError("La ronda del reto debe ser 1, 2 o 3.")
