"""Rutas de costo mínimo con cierres y peligros visibles del snapshot."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from navira.domain.mapa import Calle, Grafo, TipoCalle


@dataclass(frozen=True, slots=True)
class PerfilCostos:
    """Multiplicadores configurables por tipo sobre metros de calle.

    El valor neutral 1.0 no asigna preferencia de juego sin evidencia. Factores
    mayores modelan un costo relativo y nunca deben mezclarse con segundos o
    probabilidades sin convertir unidades primero.
    """

    factores_tipo: Mapping[TipoCalle, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        factores = dict(self.factores_tipo)
        for tipo, factor in factores.items():
            if not isinstance(tipo, TipoCalle):
                raise ValueError(f"Tipo de calle no reconocido en perfil: {tipo}.")
            if (
                isinstance(factor, bool)
                or not isinstance(factor, (int, float))
                or not math.isfinite(factor)
                or factor <= 0
            ):
                raise ValueError("Los factores de costo deben ser positivos y finitos.")
        object.__setattr__(self, "factores_tipo", MappingProxyType(factores))

    def costo(self, calle: Calle) -> float:
        """Costo relativo en metros ponderados de un sentido dirigido."""

        return calle.distancia_m * self.factores_tipo.get(calle.tipo, 1.0)


@dataclass(frozen=True, slots=True)
class Ruta:
    """Resultado determinista; calles conservan su sentido y segmento físico."""

    origen: str
    destino: str
    calles: tuple[Calle, ...]
    costo_ponderado_m: float
    refugio_id: str | None = None

    @property
    def siguiente_nodo(self) -> str | None:
        """Primer destino de calle; `None` indica que ya está en destino."""

        return self.calles[0].destino if self.calles else None


def encontrar_ruta(
    grafo: Grafo,
    origen: str,
    destino: str,
    *,
    aristas_cerradas: frozenset[str] = frozenset(),
    segmentos_cerrados: frozenset[str] = frozenset(),
    nodos_bloqueados: frozenset[str] = frozenset(),
    perfil: PerfilCostos = PerfilCostos(),
) -> Ruta | None:
    """Encuentra la ruta dirigida mínima; devuelve `None` si no existe.

    Los bloqueos se aplican al entrar a un nodo, incluido el destino. Si el
    sobreviviente ya parte de un nodo peligroso, puede buscar una salida.
    `nodos_bloqueados` debe provenir solo de peligros que el motor puede ver.
    """

    nodos = grafo.mapa.nodos_por_id
    if origen not in nodos:
        raise KeyError(f"Nodo de origen desconocido: {origen}.")
    if destino not in nodos:
        raise KeyError(f"Nodo de destino desconocido: {destino}.")
    if origen == destino:
        return Ruta(origen, destino, (), 0.0)
    if destino in nodos_bloqueados:
        return None

    return _rutas_desde(
        grafo,
        origen,
        frozenset((destino,)),
        aristas_cerradas=aristas_cerradas,
        segmentos_cerrados=segmentos_cerrados,
        nodos_bloqueados=nodos_bloqueados,
        perfil=perfil,
    ).get(destino)


def _rutas_desde(
    grafo: Grafo,
    origen: str,
    destinos: frozenset[str],
    *,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
    nodos_bloqueados: frozenset[str],
    perfil: PerfilCostos,
) -> dict[str, Ruta]:
    """Un solo Dijkstra desde `origen` que para cuando todos los `destinos` quedan fijados.

    Expande los mismos nodos en el mismo orden que una búsqueda por destino, así
    que cada ruta coincide con la de `encontrar_ruta`; solo evita repetir la
    expansión por cada refugio. Los destinos deben ser distintos de `origen`.
    """

    mejor: dict[str, tuple[float, tuple[str, ...]]] = {origen: (0.0, ())}
    anterior: dict[str, tuple[str, Calle]] = {}
    pendientes: list[tuple[float, tuple[str, ...], str]] = [(0.0, (), origen)]
    por_fijar = set(destinos)

    while pendientes and por_fijar:
        costo, secuencia, nodo = heapq.heappop(pendientes)
        if mejor.get(nodo) != (costo, secuencia):
            continue
        por_fijar.discard(nodo)
        for calle in grafo.salientes(nodo):
            # Mismo filtro que `calles_desde`, sin construir una tupla por nodo expandido.
            if calle.id in aristas_cerradas or calle.segmento_id in segmentos_cerrados:
                continue
            if calle.destino in nodos_bloqueados:
                continue
            nuevo_costo = costo + perfil.costo(calle)
            nueva_secuencia = secuencia + (calle.id,)
            anterior_candidato = mejor.get(calle.destino)
            candidato = (nuevo_costo, nueva_secuencia)
            if anterior_candidato is not None and anterior_candidato <= candidato:
                continue
            mejor[calle.destino] = candidato
            anterior[calle.destino] = (nodo, calle)
            heapq.heappush(pendientes, (nuevo_costo, nueva_secuencia, calle.destino))

    rutas: dict[str, Ruta] = {}
    for destino in destinos:
        if destino not in mejor or destino in por_fijar:
            continue
        calles: list[Calle] = []
        nodo_actual = destino
        while nodo_actual != origen:
            previo, calle = anterior[nodo_actual]
            calles.append(calle)
            nodo_actual = previo
        calles.reverse()
        rutas[destino] = Ruta(origen, destino, tuple(calles), mejor[destino][0])
    return rutas


def seleccionar_refugio(
    grafo: Grafo,
    origen: str,
    *,
    refugio_objetivo: str | None = None,
    aristas_cerradas: frozenset[str] = frozenset(),
    segmentos_cerrados: frozenset[str] = frozenset(),
    nodos_bloqueados: frozenset[str] = frozenset(),
    perfil: PerfilCostos = PerfilCostos(),
) -> Ruta | None:
    """Elige ruta viable más barata; desempata por ID estable del refugio."""

    if origen not in grafo.mapa.nodos_por_id:
        raise KeyError(f"Nodo de origen desconocido: {origen}.")
    refugios = grafo.mapa.refugios
    if refugio_objetivo is not None:
        refugios = tuple(refugio for refugio in refugios if refugio.id == refugio_objetivo)
        if not refugios:
            raise KeyError(f"Refugio desconocido: {refugio_objetivo}.")

    for refugio in refugios:
        if refugio.nodo not in grafo.mapa.nodos_por_id:
            raise KeyError(f"Nodo de destino desconocido: {refugio.nodo}.")
    destinos = frozenset(
        refugio.nodo for refugio in refugios
        if refugio.nodo != origen and refugio.nodo not in nodos_bloqueados
    )
    rutas = _rutas_desde(
        grafo,
        origen,
        destinos,
        aristas_cerradas=aristas_cerradas,
        segmentos_cerrados=segmentos_cerrados,
        nodos_bloqueados=nodos_bloqueados,
        perfil=perfil,
    )
    opciones: list[Ruta] = []
    for refugio in refugios:
        ruta = Ruta(origen, origen, (), 0.0) if refugio.nodo == origen else rutas.get(refugio.nodo)
        if ruta is not None:
            opciones.append(
                Ruta(ruta.origen, ruta.destino, ruta.calles, ruta.costo_ponderado_m, refugio.id)
            )
    return min(
        opciones,
        key=lambda ruta: (ruta.costo_ponderado_m, ruta.refugio_id, tuple(calle.id for calle in ruta.calles)),
        default=None,
    )
