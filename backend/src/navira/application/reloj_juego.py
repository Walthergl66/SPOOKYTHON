"""Runner local que impulsa una partida humana en cadencia monotónica."""

from __future__ import annotations

import logging
import math
from threading import Event, Thread
from time import monotonic

from navira.application.coordinador_juego import CoordinadorJuego
from navira.application.puerta_decisiones import PuertaDecisiones
from navira.application.snapshots import RepositorioSnapshots
from navira.domain.modelo import EstadoPartida, EstadoSobreviviente

_LOG = logging.getLogger(__name__)


class RelojJuegoLocal:
    """Avanza un juego local con deadline humano y espera por ciclo.

    Es un único proceso/hilo para desarrollo. No garantiza disponibilidad ni
    recuperación ante reinicios; el llamador lo activa explícitamente.
    """

    def __init__(
        self,
        run_id: str,
        snapshots: RepositorioSnapshots,
        coordinador: CoordinadorJuego,
        puerta: PuertaDecisiones,
        *,
        periodo_s: float = 2.0,
    ) -> None:
        if not math.isfinite(periodo_s) or periodo_s <= 0:
            raise ValueError("El período del reloj debe ser positivo y finito.")
        self._run_id = run_id
        self._snapshots = snapshots
        self._coordinador = coordinador
        self._puerta = puerta
        self._periodo_s = periodo_s
        self._detener = Event()
        self._hilo: Thread | None = None

    def iniciar(self) -> None:
        """Arranca el reloj una sola vez; una instancia corresponde a un run."""

        if self._hilo is not None and self._hilo.is_alive():
            return
        self._detener.clear()
        self._hilo = Thread(target=self._ejecutar, name="navira-game-clock", daemon=True)
        self._hilo.start()

    def detener(self, timeout_s: float = 3.0) -> None:
        """Pide cierre ordenado y espera un tiempo acotado al hilo local."""

        self._detener.set()
        if self._hilo is not None:
            self._hilo.join(timeout=max(0.0, timeout_s))

    def _ejecutar(self) -> None:
        siguiente_inicio = monotonic()
        while not self._detener.is_set():
            ahora = monotonic()
            if ahora < siguiente_inicio and self._detener.wait(siguiente_inicio - ahora):
                return
            inicio_turno = monotonic()
            snapshot = self._snapshots.obtener(self._run_id)
            if snapshot is None or snapshot.partida.estado is not EstadoPartida.ACTIVA:
                return
            if not any(
                item.estado is EstadoSobreviviente.ACTIVO
                for item in snapshot.partida.sobrevivientes
            ):
                return
            try:
                decisiones = self._coordinador.preparar(
                    self._run_id,
                    version_esperada=snapshot.version,
                    inicio_turno_monotonic_s=inicio_turno,
                )
                deadline = self._puerta.deadline(
                    self._run_id,
                    decisiones.partida.turno,
                )
                if deadline is None:
                    raise RuntimeError("El coordinador no abrió el deadline del turno.")
                restante = max(0.0, deadline - monotonic())
                if self._detener.wait(restante):
                    return
                self._coordinador.resolver(
                    self._run_id,
                    version_esperada=decisiones.version,
                )
            except Exception:
                _LOG.exception("Se detuvo el reloj local de Navira para run %s", self._run_id)
                return
            siguiente_inicio = inicio_turno + self._periodo_s
