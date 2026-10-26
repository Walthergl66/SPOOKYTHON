"""Puerta monotónica compartida entre el registro y el cierre de un turno."""

from __future__ import annotations

import math
from threading import RLock
from time import monotonic
from typing import Callable


class PuertaDecisiones:
    """Serializa órdenes/cierre y limita cada ventana a run y turno exactos.

    La instancia se comparte entre `RegistrarOrdenHumana` y
    `CoordinadorJuego`. Es una garantía local de proceso; el adaptador CAS
    sigue siendo necesario y también debe ser atómico en el almacenamiento.
    """

    def __init__(self, reloj: Callable[[], float] = monotonic) -> None:
        self._reloj = reloj
        self.lock = RLock()
        self._identidad: tuple[str, int] | None = None
        self._deadline: float | None = None

    def abrir(self, run_id: str, turno: int, *, deadline_monotonic_s: float) -> None:
        """Publica un único deadline monotónico bajo el lock compartido."""

        if (
            not run_id
            or turno < 0
            or not math.isfinite(deadline_monotonic_s)
            or deadline_monotonic_s < 0
        ):
            raise ValueError("La ventana requiere partida, turno y deadline válidos.")
        with self.lock:
            self._identidad = (run_id, turno)
            self._deadline = deadline_monotonic_s

    def acepta(self, run_id: str, turno: int) -> bool:
        """Solo acepta una orden nueva antes del deadline del mismo turno."""

        with self.lock:
            return (
                self._identidad == (run_id, turno)
                and self._deadline is not None
                and self._reloj() < self._deadline
            )

    def cerrar_si_vencida(self, run_id: str, turno: int) -> bool:
        """Cierra el turno vencido; el orden concurrente queda serializado."""

        with self.lock:
            if self._identidad != (run_id, turno) or self._deadline is None:
                return False
            if self._reloj() < self._deadline:
                return False
            self._identidad = None
            self._deadline = None
            return True

    def deadline(self, run_id: str, turno: int) -> float | None:
        """Expone el instante interno solo al coordinador del reloj."""

        with self.lock:
            if self._identidad != (run_id, turno):
                return None
            return self._deadline

    def ahora(self) -> float:
        """Lee el mismo reloj monotónico usado para ordenar/cerrar."""

        return self._reloj()
