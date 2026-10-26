"""Movimiento zombie y resolución simultánea de intenciones.

Las reglas que el reto deja abiertas se agrupan en ConfiguracionReglas; sus
valores iniciales son supuestos de producto y se conservan en la evidencia.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, replace

from navira.domain.mapa import Calle, Grafo
from navira.domain.modelo import (
    EstadoPartida,
    EstadoSobreviviente,
    EstadoZombie,
    FaseTurno,
    IntencionMovimiento,
    Partida,
    Sobreviviente,
    TipoZombie,
    Zombie,
    validar_contexto_intencion,
)


@dataclass(frozen=True, slots=True)
class ConfiguracionReglas:
    """Parámetros provisionales para reglas no precisadas por el reto."""

    alcance_corredor_hops: int = 3
    pasos_corredor: int = 2
    radio_dormido_hops: int = 2
    dormido_mueve_al_despertar: bool = False

    def __post_init__(self) -> None:
        if min(self.alcance_corredor_hops, self.pasos_corredor, self.radio_dormido_hops) < 0:
            raise ValueError("Los alcances y pasos de configuración no pueden ser negativos.")


@dataclass(frozen=True, slots=True)
class MovimientoZombie:
    zombie_id: str
    origen: str
    destino: str
    tramos: tuple[Calle, ...]


@dataclass(frozen=True, slots=True)
class MovimientoSobreviviente:
    sobreviviente_id: str
    origen: str
    destino: str
    calle: Calle | None


@dataclass(frozen=True, slots=True)
class ResultadoTurno:
    partida: Partida
    movimientos_zombies: tuple[MovimientoZombie, ...]
    movimientos_sobrevivientes: tuple[MovimientoSobreviviente, ...]
    mordidos: tuple[str, ...]
    evacuados: tuple[str, ...]
    intenciones_rechazadas: tuple[str, ...]


def resolver_turno(
    partida: Partida,
    grafo: Grafo,
    intenciones: tuple[IntencionMovimiento, ...] = (),
    *,
    rng: random.Random,
    aristas_cerradas: frozenset[str] = frozenset(),
    segmentos_cerrados: frozenset[str] = frozenset(),
    configuracion: ConfiguracionReglas = ConfiguracionReglas(),
) -> ResultadoTurno:
    """Avanza zombies primero y luego resuelve a la vez a los sobrevivientes.

    Esta función procesa un solo turno sin manejar el reloj ni la persistencia.
    Requiere una partida activa en fase PREPARACION; P1-04 añadirá el ciclo de
    reloj/snapshots y la transición al siguiente turno.
    """

    if partida.estado is not EstadoPartida.ACTIVA or partida.fase is not FaseTurno.PREPARACION:
        raise ValueError("El turno debe iniciar con una partida activa en preparación.")
    partida.validar_mapa(grafo.mapa)

    intenciones_por_id: dict[str, IntencionMovimiento] = {}
    for intencion in intenciones:
        if intencion.sobreviviente_id in intenciones_por_id:
            raise ValueError(f"Intención duplicada para {intencion.sobreviviente_id}.")
        intenciones_por_id[intencion.sobreviviente_id] = intencion

    zombies_actualizados: list[Zombie] = []
    movimientos_zombies: list[MovimientoZombie] = []
    for zombie in sorted(partida.zombies, key=lambda item: item.id):
        actualizado, movimiento = _mover_zombie(
            zombie,
            partida.sobrevivientes,
            grafo,
            partida.turno,
            rng,
            aristas_cerradas,
            segmentos_cerrados,
            configuracion,
        )
        zombies_actualizados.append(actualizado)
        movimientos_zombies.append(movimiento)

    partida_decisiones = replace(
        partida,
        zombies=tuple(zombies_actualizados),
        fase=FaseTurno.DECISIONES,
    )
    bloqueados_horda = _nodos_bloqueados_por_horda(
        zombies_actualizados, grafo, aristas_cerradas, segmentos_cerrados
    )

    movimientos_sobrevivientes: list[MovimientoSobreviviente] = []
    sobrevivientes_actualizados: list[Sobreviviente] = []
    intenciones_rechazadas: list[str] = []
    por_id = {sobreviviente.id: sobreviviente for sobreviviente in partida.sobrevivientes}

    for sobreviviente in partida.sobrevivientes:
        intencion = intenciones_por_id.get(sobreviviente.id)
        calle_elegida: Calle | None = None
        destino = sobreviviente.nodo

        if sobreviviente.estado is EstadoSobreviviente.ACTIVO and intencion is not None:
            try:
                validar_contexto_intencion(partida_decisiones, sobreviviente, intencion)
                calle_elegida = _calle_hacia(
                    grafo,
                    sobreviviente.nodo,
                    intencion.destino,
                    aristas_cerradas,
                    segmentos_cerrados,
                )
                if intencion.destino == sobreviviente.nodo:
                    destino = sobreviviente.nodo
                elif calle_elegida is None or intencion.destino in bloqueados_horda:
                    raise ValueError("Movimiento no transitable.")
                else:
                    destino = intencion.destino
            except ValueError:
                destino = sobreviviente.nodo
                calle_elegida = None
                intenciones_rechazadas.append(sobreviviente.id)

        movimientos_sobrevivientes.append(
            MovimientoSobreviviente(sobreviviente.id, sobreviviente.nodo, destino, calle_elegida)
        )
        sobrevivientes_actualizados.append(replace(sobreviviente, nodo=destino))

    mordidos = _resolver_mordidas(
        movimientos_sobrevivientes,
        movimientos_zombies,
        zombies_actualizados,
    )
    refugios_por_nodo = {refugio.nodo: refugio.id for refugio in grafo.mapa.refugios}
    evacuados: list[str] = []
    finales: list[Sobreviviente] = []
    for sobreviviente in sobrevivientes_actualizados:
        if sobreviviente.id in mordidos:
            finales.append(replace(sobreviviente, estado=EstadoSobreviviente.MORDIDO))
        elif sobreviviente.estado is EstadoSobreviviente.ACTIVO and sobreviviente.nodo in refugios_por_nodo:
            finales.append(
                replace(
                    sobreviviente,
                    estado=EstadoSobreviviente.EVACUADO,
                    refugio_objetivo=refugios_por_nodo[sobreviviente.nodo],
                )
            )
            evacuados.append(sobreviviente.id)
        else:
            finales.append(sobreviviente)

    partida_resuelta = replace(
        partida_decisiones,
        sobrevivientes=tuple(finales),
        fase=FaseTurno.RESUELTA,
    )
    partida_resuelta.validar_mapa(grafo.mapa)
    return ResultadoTurno(
        partida=partida_resuelta,
        movimientos_zombies=tuple(movimientos_zombies),
        movimientos_sobrevivientes=tuple(movimientos_sobrevivientes),
        mordidos=tuple(sorted(mordidos)),
        evacuados=tuple(sorted(evacuados)),
        intenciones_rechazadas=tuple(sorted(intenciones_rechazadas)),
    )


def _mover_zombie(
    zombie: Zombie,
    sobrevivientes: tuple[Sobreviviente, ...],
    grafo: Grafo,
    turno: int,
    rng: random.Random,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
    configuracion: ConfiguracionReglas,
) -> tuple[Zombie, MovimientoZombie]:
    origen = zombie.nodo
    se_desperto = False
    if zombie.estado is EstadoZombie.DORMIDO:
        cerca = any(
            sobreviviente.estado is EstadoSobreviviente.ACTIVO
            and _distancia_hops(origen, sobreviviente.nodo, grafo, aristas_cerradas, segmentos_cerrados, dirigido=False)
            <= configuracion.radio_dormido_hops
            for sobreviviente in sobrevivientes
        )
        if not cerca:
            return zombie, MovimientoZombie(zombie.id, origen, origen, ())
        zombie = replace(zombie, tipo=TipoZombie.CAMINANTE, estado=EstadoZombie.ACTIVO, turno_activacion=turno)
        se_desperto = True
        if not configuracion.dormido_mueve_al_despertar:
            return zombie, MovimientoZombie(zombie.id, origen, origen, ())

    if zombie.tipo is TipoZombie.HORDA:
        return zombie, MovimientoZombie(zombie.id, origen, origen, ())
    if (
        zombie.tipo is TipoZombie.CAMINANTE
        and not se_desperto
        and turno % 2 != zombie.fase_movimiento
    ):
        return zombie, MovimientoZombie(zombie.id, origen, origen, ())

    pasos = configuracion.pasos_corredor if zombie.tipo is TipoZombie.CORREDOR else 1
    nodo_actual = origen
    tramos: list[Calle] = []
    objetivo = _objetivo_corredor(
        zombie,
        sobrevivientes,
        grafo,
        aristas_cerradas,
        segmentos_cerrados,
        configuracion.alcance_corredor_hops,
    ) if zombie.tipo is TipoZombie.CORREDOR else None

    for _ in range(pasos):
        if objetivo is not None and nodo_actual == objetivo:
            break
        salientes = grafo.calles_desde(
            nodo_actual,
            aristas_cerradas=aristas_cerradas,
            segmentos_cerrados=segmentos_cerrados,
        )
        if not salientes:
            break
        if objetivo is not None:
            ruta = _ruta_corta(nodo_actual, objetivo, grafo, aristas_cerradas, segmentos_cerrados)
            siguiente = ruta[0] if ruta else None
        else:
            siguiente = None
        calle = siguiente if siguiente is not None else rng.choice(salientes)
        tramos.append(calle)
        nodo_actual = calle.destino

    actualizado = replace(zombie, nodo=nodo_actual)
    return actualizado, MovimientoZombie(zombie.id, origen, nodo_actual, tuple(tramos))


def _objetivo_corredor(
    zombie: Zombie,
    sobrevivientes: tuple[Sobreviviente, ...],
    grafo: Grafo,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
    alcance: int,
) -> str | None:
    candidatos: list[tuple[int, str, str]] = []
    for sobreviviente in sobrevivientes:
        if sobreviviente.estado is not EstadoSobreviviente.ACTIVO:
            continue
        distancia = _distancia_hops(
            zombie.nodo,
            sobreviviente.nodo,
            grafo,
            aristas_cerradas,
            segmentos_cerrados,
            dirigido=True,
        )
        if distancia <= alcance:
            candidatos.append((distancia, sobreviviente.id, sobreviviente.nodo))
    return min(candidatos)[2] if candidatos else None


def _ruta_corta(
    inicio: str,
    destino: str,
    grafo: Grafo,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
) -> tuple[Calle, ...]:
    """Ruta por saltos con desempate estable por ID de calle."""

    if inicio == destino:
        return ()
    pendientes = deque([inicio])
    anterior: dict[str, tuple[str, Calle] | None] = {inicio: None}
    while pendientes:
        actual = pendientes.popleft()
        for calle in grafo.calles_desde(
            actual,
            aristas_cerradas=aristas_cerradas,
            segmentos_cerrados=segmentos_cerrados,
        ):
            if calle.destino in anterior:
                continue
            anterior[calle.destino] = (actual, calle)
            if calle.destino == destino:
                pendientes.clear()
                break
            pendientes.append(calle.destino)
    if destino not in anterior:
        return ()

    ruta: list[Calle] = []
    nodo = destino
    while anterior[nodo] is not None:
        previo, calle = anterior[nodo]  # type: ignore[misc]
        ruta.append(calle)
        nodo = previo
    ruta.reverse()
    return tuple(ruta)


def _distancia_hops(
    inicio: str,
    destino: str,
    grafo: Grafo,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
    *,
    dirigido: bool,
) -> int:
    if inicio == destino:
        return 0
    pendientes = deque([(inicio, 0)])
    visitados = {inicio}
    inversas: dict[str, list[str]] | None = None
    if not dirigido:
        inversas = {nodo_id: [] for nodo_id in grafo.mapa.nodos_por_id}
        for calle in grafo.mapa.calles:
            if calle.id not in aristas_cerradas and calle.segmento_id not in segmentos_cerrados:
                inversas[calle.destino].append(calle.origen)

    while pendientes:
        nodo, distancia = pendientes.popleft()
        vecinos = [
            calle.destino
            for calle in grafo.calles_desde(
                nodo,
                aristas_cerradas=aristas_cerradas,
                segmentos_cerrados=segmentos_cerrados,
            )
        ]
        if inversas is not None:
            vecinos.extend(inversas[nodo])
        for vecino in vecinos:
            if vecino == destino:
                return distancia + 1
            if vecino not in visitados:
                visitados.add(vecino)
                pendientes.append((vecino, distancia + 1))
    return 10**9


def _calle_hacia(
    grafo: Grafo,
    origen: str,
    destino: str,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
) -> Calle | None:
    opciones = [
        calle
        for calle in grafo.calles_desde(
            origen,
            aristas_cerradas=aristas_cerradas,
            segmentos_cerrados=segmentos_cerrados,
        )
        if calle.destino == destino
    ]
    return min(opciones, key=lambda calle: (calle.distancia_m, calle.id)) if opciones else None


def _nodos_bloqueados_por_horda(
    zombies: list[Zombie],
    grafo: Grafo,
    aristas_cerradas: frozenset[str],
    segmentos_cerrados: frozenset[str],
) -> frozenset[str]:
    bloqueados: set[str] = set()
    for zombie in zombies:
        if zombie.tipo is not TipoZombie.HORDA or zombie.estado is not EstadoZombie.ACTIVO:
            continue
        bloqueados.add(zombie.nodo)
        for calle in grafo.calles_desde(
            zombie.nodo,
            aristas_cerradas=aristas_cerradas,
            segmentos_cerrados=segmentos_cerrados,
        ):
            if calle.origen == zombie.nodo:
                bloqueados.add(calle.destino)
        for calle in grafo.mapa.calles:
            if calle.id in aristas_cerradas or calle.segmento_id in segmentos_cerrados:
                continue
            if calle.destino == zombie.nodo:
                bloqueados.add(calle.origen)
    return frozenset(bloqueados)


def _resolver_mordidas(
    movimientos_sobrevivientes: list[MovimientoSobreviviente],
    movimientos_zombies: list[MovimientoZombie],
    zombies: list[Zombie],
) -> set[str]:
    posiciones_zombie = {zombie.nodo for zombie in zombies if zombie.estado is EstadoZombie.ACTIVO}
    mordidos: set[str] = set()
    tramos_zombie = [tramo for movimiento in movimientos_zombies for tramo in movimiento.tramos]
    for movimiento in movimientos_sobrevivientes:
        if movimiento.destino in posiciones_zombie:
            mordidos.add(movimiento.sobreviviente_id)
            continue
        calle = movimiento.calle
        if calle is None:
            continue
        if any(
            tramo.segmento_id == calle.segmento_id
            and tramo.origen == calle.destino
            and tramo.destino == calle.origen
            for tramo in tramos_zombie
        ):
            mordidos.add(movimiento.sobreviviente_id)
    return mordidos
