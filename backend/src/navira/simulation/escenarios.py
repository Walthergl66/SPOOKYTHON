"""Generación de escenarios sintéticos: dormidos y eventos de ciudad.

Recibe el RNG como argumento y no guarda semilla ni estado propio. No lo deben
importar `api/`, `routing/` ni la proyección observable: los dormidos son
información privada del mundo.
"""

from __future__ import annotations

import random
from typing import Literal

from navira.domain.mapa import Grafo
from navira.domain.modelo import EstadoZombie, TipoZombie, Zombie
from navira.domain.snapshot import EventoCierre


IntensidadEscenario = Literal["baja", "media", "alta"]
# Fracción de nodos elegibles con amenaza. El fixture de Manta pasó de 300 a
# 1500 nodos: estas cifras son 1/5 de 6/14/25 % para mantener el mismo número
# de amenazas por intensidad (42 en media) y no multiplicar los zombies.
FRACCION_NODOS_POR_INTENSIDAD: dict[str, float] = {"baja": 0.012, "media": 0.028, "alta": 0.05}
ESCENARIOS: dict[str, tuple[tuple[TipoZombie, float], ...]] = {
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


def crear_zombies(
    escenario: str,
    nodos_elegibles: tuple[str, ...],
    posiciones_sobrevivientes: tuple[str, ...],
    coordenadas: dict[str, tuple[float, float]],
    intensidad: IntensidadEscenario,
    rng: random.Random,
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

    total = min(
        len(disponibles),
        max(1, round(len(disponibles) * FRACCION_NODOS_POR_INTENSIDAD[intensidad])),
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


def crear_eventos_ciudad(
    grafo: Grafo,
    intensidad: IntensidadEscenario,
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
