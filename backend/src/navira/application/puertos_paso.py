"""Errores y puertos del caso de uso de decisión de paso."""

from __future__ import annotations

from typing import Protocol

from navira.domain.mapa import Grafo
from navira.domain.snapshot import SnapshotMundo


class PartidaNoDisponible(RuntimeError):
    """No existe un snapshot/mapa de partida vigente y usable."""


class PasoIncompatible(RuntimeError):
    """Turno, fase, personaje o posición no coinciden con el mundo vigente."""


class EntidadNoEncontrada(LookupError):
    """El personaje indicado no existe en la partida activa."""


class ProveedorSnapshotsActivos(Protocol):
    def obtener_activa(self) -> SnapshotMundo | None:
        """Devuelve la única partida activa o nada si no hay partida."""


class ProveedorMapas(Protocol):
    def obtener(self, version: str) -> Grafo | None:
        """Busca un grafo validado por su versión inmutable."""
