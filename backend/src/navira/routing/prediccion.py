"""Pronóstico acotado de ocupación a partir de observaciones permitidas.

Este módulo no recibe la entidad `Partida`, zombies dormidos, fase privada de
caminantes ni RNG. Las estimaciones son escenarios del prototipo, no
probabilidades calibradas de mordida o supervivencia.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Mapping

from navira.domain.mapa import Calle, Grafo
from navira.domain.modelo import TipoZombie
from navira.routing.temporal import CondicionTurno


@dataclass(frozen=True, slots=True)
class ZombieObservable:
    """Proyección mínima de un zombie activo que puede conocer el planificador."""

    id: str
    tipo: TipoZombie
    nodo: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.nodo.strip():
            raise ValueError("La observación del zombie requiere identidad y nodo.")
        if not isinstance(self.tipo, TipoZombie) or self.tipo is TipoZombie.DORMIDO:
            raise ValueError("Un zombie dormido no puede entrar al pronosticador.")


@dataclass(frozen=True, slots=True)
class SobrevivienteObservable:
    """Posición pública usada como escenario estático para perseguidores."""

    id: str
    nodo: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.nodo.strip():
            raise ValueError("La observación del sobreviviente requiere identidad y nodo.")


@dataclass(frozen=True, slots=True)
class ResultadoPronostico:
    """Condiciones futuras y supuestos visibles para cualquier consumidor."""

    turnos: tuple[CondicionTurno, ...]
    supuestos: tuple[str, ...]


def pronosticar_zombies_visibles(
    grafo: Grafo,
    zombies: tuple[ZombieObservable, ...],
    sobrevivientes: tuple[SobrevivienteObservable, ...],
    *,
    turno_actual: int,
    horizonte_turnos: int = 6,
    alcance_corredor_hops: int = 3,
    pasos_corredor: int = 2,
    aristas_cerradas: frozenset[str] = frozenset(),
    segmentos_cerrados: frozenset[str] = frozenset(),
) -> ResultadoPronostico:
    """Estima ocupación futura en el grafo dirigido sin consultar el estado privado.

    Caminantes ramifican por igual entre salidas legales y mezclan ambas fases
    posibles porque la fase real no se entrega. Corredores siguen la regla
    provisional de objetivo más cercano sobre las posiciones observadas, que
    se mantienen fijas durante el horizonte. Las hordas permanecen estáticas
    según el prototipo. Todos estos supuestos se reportan y no son reglas
    oficiales.
    """

    _validar_parametros(grafo, zombies, sobrevivientes, turno_actual, horizonte_turnos,
                        alcance_corredor_hops, pasos_corredor, aristas_cerradas,
                        segmentos_cerrados)
    por_turno: list[dict[str, float]] = [dict() for _ in range(horizonte_turnos)]
    cruces_por_turno: list[dict[str, float]] = [dict() for _ in range(horizonte_turnos)]
    bloqueos: list[set[str]] = [set() for _ in range(horizonte_turnos)]
    supuestos: set[str] = set()
    destinos_sobrevivientes = tuple(sorted((item.id, item.nodo) for item in sobrevivientes))
    aristas_inversas = _indice_aristas_inversas(grafo)

    for zombie in sorted(zombies, key=lambda item: item.id):
        if zombie.tipo is TipoZombie.HORDA:
            supuestos.add("horda_estatica_provisional")
            footprint = {zombie.nodo}
            footprint.update(
                calle.destino for calle in grafo.calles_desde(
                    zombie.nodo,
                    aristas_cerradas=aristas_cerradas,
                    segmentos_cerrados=segmentos_cerrados,
                )
            )
            footprint.update(
                calle.origen for calle in grafo.mapa.calles
                if calle.destino == zombie.nodo
                and calle.id not in aristas_cerradas
                and calle.segmento_id not in segmentos_cerrados
            )
            for bloqueados in bloqueos:
                bloqueados.update(footprint)
            continue

        if zombie.tipo is TipoZombie.CAMINANTE:
            supuestos.add("caminante_uniforme_fase_desconocida")
            estados: dict[tuple[str, int], float] = {(zombie.nodo, 0): 0.5, (zombie.nodo, 1): 0.5}
            for indice in range(horizonte_turnos):
                turno_futuro = turno_actual + indice + 1
                estados, cruces = _avanzar_caminante(
                    grafo, estados, turno_futuro, aristas_cerradas, segmentos_cerrados,
                    aristas_inversas,
                )
                _acumular_ocupacion(por_turno[indice], estados)
                _acumular_exposicion_aristas(cruces_por_turno[indice], cruces)
            continue

        if zombie.tipo is TipoZombie.CORREDOR:
            supuestos.add("corredor_objetivo_con_sobrevivientes_estaticos")
            estados_corredor: dict[str, float] = {zombie.nodo: 1.0}
            for indice in range(horizonte_turnos):
                estados_corredor, ocupacion_turno, cruces_turno = _avanzar_corredor(
                    grafo,
                    estados_corredor,
                    destinos_sobrevivientes,
                    alcance_corredor_hops,
                    pasos_corredor,
                    aristas_cerradas,
                    segmentos_cerrados,
                    aristas_inversas,
                )
                _acumular_ocupacion(por_turno[indice], ocupacion_turno)
                _acumular_exposicion_aristas(cruces_por_turno[indice], cruces_turno)

    condiciones = tuple(
        CondicionTurno(
            nodos_bloqueados=frozenset(bloqueos[indice]),
            exposicion_nodo={
                nodo: round(min(1.0, puntaje), 12)
                for nodo, puntaje in por_turno[indice].items()
                if puntaje > 0
            },
            exposicion_arista={
                arista: round(min(1.0, puntaje), 12)
                for arista, puntaje in cruces_por_turno[indice].items()
                if puntaje > 0
            },
        )
        for indice in range(horizonte_turnos)
    )
    return ResultadoPronostico(condiciones, tuple(sorted(supuestos)))


def _avanzar_caminante(
    grafo: Grafo,
    estados: Mapping[tuple[str, int], float],
    turno: int,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
    aristas_inversas: Mapping[str, tuple[str, ...]],
) -> tuple[dict[tuple[str, int], float], dict[str, float]]:
    siguientes: dict[tuple[str, int], float] = {}
    cruces: dict[str, float] = {}
    for (nodo, fase), peso in estados.items():
        if turno % 2 != fase:
            siguientes[(nodo, fase)] = siguientes.get((nodo, fase), 0.0) + peso
            continue
        salientes = grafo.calles_desde(
            nodo, aristas_cerradas=aristas_cerradas, segmentos_cerrados=segmentos_cerrados
        )
        if not salientes:
            siguientes[(nodo, fase)] = siguientes.get((nodo, fase), 0.0) + peso
            continue
        por_salida = peso / len(salientes)
        for calle in salientes:
            clave = (calle.destino, fase)
            siguientes[clave] = siguientes.get(clave, 0.0) + por_salida
            for arista_inversa in aristas_inversas.get(calle.id, ()):
                cruces[arista_inversa] = cruces.get(arista_inversa, 0.0) + por_salida
    return siguientes, cruces


def _avanzar_corredor(
    grafo: Grafo,
    estados: Mapping[str, float],
    sobrevivientes: tuple[tuple[str, str], ...],
    alcance: int,
    pasos: int,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
    aristas_inversas: Mapping[str, tuple[str, ...]],
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    siguientes: dict[str, float] = {}
    ocupacion: dict[str, float] = {}
    cruces: dict[str, float] = {}
    for inicio, peso in estados.items():
        nodo = inicio
        objetivo = _objetivo_visible(
            grafo, nodo, sobrevivientes, alcance, aristas_cerradas, segmentos_cerrados
        )
        distribucion = {nodo: peso}
        for _ in range(pasos):
            actualizada: dict[str, float] = {}
            for posicion, masa in distribucion.items():
                if objetivo is not None and posicion == objetivo:
                    actualizada[posicion] = actualizada.get(posicion, 0.0) + masa
                    continue
                salientes = grafo.calles_desde(
                    posicion,
                    aristas_cerradas=aristas_cerradas,
                    segmentos_cerrados=segmentos_cerrados,
                )
                if not salientes:
                    actualizada[posicion] = actualizada.get(posicion, 0.0) + masa
                    continue
                camino = (
                    _primer_paso(grafo, posicion, objetivo, aristas_cerradas, segmentos_cerrados)
                    if objetivo is not None
                    else None
                )
                elegidas = (camino,) if camino is not None else salientes
                por_salida = masa / len(elegidas)
                for calle in elegidas:
                    actualizada[calle.destino] = actualizada.get(calle.destino, 0.0) + por_salida
                    for arista_inversa in aristas_inversas.get(calle.id, ()):
                        cruces[arista_inversa] = cruces.get(arista_inversa, 0.0) + por_salida
            distribucion = actualizada
            for posicion, masa in distribucion.items():
                ocupacion[posicion] = ocupacion.get(posicion, 0.0) + masa
        for posicion, masa in distribucion.items():
            siguientes[posicion] = siguientes.get(posicion, 0.0) + masa
    return siguientes, ocupacion, cruces


def _indice_aristas_inversas(grafo: Grafo) -> Mapping[str, tuple[str, ...]]:
    """Builds a linear-time reverse-edge lookup for the immutable graph."""

    por_direccion: dict[tuple[str, str, str], list[str]] = {}
    for calle in grafo.mapa.calles:
        por_direccion.setdefault(
            (calle.segmento_id, calle.origen, calle.destino), []
        ).append(calle.id)
    return {
        calle.id: tuple(
            por_direccion.get((calle.segmento_id, calle.destino, calle.origen), ())
        )
        for calle in grafo.mapa.calles
    }


def _acumular_exposicion_aristas(destino: dict[str, float], fuente: Mapping[str, float]) -> None:
    """Caps accumulated zombie edge mass as a bounded exposure score."""

    for arista, masa in fuente.items():
        destino[arista] = min(1.0, destino.get(arista, 0.0) + masa)


def _objetivo_visible(
    grafo: Grafo,
    origen: str,
    sobrevivientes: tuple[tuple[str, str], ...],
    alcance: int,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
) -> str | None:
    sobrevivientes_por_nodo: dict[str, list[str]] = {}
    for sobreviviente_id, nodo in sobrevivientes:
        sobrevivientes_por_nodo.setdefault(nodo, []).append(sobreviviente_id)
    if origen in sobrevivientes_por_nodo:
        return origen

    distancias = {origen: 0}
    cola = deque([origen])
    candidatos: list[tuple[int, str, str]] = []
    while cola:
        nodo = cola.popleft()
        distancia = distancias[nodo]
        if distancia >= alcance:
            continue
        for calle in grafo.calles_desde(
            nodo, aristas_cerradas=aristas_cerradas, segmentos_cerrados=segmentos_cerrados
        ):
            if calle.destino in distancias:
                continue
            nueva_distancia = distancia + 1
            distancias[calle.destino] = nueva_distancia
            for sobreviviente_id in sobrevivientes_por_nodo.get(calle.destino, ()):
                candidatos.append((nueva_distancia, sobreviviente_id, calle.destino))
            cola.append(calle.destino)
    return min(candidatos)[2] if candidatos else None


def _primer_paso(
    grafo: Grafo,
    origen: str,
    destino: str,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
) -> Calle | None:
    if origen == destino:
        return None
    anterior: dict[str, tuple[str, Calle] | None] = {origen: None}
    cola = deque([origen])
    while cola:
        nodo = cola.popleft()
        for calle in grafo.calles_desde(
            nodo, aristas_cerradas=aristas_cerradas, segmentos_cerrados=segmentos_cerrados
        ):
            if calle.destino in anterior:
                continue
            anterior[calle.destino] = (nodo, calle)
            if calle.destino == destino:
                actual = destino
                while (entrada := anterior[actual]) is not None and entrada[0] != origen:
                    actual = entrada[0]
                entrada = anterior[actual]
                return entrada[1] if entrada is not None else None
            cola.append(calle.destino)
    return None


def _acumular_ocupacion(destino: dict[str, float], estados: Mapping[object, float]) -> None:
    for estado, masa in estados.items():
        nodo = estado[0] if isinstance(estado, tuple) else estado
        destino[nodo] = destino.get(nodo, 0.0) + masa


def _validar_parametros(
    grafo: Grafo,
    zombies: tuple[ZombieObservable, ...],
    sobrevivientes: tuple[SobrevivienteObservable, ...],
    turno_actual: int,
    horizonte: int,
    alcance: int,
    pasos: int,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
) -> None:
    if isinstance(turno_actual, bool) or not isinstance(turno_actual, int) or turno_actual < 0:
        raise ValueError("El turno actual debe ser un entero no negativo.")
    if isinstance(horizonte, bool) or not isinstance(horizonte, int) or not 1 <= horizonte <= 12:
        raise ValueError("El horizonte debe estar entre 1 y 12 turnos.")
    if isinstance(alcance, bool) or not isinstance(alcance, int) or alcance < 0:
        raise ValueError("El alcance del corredor debe ser un entero no negativo.")
    if isinstance(pasos, bool) or not isinstance(pasos, int) or not 0 <= pasos <= 4:
        raise ValueError("Los pasos del corredor deben estar entre 0 y 4.")
    if len({zombie.id for zombie in zombies}) != len(zombies):
        raise ValueError("La observación contiene zombies duplicados.")
    if len({sobreviviente.id for sobreviviente in sobrevivientes}) != len(sobrevivientes):
        raise ValueError("La observación contiene sobrevivientes duplicados.")
    conocidos = set(grafo.mapa.nodos_por_id)
    if any(zombie.nodo not in conocidos for zombie in zombies) or any(
        sobreviviente.nodo not in conocidos for sobreviviente in sobrevivientes
    ):
        raise KeyError("La observación referencia un nodo desconocido.")
    ids_aristas = {calle.id for calle in grafo.mapa.calles}
    ids_segmentos = {calle.segmento_id for calle in grafo.mapa.calles}
    if aristas_cerradas - ids_aristas or segmentos_cerrados - ids_segmentos:
        raise KeyError("El pronóstico referencia un cierre desconocido.")

