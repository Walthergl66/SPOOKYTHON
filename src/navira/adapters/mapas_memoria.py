"""Catálogo inmutable por versión de mapas ya validados."""

from __future__ import annotations

from threading import RLock

from navira.domain.mapa import Grafo


class CatalogoMapasMemoria:
    """Registro local de grafos; no consulta fuentes externas ni modifica mapas."""

    def __init__(self, mapas: tuple[Grafo, ...] = ()) -> None:
        self._por_version: dict[str, Grafo] = {}
        self._lock = RLock()
        for grafo in mapas:
            self.registrar(grafo)

    def registrar(self, grafo: Grafo) -> None:
        """Añade una versión una sola vez para conservar identidad del mapa."""

        version = grafo.mapa.version
        with self._lock:
            existente = self._por_version.get(version)
            if existente is not None and existente.mapa != grafo.mapa:
                raise ValueError(f"La versión de mapa {version} ya existe con otro contenido.")
            self._por_version[version] = grafo

    def obtener(self, version: str) -> Grafo | None:
        """Recupera el grafo exacto versionado por la partida."""

        with self._lock:
            return self._por_version.get(version)
