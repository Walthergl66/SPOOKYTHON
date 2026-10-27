"""Repositorio local de sesiones de juego; no ofrece persistencia entre procesos."""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import replace
from threading import RLock
from typing import Callable

from navira.application.juego import EstadoSesion, SesionJugador


class RepositorioSesionesMemoria:
    """Almacena hash de token con expiración inactiva; solo proceso local."""

    def __init__(
        self,
        inactividad_segundos: float = 1800.0,
        reloj_monotonico: Callable[[], float] = time.monotonic,
    ) -> None:
        if not math.isfinite(inactividad_segundos) or inactividad_segundos <= 0:
            raise ValueError("La expiración por inactividad debe ser finita y positiva.")
        self._inactividad_segundos = inactividad_segundos
        self._reloj_monotonico = reloj_monotonico
        self._sesiones: dict[str, SesionJugador] = {}
        self._propietario_por_run: dict[str, str] = {}
        self._run_por_token: dict[str, str] = {}
        self._ultima_actividad: dict[str, float] = {}
        self._expiradas: set[str] = set()
        self._lock = RLock()

    def reservar(self, token: str, run_id: str, sobreviviente_id: str) -> bool:
        huella = _huella(token)
        with self._lock:
            if huella in self._expiradas:
                return False
            existente = self._sesiones.get(huella)
            if existente is not None:
                return existente.run_id == run_id
            propietario = self._propietario_por_run.get(run_id)
            if propietario is not None:
                return False
            self._sesiones[huella] = SesionJugador(
                run_id, sobreviviente_id, EstadoSesion.ESPERANDO_APARICION
            )
            self._propietario_por_run[run_id] = huella
            self._run_por_token[huella] = run_id
            self._ultima_actividad[huella] = self._reloj_monotonico()
            return True

    def obtener(self, token: str) -> SesionJugador | None:
        with self._lock:
            huella = _huella(token)
            ahora = self._reloj_monotonico()
            sesion = self._vigente(huella, ahora)
            if sesion is not None:
                self._ultima_actividad[huella] = ahora
            return sesion

    def expirada(self, token: str) -> bool:
        with self._lock:
            huella = _huella(token)
            self._vigente(huella, self._reloj_monotonico())
            return huella in self._expiradas

    def pendiente(self, run_id: str) -> SesionJugador | None:
        with self._lock:
            huella = self._propietario_por_run.get(run_id)
            sesion = self._vigente(huella, self._reloj_monotonico()) if huella is not None else None
            return sesion if sesion and sesion.estado is EstadoSesion.ESPERANDO_APARICION else None

    def activar(self, token: str, nodo: str) -> bool:
        huella = _huella(token)
        with self._lock:
            ahora = self._reloj_monotonico()
            actual = self._vigente(huella, ahora)
            if actual is None:
                return False
            if actual.estado is EstadoSesion.ACTIVO:
                return actual.nodo == nodo
            self._sesiones[huella] = replace(actual, estado=EstadoSesion.ACTIVO, nodo=nodo)
            self._ultima_actividad[huella] = ahora
            return True

    def activar_pendiente(self, run_id: str, sobreviviente_id: str, nodo: str) -> bool:
        with self._lock:
            huella = self._propietario_por_run.get(run_id)
            actual = self._vigente(huella, self._reloj_monotonico()) if huella is not None else None
            if actual is None or actual.sobreviviente_id != sobreviviente_id:
                return False
            if actual.estado is EstadoSesion.ACTIVO:
                return actual.nodo == nodo
            self._sesiones[huella] = replace(actual, estado=EstadoSesion.ACTIVO, nodo=nodo)
            return True

    def liberar(self, token: str) -> None:
        huella = _huella(token)
        with self._lock:
            sesion = self._sesiones.pop(huella, None)
            run_id = sesion.run_id if sesion is not None else self._run_por_token.get(huella)
            self._ultima_actividad.pop(huella, None)
            self._expiradas.discard(huella)
            self._run_por_token.pop(huella, None)
            if run_id is not None and self._propietario_por_run.get(run_id) == huella:
                del self._propietario_por_run[run_id]

    def _vigente(self, huella: str, ahora: float) -> SesionJugador | None:
        """Expira por reloj monotónico y conserva la reserva del run como tombstone."""

        sesion = self._sesiones.get(huella)
        ultima = self._ultima_actividad.get(huella)
        if sesion is not None and ultima is not None and ahora - ultima >= self._inactividad_segundos:
            self._sesiones.pop(huella, None)
            self._ultima_actividad.pop(huella, None)
            self._expiradas.add(huella)
            return None
        return sesion


def _huella(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
