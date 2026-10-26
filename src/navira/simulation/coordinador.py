"""Coordinación pura de transiciones versionadas de una partida.

Este módulo prepara snapshots completos en memoria. La confirmación atómica
entre procesos requiere un adaptador con compare-and-swap, todavía pendiente.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field, replace

from navira.domain.mapa import Grafo
from navira.domain.modelo import EstadoPartida, FaseTurno, IntencionMovimiento, Partida
from navira.simulation.resolver import (
    ConfiguracionReglas,
    MovimientoZombie,
    PreparacionTurno,
    ResultadoTurno,
    preparar_turno as preparar_turno_puro,
    resolver_decisiones,
)

EstadoAleatorio = tuple[int, tuple[int, ...], float | None]


@dataclass(frozen=True, slots=True)
class EventoCierre:
    """Cierre de una arista dirigida o de un segmento desde un turno dado."""

    id: str
    turno_objetivo: int
    aristas: frozenset[str] = frozenset()
    segmentos: frozenset[str] = frozenset()
    causa: str = "evento"

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.causa.strip():
            raise ValueError("El evento requiere id y causa no vacíos.")
        if self.turno_objetivo < 0:
            raise ValueError("El turno del evento no puede ser negativo.")
        object.__setattr__(self, "aristas", frozenset(self.aristas))
        object.__setattr__(self, "segmentos", frozenset(self.segmentos))
        if not self.aristas and not self.segmentos:
            raise ValueError("El evento debe cerrar al menos una arista o segmento.")


@dataclass(frozen=True, slots=True)
class SnapshotMundo:
    """Estado privado, íntegro e identificado por partida/fase/versión."""

    partida: Partida
    version: int
    aristas_cerradas: frozenset[str] = frozenset()
    segmentos_cerrados: frozenset[str] = frozenset()
    eventos_programados: tuple[EventoCierre, ...] = ()
    eventos_aplicados: tuple[str, ...] = ()
    movimientos_zombies: tuple[MovimientoZombie, ...] = ()
    _estado_rng: EstadoAleatorio | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.version < 0:
            raise ValueError("La versión del snapshot no puede ser negativa.")
        object.__setattr__(self, "aristas_cerradas", frozenset(self.aristas_cerradas))
        object.__setattr__(self, "segmentos_cerrados", frozenset(self.segmentos_cerrados))
        object.__setattr__(self, "eventos_programados", tuple(self.eventos_programados))
        object.__setattr__(self, "eventos_aplicados", tuple(self.eventos_aplicados))
        object.__setattr__(self, "movimientos_zombies", tuple(self.movimientos_zombies))
        if len(self.eventos_aplicados) != len(set(self.eventos_aplicados)):
            raise ValueError("Un evento no puede figurar aplicado dos veces.")
        ids = [evento.id for evento in self.eventos_programados]
        if len(ids) != len(set(ids)):
            raise ValueError("Los eventos programados deben tener IDs únicos.")
        if not set(self.eventos_aplicados) <= set(ids):
            raise ValueError("El snapshot referencia un evento aplicado que no está programado.")

    @property
    def identidad(self) -> tuple[str, int, FaseTurno, str, int]:
        """Clave de snapshot; la versión crece también entre fases del turno."""

        partida = self.partida
        return (partida.run_id, partida.turno, partida.fase, partida.map_version, self.version)


@dataclass(frozen=True, slots=True)
class TurnoVersionado:
    """Snapshots completos de decisión y resolución calculados antes de devolver."""

    decisiones: SnapshotMundo
    resuelto: SnapshotMundo
    resultado: ResultadoTurno
    eventos_aplicados_ahora: tuple[str, ...]


def crear_snapshot_inicial(
    partida: Partida,
    grafo: Grafo,
    *,
    rng: random.Random,
    eventos: tuple[EventoCierre, ...] = (),
) -> SnapshotMundo:
    """Valida y captura el estado inicial junto al estado privado del RNG."""

    if partida.fase is not FaseTurno.PREPARACION:
        raise ValueError("El snapshot inicial debe comenzar en preparación.")
    partida.validar_mapa(grafo.mapa)
    _validar_eventos(eventos, grafo, partida.turno)
    return SnapshotMundo(
        partida=partida,
        version=0,
        eventos_programados=eventos,
        _estado_rng=copy.deepcopy(rng.getstate()),
    )


def avanzar_turno(
    snapshot: SnapshotMundo,
    grafo: Grafo,
    *,
    version_esperada: int,
    intenciones: tuple[IntencionMovimiento, ...] = (),
    configuracion: ConfiguracionReglas = ConfiguracionReglas(),
) -> TurnoVersionado:
    """Atajo automático: prepara zombies y resuelve decisiones en una llamada.

    El modo de juego debe usar `preparar_turno_versionado` y
    `resolver_turno_versionado` para recibir órdenes entre ambas fases.
    """

    decisiones, eventos_aplicados = preparar_turno_versionado(
        snapshot,
        grafo,
        version_esperada=version_esperada,
        configuracion=configuracion,
    )
    resuelto, resultado = resolver_turno_versionado(
        decisiones,
        grafo,
        version_esperada=decisiones.version,
        intenciones=intenciones,
    )
    return TurnoVersionado(decisiones, resuelto, resultado, eventos_aplicados)


def preparar_turno_versionado(
    snapshot: SnapshotMundo,
    grafo: Grafo,
    *,
    version_esperada: int,
    configuracion: ConfiguracionReglas = ConfiguracionReglas(),
) -> tuple[SnapshotMundo, tuple[str, ...]]:
    """Aplica eventos y movimiento zombie; devuelve la fase abierta a órdenes."""

    if snapshot.version != version_esperada:
        raise ValueError("La versión esperada ya no coincide con el snapshot actual.")
    partida = snapshot.partida
    if partida.estado is not EstadoPartida.ACTIVA or partida.fase is not FaseTurno.PREPARACION:
        raise ValueError("Solo se puede avanzar una partida activa en preparación.")
    partida.validar_mapa(grafo.mapa)
    _validar_eventos(
        snapshot.eventos_programados,
        grafo,
        partida.turno,
        frozenset(snapshot.eventos_aplicados),
    )
    if snapshot._estado_rng is None:
        raise ValueError("El snapshot no tiene estado aleatorio privado para continuar.")

    vencidos = tuple(
        evento
        for evento in snapshot.eventos_programados
        if evento.turno_objetivo < partida.turno and evento.id not in snapshot.eventos_aplicados
    )
    if vencidos:
        raise ValueError("Hay eventos vencidos sin aplicar; no se puede omitir un cierre.")
    ahora = tuple(
        evento
        for evento in snapshot.eventos_programados
        if evento.turno_objetivo == partida.turno and evento.id not in snapshot.eventos_aplicados
    )
    cierres_aristas = snapshot.aristas_cerradas | frozenset(
        arista for evento in ahora for arista in evento.aristas
    )
    cierres_segmentos = snapshot.segmentos_cerrados | frozenset(
        segmento for evento in ahora for segmento in evento.segmentos
    )

    rng = random.Random()
    rng.setstate(copy.deepcopy(snapshot._estado_rng))
    preparacion: PreparacionTurno = preparar_turno_puro(
        partida,
        grafo,
        rng=rng,
        aristas_cerradas=cierres_aristas,
        segmentos_cerrados=cierres_segmentos,
        configuracion=configuracion,
    )
    aplicados = snapshot.eventos_aplicados + tuple(evento.id for evento in ahora)
    decisiones = SnapshotMundo(
        partida=preparacion.partida,
        version=snapshot.version + 1,
        aristas_cerradas=cierres_aristas,
        segmentos_cerrados=cierres_segmentos,
        eventos_programados=snapshot.eventos_programados,
        eventos_aplicados=aplicados,
        movimientos_zombies=preparacion.movimientos_zombies,
        _estado_rng=copy.deepcopy(rng.getstate()),
    )
    return decisiones, tuple(evento.id for evento in ahora)


def resolver_turno_versionado(
    snapshot: SnapshotMundo,
    grafo: Grafo,
    *,
    version_esperada: int,
    intenciones: tuple[IntencionMovimiento, ...] = (),
) -> tuple[SnapshotMundo, ResultadoTurno]:
    """Resuelve las órdenes sobre el snapshot zombie sin volver a moverlos."""

    if snapshot.version != version_esperada:
        raise ValueError("La versión esperada ya no coincide con el snapshot actual.")
    if snapshot.partida.estado is not EstadoPartida.ACTIVA or snapshot.partida.fase is not FaseTurno.DECISIONES:
        raise ValueError("Solo se resuelve un snapshot activo en fase de decisiones.")
    if snapshot._estado_rng is None:
        raise ValueError("El snapshot no tiene estado aleatorio privado para continuar.")
    resultado = resolver_decisiones(
        snapshot.partida,
        grafo,
        intenciones,
        movimientos_zombies=snapshot.movimientos_zombies,
        aristas_cerradas=snapshot.aristas_cerradas,
        segmentos_cerrados=snapshot.segmentos_cerrados,
    )
    resuelto = SnapshotMundo(
        partida=resultado.partida,
        version=snapshot.version + 1,
        aristas_cerradas=snapshot.aristas_cerradas,
        segmentos_cerrados=snapshot.segmentos_cerrados,
        eventos_programados=snapshot.eventos_programados,
        eventos_aplicados=snapshot.eventos_aplicados,
        movimientos_zombies=snapshot.movimientos_zombies,
        _estado_rng=copy.deepcopy(snapshot._estado_rng),
    )
    return resuelto, resultado


def abrir_siguiente_turno(snapshot: SnapshotMundo, *, version_esperada: int) -> SnapshotMundo:
    """Avanza el contador solo desde un resultado completo y vigente."""

    if snapshot.version != version_esperada:
        raise ValueError("La versión esperada ya no coincide con el snapshot actual.")
    partida = snapshot.partida
    if partida.estado is not EstadoPartida.ACTIVA or partida.fase is not FaseTurno.RESUELTA:
        raise ValueError("El siguiente turno solo se abre tras resolver el turno actual.")
    return replace(
        snapshot,
        partida=replace(partida, turno=partida.turno + 1, fase=FaseTurno.PREPARACION),
        version=snapshot.version + 1,
        movimientos_zombies=(),
    )


def _validar_eventos(
    eventos: tuple[EventoCierre, ...],
    grafo: Grafo,
    turno: int,
    aplicados: frozenset[str] = frozenset(),
) -> None:
    ids: set[str] = set()
    calles = {calle.id for calle in grafo.mapa.calles}
    segmentos = {calle.segmento_id for calle in grafo.mapa.calles}
    for evento in eventos:
        if evento.id in ids:
            raise ValueError(f"ID de evento duplicado: {evento.id}.")
        ids.add(evento.id)
        if not evento.aristas <= calles:
            raise ValueError(f"El evento {evento.id} referencia una arista desconocida.")
        if not evento.segmentos <= segmentos:
            raise ValueError(f"El evento {evento.id} referencia un segmento desconocido.")
        if evento.turno_objetivo < turno and evento.id not in aplicados:
            raise ValueError(f"El evento {evento.id} está programado en un turno pasado.")
