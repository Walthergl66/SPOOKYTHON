"""Runner local de rondas automáticas para la demo del panel."""

from __future__ import annotations

import logging
import math
from threading import Event, Thread
from time import monotonic

from navira.application.simulacion_automatica import EjecutarRondaAutomatica
from navira.application.snapshots import RepositorioSnapshots
from navira.domain.modelo import EstadoPartida, EstadoSobreviviente

_LOG = logging.getLogger(__name__)


class RelojSimuladorLocal:
    """Impulsa rondas automáticas en un único proceso de desarrollo.

    El periodo se mide desde el inicio de cada ciclo. Pausar evita abrir una
    ronda nueva; el estado confirmado de la ronda en curso no se revierte.
    """

    def __init__(
        self,
        run_id: str,
        snapshots: RepositorioSnapshots,
        ejecutar_ronda: EjecutarRondaAutomatica,
        *,
        periodo_s: float = 2.0,
    ) -> None:
        if not math.isfinite(periodo_s) or periodo_s <= 0:
            raise ValueError("El período del reloj debe ser positivo y finito.")
        self._run_id = run_id
        self._snapshots = snapshots
        self._ejecutar_ronda = ejecutar_ronda
        self._periodo_s = periodo_s
        self._detener = Event()
        self._pausado = Event()
        self._hilo: Thread | None = None
        self._error: str | None = None

    def iniciar(self) -> None:
        """Inicia el hilo una sola vez para esta partida."""

        if self._hilo is not None and self._hilo.is_alive():
            return
        self._detener.clear()
        self._hilo = Thread(target=self._ejecutar, name="navira-simulator-clock", daemon=True)
        self._hilo.start()

    def pausar(self) -> None:
        """Evita el inicio de nuevos turnos."""

        self._pausado.set()

    def reanudar(self) -> None:
        """Permite que el siguiente turno automático continúe."""

        self._pausado.clear()

    def detener(self, timeout_s: float = 3.0) -> None:
        """Solicita cierre ordenado y espera un intervalo acotado."""

        self._detener.set()
        if self._hilo is not None:
            self._hilo.join(timeout=max(0.0, timeout_s))

    @property
    def pausado(self) -> bool:
        return self._pausado.is_set()

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def ejecutandose(self) -> bool:
        return self._hilo is not None and self._hilo.is_alive()

    def _ejecutar(self) -> None:
        siguiente_inicio = monotonic()
        while not self._detener.is_set():
            if self._pausado.is_set():
                self._detener.wait(0.05)
                siguiente_inicio = monotonic()
                continue
            ahora = monotonic()
            if ahora < siguiente_inicio and self._detener.wait(siguiente_inicio - ahora):
                return
            if self._pausado.is_set():
                continue
            snapshot = self._snapshots.obtener(self._run_id)
            if snapshot is None or snapshot.partida.estado is not EstadoPartida.ACTIVA:
                return
            if not any(
                item.estado is EstadoSobreviviente.ACTIVO
                for item in snapshot.partida.sobrevivientes
            ):
                return
            try:
                self._ejecutar_ronda.ejecutar(
                    self._run_id,
                    version_esperada=snapshot.version,
                )
            except Exception as error:
                self._error = str(error)
                _LOG.exception("Se detuvo el simulador local para run %s", self._run_id)
                return
            siguiente_inicio = monotonic() + self._periodo_s
