"""Snapshot inmutable del mundo y valores asociados (sin dependencias de capas externas)."""

from __future__ import annotations

from dataclasses import dataclass, field

from navira.domain.mapa import Calle
from navira.domain.modelo import EstadoSobreviviente, FaseTurno, Partida

EstadoAleatorio = tuple[int, tuple[int, ...], float | None]


@dataclass(frozen=True, slots=True)
class MovimientoZombie:
    zombie_id: str
    origen: str
    destino: str
    tramos: tuple[Calle, ...]


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
    """Estado privado, íntegro e identificado por partida/fase/versión.

    `mordidos_ultimo_turno` conserva las personas mordidas por la resolución
    más reciente; el acumulado se obtiene de los estados terminales de partida.
    """

    partida: Partida
    version: int
    aristas_cerradas: frozenset[str] = frozenset()
    segmentos_cerrados: frozenset[str] = frozenset()
    eventos_programados: tuple[EventoCierre, ...] = ()
    eventos_aplicados: tuple[str, ...] = ()
    movimientos_zombies: tuple[MovimientoZombie, ...] = ()
    mordidos_ultimo_turno: tuple[str, ...] = ()
    _estado_rng: EstadoAleatorio | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.version < 0:
            raise ValueError("La versión del snapshot no puede ser negativa.")
        object.__setattr__(self, "aristas_cerradas", frozenset(self.aristas_cerradas))
        object.__setattr__(self, "segmentos_cerrados", frozenset(self.segmentos_cerrados))
        object.__setattr__(self, "eventos_programados", tuple(self.eventos_programados))
        object.__setattr__(self, "eventos_aplicados", tuple(self.eventos_aplicados))
        object.__setattr__(self, "movimientos_zombies", tuple(self.movimientos_zombies))
        object.__setattr__(self, "mordidos_ultimo_turno", tuple(self.mordidos_ultimo_turno))
        if len(self.eventos_aplicados) != len(set(self.eventos_aplicados)):
            raise ValueError("Un evento no puede figurar aplicado dos veces.")
        ids = [evento.id for evento in self.eventos_programados]
        if len(ids) != len(set(ids)):
            raise ValueError("Los eventos programados deben tener IDs únicos.")
        if not set(self.eventos_aplicados) <= set(ids):
            raise ValueError("El snapshot referencia un evento aplicado que no está programado.")
        if len(self.mordidos_ultimo_turno) != len(set(self.mordidos_ultimo_turno)):
            raise ValueError("Un sobreviviente no puede contarse dos veces en la misma resolución.")
        sobrevivientes = {item.id for item in self.partida.sobrevivientes}
        if not set(self.mordidos_ultimo_turno) <= sobrevivientes:
            raise ValueError("El snapshot registra una mordida para un sobreviviente desconocido.")
        estados_sobrevivientes = {
            item.id: item.estado for item in self.partida.sobrevivientes
        }
        if any(
            estados_sobrevivientes[item] is not EstadoSobreviviente.MORDIDO
            for item in self.mordidos_ultimo_turno
        ):
            raise ValueError("La última resolución solo puede registrar sobrevivientes mordidos.")

    @property
    def identidad(self) -> tuple[str, int, FaseTurno, str, int]:
        """Clave de snapshot; la versión crece también entre fases del turno."""

        partida = self.partida
        return (partida.run_id, partida.turno, partida.fase, partida.map_version, self.version)
