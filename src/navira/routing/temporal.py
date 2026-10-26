"""Búsqueda de rutas acotada por turnos sobre peligros observables."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from time import perf_counter
from types import MappingProxyType
from typing import Mapping

from navira.domain.mapa import Grafo, Refugio
from navira.routing.dijkstra import PerfilCostos


@dataclass(frozen=True, slots=True)
class CondicionTurno:
    """Bloqueos conocidos y exposición estimada para una fase de decisión.

    La exposición por nodo está en [0, 1] para una fase. Su suma en la ruta es
    una puntuación acumulada, no una probabilidad calibrada de supervivencia.
    Las condiciones futuras deben derivarse solo de información observable.
    """

    nodos_bloqueados: frozenset[str] = frozenset()
    aristas_cerradas: frozenset[str] = frozenset()
    segmentos_cerrados: frozenset[str] = frozenset()
    exposicion_nodo: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodos_bloqueados", frozenset(self.nodos_bloqueados))
        object.__setattr__(self, "aristas_cerradas", frozenset(self.aristas_cerradas))
        object.__setattr__(self, "segmentos_cerrados", frozenset(self.segmentos_cerrados))
        exposicion = dict(self.exposicion_nodo)
        if any(
            not isinstance(nodo, str)
            or not nodo
            or isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not math.isfinite(valor)
            or not 0 <= valor <= 1
            for nodo, valor in exposicion.items()
        ):
            raise ValueError("La exposición temporal requiere nodos y valores finitos entre 0 y 1.")
        object.__setattr__(self, "exposicion_nodo", MappingProxyType(exposicion))


@dataclass(frozen=True, slots=True)
class ResultadoRutaTemporal:
    """Resultado completo o motivo de salida sin aplicar una ruta parcial."""

    estado: str
    trayecto: tuple[str, ...] | None
    turnos: int | None
    exposicion_acumulada: float | None
    costo_ponderado_m: float | None
    expansiones: int
    duracion_ms: float


def buscar_ruta_temporal(
    grafo: Grafo,
    origen: str,
    refugios: frozenset[str],
    *,
    peligros_actuales: CondicionTurno = CondicionTurno(),
    pronostico: tuple[CondicionTurno, ...] = (),
    horizonte_turnos: int = 6,
    limite_expansiones: int = 20_000,
    presupuesto_ms: float = 25.0,
    perfil: PerfilCostos = PerfilCostos(),
) -> ResultadoRutaTemporal:
    """Busca una ruta por `(nodo, turnos_restantes)` con opción de esperar.

    El primer paso respeta el estado observable del snapshot. Cada pronóstico
    después cubre una fase de decisión futura. La búsqueda usa prioridades
    lexicográficas: exposición acumulada, turnos, metros ponderados y secuencia
    estable de acciones. No consulta RNG, red, zombies dormidos ni detalles
    privados. Si se agota un límite, descarta el resultado parcial para que el
    llamador conserve una ruta base independiente.
    """

    inicio = perf_counter()
    _validar_limites(horizonte_turnos, limite_expansiones, presupuesto_ms)
    nodos = grafo.mapa.nodos_por_id
    if origen not in nodos:
        raise KeyError(f"Nodo de origen desconocido: {origen}.")
    if not refugios:
        raise ValueError("La búsqueda temporal requiere al menos un refugio.")
    refugios_por_id = {refugio.id: refugio for refugio in grafo.mapa.refugios}
    if refugios - set(refugios_por_id):
        raise KeyError("La búsqueda temporal referencia un refugio desconocido.")
    _validar_condicion(peligros_actuales, grafo)
    for condicion in pronostico:
        _validar_condicion(condicion, grafo)

    if any(refugios_por_id[refugio].nodo == origen for refugio in refugios):
        return _resultado("en_refugio", (origen,), 0, 0.0, 0.0, 0, inicio)

    # Heap tuple also provides deterministic tie-breaking without node-ID bias.
    inicial = (0.0, 0, 0.0, (), (origen,), origen)
    frontera: list[tuple[float, int, float, tuple[str, ...], tuple[str, ...], str]] = [inicial]
    mejor: dict[tuple[str, int], tuple[float, int, float, tuple[str, ...], tuple[str, ...]]] = {
        (origen, 0): inicial[:-1]
    }
    expansiones = 0

    while frontera:
        if expansiones >= limite_expansiones or (perf_counter() - inicio) * 1000 >= presupuesto_ms:
            return _resultado("presupuesto_agotado", None, None, None, None, expansiones, inicio)

        exposicion, turnos, costo, acciones, trayecto, nodo = heapq.heappop(frontera)
        clave = (nodo, turnos)
        if mejor.get(clave) != (exposicion, turnos, costo, acciones, trayecto):
            continue
        refugio = _refugio_en_nodo(refugios_por_id, refugios, nodo)
        if refugio is not None:
            return _resultado("ruta_encontrada", trayecto, turnos, exposicion, costo, expansiones, inicio)
        if turnos >= horizonte_turnos:
            continue

        condicion = (
            peligros_actuales
            if turnos == 0
            else _pronostico_en(peligros_actuales, pronostico, turnos - 1)
        )
        expansiones += 1
        sucesores: list[tuple[str, str | None, float]] = []
        if nodo not in condicion.nodos_bloqueados:
            sucesores.append((nodo, None, 0.0))
        for calle in grafo.calles_desde(
            nodo,
            aristas_cerradas=condicion.aristas_cerradas,
            segmentos_cerrados=condicion.segmentos_cerrados,
        ):
            if calle.destino in condicion.nodos_bloqueados:
                continue
            sucesores.append((calle.destino, calle.id, perfil.costo(calle)))

        for destino, id_calle, costo_tramo in sucesores:
            nuevo_turno = turnos + 1
            nueva_exposicion = round(exposicion + condicion.exposicion_nodo.get(destino, 0.0), 12)
            nuevo_costo = costo + costo_tramo
            nueva_accion = acciones + ((id_calle if id_calle is not None else "~esperar"),)
            nuevo_trayecto = trayecto + (destino,)
            candidato = (
                nueva_exposicion,
                nuevo_turno,
                nuevo_costo,
                nueva_accion,
                nuevo_trayecto,
            )
            nueva_clave = (destino, nuevo_turno)
            if nueva_clave in mejor and mejor[nueva_clave] <= candidato:
                continue
            mejor[nueva_clave] = candidato
            heapq.heappush(frontera, (*candidato, destino))

    return _resultado("sin_ruta_en_horizonte", None, None, None, None, expansiones, inicio)


def _pronostico_en(
    actual: CondicionTurno,
    pronostico: tuple[CondicionTurno, ...],
    indice: int,
) -> CondicionTurno:
    """Preserva cierres activos; las reglas actuales solo los agregan."""

    futuro = pronostico[indice] if indice < len(pronostico) else CondicionTurno()
    anteriores = pronostico[: indice + 1]
    return CondicionTurno(
        nodos_bloqueados=futuro.nodos_bloqueados,
        aristas_cerradas=actual.aristas_cerradas | frozenset(
            arista for paso in anteriores for arista in paso.aristas_cerradas
        ),
        segmentos_cerrados=actual.segmentos_cerrados | frozenset(
            segmento for paso in anteriores for segmento in paso.segmentos_cerrados
        ),
        exposicion_nodo=futuro.exposicion_nodo,
    )


def _refugio_en_nodo(refugios_por_id: Mapping[str, Refugio], refugios: frozenset[str], nodo: str) -> str | None:
    return next(
        (refugio_id for refugio_id in sorted(refugios) if refugios_por_id[refugio_id].nodo == nodo),
        None,
    )


def _validar_condicion(condicion: CondicionTurno, grafo: Grafo) -> None:
    nodos_conocidos = set(grafo.mapa.nodos_por_id)
    aristas_conocidas = {calle.id for calle in grafo.mapa.calles}
    segmentos_conocidos = {calle.segmento_id for calle in grafo.mapa.calles}
    if condicion.nodos_bloqueados - nodos_conocidos or set(condicion.exposicion_nodo) - nodos_conocidos:
        raise KeyError("La condición temporal referencia un nodo desconocido.")
    if condicion.aristas_cerradas - aristas_conocidas:
        raise KeyError("La condición temporal referencia una arista desconocida.")
    if condicion.segmentos_cerrados - segmentos_conocidos:
        raise KeyError("La condición temporal referencia un segmento desconocido.")


def _validar_limites(horizonte: int, expansiones: int, presupuesto_ms: float) -> None:
    if isinstance(horizonte, bool) or not isinstance(horizonte, int) or not 1 <= horizonte <= 12:
        raise ValueError("El horizonte debe ser un entero entre 1 y 12 turnos.")
    if isinstance(expansiones, bool) or not isinstance(expansiones, int) or expansiones < 1:
        raise ValueError("El límite de expansiones debe ser un entero positivo.")
    if isinstance(presupuesto_ms, bool) or not isinstance(presupuesto_ms, (int, float)) or not math.isfinite(presupuesto_ms) or presupuesto_ms <= 0:
        raise ValueError("El presupuesto temporal debe ser positivo y finito.")


def _resultado(
    estado: str,
    trayecto: tuple[str, ...] | None,
    turnos: int | None,
    exposicion: float | None,
    costo: float | None,
    expansiones: int,
    inicio: float,
) -> ResultadoRutaTemporal:
    return ResultadoRutaTemporal(
        estado=estado,
        trayecto=trayecto,
        turnos=turnos,
        exposicion_acumulada=exposicion,
        costo_ponderado_m=costo,
        expansiones=expansiones,
        duracion_ms=(perf_counter() - inicio) * 1000,
    )
