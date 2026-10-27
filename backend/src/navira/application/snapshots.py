"""Casos de uso y puerto para transiciones condicionales de snapshots."""

from __future__ import annotations

from typing import Mapping, Protocol

from navira.domain.mapa import Grafo
from navira.domain.modelo import IntencionMovimiento
from navira.domain.snapshot import SnapshotMundo
from navira.domain.snapshot import CompromisoRuta
from navira.simulation.coordinador import (
    abrir_siguiente_turno,
    preparar_turno_versionado,
    resolver_turno_versionado,
)
from navira.simulation.resolver import ConfiguracionReglas, ResultadoTurno


class SnapshotObsoleto(RuntimeError):
    """Otra operación confirmó primero una transición desde esta versión."""


class RepositorioSnapshots(Protocol):
    """Puerto mínimo para leer y guardar una transición con compare-and-swap."""

    def obtener(self, run_id: str) -> SnapshotMundo | None:
        """Devuelve el snapshot completo actual o `None` si la partida no existe."""

    def obtener_activa(self) -> SnapshotMundo | None:
        """Devuelve la única partida activa; falla si la invariancia se rompe."""

    def insertar_inicial(self, snapshot: SnapshotMundo) -> bool:
        """Inserta una partida nueva solo si el `run_id` todavía no existe."""

    def guardar_si_version(
        self, run_id: str, version_esperada: int, siguiente: SnapshotMundo
    ) -> bool:
        """Confirma un snapshot completo si el estado actual conserva la versión."""


def preparar_turno_persistido(
    repositorio: RepositorioSnapshots,
    grafo: Grafo,
    run_id: str,
    *,
    version_esperada: int,
    configuracion: ConfiguracionReglas = ConfiguracionReglas(),
) -> SnapshotMundo:
    """Aplica cierres/movimiento zombie y confirma fase de decisiones con CAS."""

    actual = _leer_version(repositorio, run_id, version_esperada)
    decisiones, _ = preparar_turno_versionado(
        actual,
        grafo,
        version_esperada=version_esperada,
        configuracion=configuracion,
    )
    _confirmar(repositorio, run_id, version_esperada, decisiones)
    return decisiones


def resolver_turno_persistido(
    repositorio: RepositorioSnapshots,
    grafo: Grafo,
    run_id: str,
    *,
    version_esperada: int,
    intenciones: tuple[IntencionMovimiento, ...] = (),
    rutas_propuestas: Mapping[str, CompromisoRuta | None] | None = None,
) -> tuple[SnapshotMundo, ResultadoTurno]:
    """Confirma conjuntamente el resultado sobre el snapshot de decisiones."""

    actual = _leer_version(repositorio, run_id, version_esperada)
    resuelto, resultado = resolver_turno_versionado(
        actual,
        grafo,
        version_esperada=version_esperada,
        intenciones=intenciones,
        rutas_propuestas=rutas_propuestas,
    )
    _confirmar(repositorio, run_id, version_esperada, resuelto)
    return resuelto, resultado


def abrir_siguiente_turno_persistido(
    repositorio: RepositorioSnapshots,
    run_id: str,
    *,
    version_esperada: int,
) -> SnapshotMundo:
    """Avanza turno/fase solo después de confirmar el resultado actual."""

    actual = _leer_version(repositorio, run_id, version_esperada)
    siguiente = abrir_siguiente_turno(actual, version_esperada=version_esperada)
    _confirmar(repositorio, run_id, version_esperada, siguiente)
    return siguiente


def _leer_version(
    repositorio: RepositorioSnapshots, run_id: str, version_esperada: int
) -> SnapshotMundo:
    actual = repositorio.obtener(run_id)
    if actual is None:
        raise KeyError(f"No existe una partida con run_id {run_id}.")
    if actual.version != version_esperada:
        raise SnapshotObsoleto("El snapshot vigente cambió antes de iniciar la transición.")
    return actual


def _confirmar(
    repositorio: RepositorioSnapshots,
    run_id: str,
    version_esperada: int,
    siguiente: SnapshotMundo,
) -> None:
    if not repositorio.guardar_si_version(run_id, version_esperada, siguiente):
        raise SnapshotObsoleto("Otra transición confirmó primero esta versión.")
