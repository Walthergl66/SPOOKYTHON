"""Cálculo de plazo absoluto de un turno usando reloj monotónico."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VentanaTurno:
    """Límite temporal calculable sin dormir ni depender del reloj civil."""

    inicio_monotonic_s: float
    duracion_s: float = 2.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.inicio_monotonic_s) or self.inicio_monotonic_s < 0:
            raise ValueError("El inicio monotónico no puede ser negativo.")
        if not math.isfinite(self.duracion_s) or self.duracion_s <= 0:
            raise ValueError("La duración del turno debe ser positiva.")

    @property
    def deadline_monotonic_s(self) -> float:
        """Plazo absoluto; el procesamiento consume parte de la duración."""

        return self.inicio_monotonic_s + self.duracion_s

    def restante_s(self, ahora_monotonic_s: float) -> float:
        """Tiempo restante no negativo para esperar órdenes o decidir timeout."""

        if not math.isfinite(ahora_monotonic_s) or ahora_monotonic_s < 0:
            raise ValueError("La lectura monotónica debe ser finita y no negativa.")
        return max(0.0, self.deadline_monotonic_s - ahora_monotonic_s)

    def retraso_s(self, ahora_monotonic_s: float) -> float:
        """Retraso sobre el plazo absoluto, útil para medir el ciclo real."""

        if not math.isfinite(ahora_monotonic_s) or ahora_monotonic_s < 0:
            raise ValueError("La lectura monotónica debe ser finita y no negativa.")
        return max(0.0, ahora_monotonic_s - self.deadline_monotonic_s)
