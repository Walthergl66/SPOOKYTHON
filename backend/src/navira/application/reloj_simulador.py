"""Runner local de rondas automáticas para la demo del panel."""

from __future__ import annotations

import logging
import math
from threading import Event, RLock, Thread
from time import monotonic

from navira.application.simulacion_automatica import EjecutarRondaAutomatica
from navira.application.snapshots import RepositorioSnapshots
from navira.domain.modelo import EstadoPartida, EstadoSobreviviente

_LOG = logging.getLogger(__name__)
_PAUSA_MINIMA_S = 0.02


def validar_velocidad(velocidad: float) -> float:
    """Factor de aceleración: divide el periodo entre rondas; debe ser positivo y finito."""

    if not math.isfinite(velocidad) or velocidad <= 0:
        raise ValueError("La velocidad del reloj debe ser positiva y finita.")
    return velocidad


class RelojSimuladorLocal:
    """Impulsa rondas automáticas en un único proceso de desarrollo.

    El periodo se mide desde el inicio de cada ciclo y se divide entre la
    velocidad: x4 solo se cumple si cada ronda termina antes del nuevo periodo.
    Pausar evita abrir una ronda nueva; el estado confirmado de la ronda en
    curso no se revierte.
    """

    def __init__(
        self,
        run_id: str,
        snapshots: RepositorioSnapshots,
        ejecutar_ronda: EjecutarRondaAutomatica,
        *,
        periodo_s: float = 2.0,
        velocidad: float = 4.0,
        bloqueo_estado: RLock | None = None,
        continuar_sin_sobrevivientes: bool = False,
    ) -> None:
        if not math.isfinite(periodo_s) or periodo_s <= 0:
            raise ValueError("El período del reloj debe ser positivo y finito.")
        self._run_id = run_id
        self._snapshots = snapshots
        self._ejecutar_ronda = ejecutar_ronda
        self._periodo_s = periodo_s
        self._velocidad = validar_velocidad(velocidad)
        self._bloqueo_estado = bloqueo_estado or RLock()
        self._continuar_sin_sobrevivientes = continuar_sin_sobrevivientes
        self._detener = Event()
        self._pausado = Event()
        # La sección crítica solo protege la transición entre «listo» e
        # «iniciado». El turno se marca antes de adquirir el lock del mundo,
        # de modo que una pausa pueda acusarse sin esperar el cálculo completo.
        self._guardia_inicio = RLock()
        self._ronda_en_curso = Event()
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
        """Evita nuevos turnos; la guardia cierra la carrera con su inicio."""

        with self._guardia_inicio:
            self._pausado.set()

    def reanudar(self) -> None:
        """Permite que el siguiente turno automático continúe."""

        self._pausado.clear()

    def fijar_velocidad(self, velocidad: float) -> None:
        """Cambia el factor en caliente; el siguiente ciclo ya usa el nuevo periodo."""

        self._velocidad = validar_velocidad(velocidad)

    @property
    def velocidad(self) -> float:
        return self._velocidad

    def solicitar_detencion(self) -> None:
        """Evita que comience otro turno y deja terminar el ya iniciado."""
        self._detener.set()

    def detener(self, timeout_s: float | None = 3.0) -> None:
        """Solicita cierre ordenado y espera hasta el límite indicado; None espera el cierre."""

        self.solicitar_detencion()
        if self._hilo is not None:
            if timeout_s is None:
                self._hilo.join()
            else:
                self._hilo.join(timeout=max(0.0, timeout_s))

    @property
    def pausado(self) -> bool:
        return self._pausado.is_set()

    @property
    def ronda_en_curso(self) -> bool:
        """Indica si un turno ya comenzó y debe terminar antes de la pausa efectiva."""

        return self._ronda_en_curso.is_set()

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
            # La ronda queda considerada iniciada de forma atómica respecto
            # a pausar(): después del ACK no se abrirá otra ronda.
            with self._guardia_inicio:
                if self._pausado.is_set():
                    continue
                self._ronda_en_curso.set()
            inicio_ronda = monotonic()
            try:
                # El snapshot y su versión se leen junto con el mismo lock que
                # usa el operador, evitando que un alta entre lectura y CAS.
                with self._bloqueo_estado:
                    snapshot = self._snapshots.obtener(self._run_id)
                    if snapshot is None or snapshot.partida.estado is not EstadoPartida.ACTIVA:
                        return
                    if not self._continuar_sin_sobrevivientes and not any(
                        item.estado is EstadoSobreviviente.ACTIVO
                        for item in snapshot.partida.sobrevivientes
                    ):
                        return
                    self._ejecutar_ronda.ejecutar(
                        self._run_id,
                        version_esperada=snapshot.version,
                    )
            except Exception as error:
                self._error = str(error)
                _LOG.exception("Se detuvo el simulador local para run %s", self._run_id)
                return
            finally:
                self._ronda_en_curso.clear()
            # Cede la CPU entre rondas: si una ronda tarda más que el periodo, sin esta pausa
            # el hilo acapara el GIL y la API responde con retraso.
            if self._detener.wait(_PAUSA_MINIMA_S):
                return
            siguiente_inicio = inicio_ronda + self._periodo_s / self._velocidad
