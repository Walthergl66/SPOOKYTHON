"""Adaptador atómico en proceso para pruebas y ejecuciones locales.

No es persistencia durable ni coordina varios procesos/hosts. La implementación
productiva deberá cumplir el mismo puerto usando una escritura condicional.
"""

from __future__ import annotations

from threading import RLock

from navira.domain.modelo import EstadoPartida, FaseTurno
from navira.simulation.coordinador import SnapshotMundo


class AlmacenSnapshotsMemoria:
    """Repositorio de un escritor local con compare-and-swap bajo un lock."""

    def __init__(self) -> None:
        self._por_run: dict[str, SnapshotMundo] = {}
        self._lock = RLock()

    def obtener(self, run_id: str) -> SnapshotMundo | None:
        """Lee una referencia inmutable bajo el mismo lock de escrituras."""

        with self._lock:
            return self._por_run.get(run_id)

    def obtener_activa(self) -> SnapshotMundo | None:
        """Lee la partida activa única definida por el alcance inicial."""

        with self._lock:
            activas = tuple(
                snapshot
                for snapshot in self._por_run.values()
                if snapshot.partida.estado is EstadoPartida.ACTIVA
            )
            if len(activas) > 1:
                raise RuntimeError("Hay más de una partida activa en el repositorio.")
            return activas[0] if activas else None

    def insertar_inicial(self, snapshot: SnapshotMundo) -> bool:
        """Añade una única partida nueva en versión cero/preparación."""

        partida = snapshot.partida
        if snapshot.version != 0 or partida.turno != 0 or partida.fase is not FaseTurno.PREPARACION:
            raise ValueError("El snapshot inicial debe ser versión cero en preparación.")
        with self._lock:
            if partida.run_id in self._por_run:
                return False
            self._por_run[partida.run_id] = snapshot
            return True

    def guardar_si_version(
        self, run_id: str, version_esperada: int, siguiente: SnapshotMundo
    ) -> bool:
        """Reemplaza el snapshot completo una sola vez desde la versión esperada."""

        if siguiente.partida.run_id != run_id or siguiente.version != version_esperada + 1:
            raise ValueError("La nueva versión debe pertenecer al run y avanzar exactamente una vez.")
        with self._lock:
            actual = self._por_run.get(run_id)
            if actual is None or actual.version != version_esperada:
                return False
            self._por_run[run_id] = siguiente
            return True
