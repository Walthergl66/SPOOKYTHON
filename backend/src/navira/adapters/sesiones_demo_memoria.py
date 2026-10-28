"""Registro efímero de mundos públicos aislados por cookie de navegador."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Callable, Protocol


class ControlDemo(Protocol):
    """Operaciones que necesita el ciclo de vida de una sesión de demo."""

    def cerrar(self) -> None: ...


class LimiteSesionesDemo(Exception):
    """No hay capacidad para admitir otro mundo público temporal."""


@dataclass(slots=True)
class _Sesion:
    token_hash: str
    control: ControlDemo
    ultimo_uso: float


class RegistroSesionesDemoMemoria:
    """Aísla una instancia de control por token y elimina sesiones inactivas.

    El token en claro solo existe en la cookie del navegador. El registro usa
    SHA-256 para que un volcado de memoria no revele directamente credenciales
    de sesión; el proceso único es también el límite de consistencia vigente.
    """

    def __init__(
        self,
        crear_control: Callable[[], ControlDemo],
        *,
        max_sesiones: int = 4,
        inactividad_segundos: float = 10_800,
        reloj: Callable[[], float] = monotonic,
    ) -> None:
        if max_sesiones < 1:
            raise ValueError("El máximo de sesiones debe ser al menos uno.")
        if inactividad_segundos <= 0:
            raise ValueError("El TTL de sesión debe ser positivo.")
        self._crear_control = crear_control
        self._max_sesiones = max_sesiones
        self._ttl = inactividad_segundos
        self._reloj = reloj
        self._sesiones: dict[str, _Sesion] = {}
        self._lock = RLock()

    def obtener_o_crear(self, token: str | None) -> tuple[ControlDemo, str | None]:
        """Renueva una sesión válida o crea una cookie y mundo independientes."""

        ahora = self._reloj()
        with self._lock:
            self._eliminar_vencidas(ahora)
            token_hash = _hash(token) if token else None
            sesion = self._sesiones.get(token_hash) if token_hash else None
            if sesion is not None:
                sesion.ultimo_uso = ahora
                return sesion.control, None
            if len(self._sesiones) >= self._max_sesiones:
                raise LimiteSesionesDemo("La demo está llena temporalmente. Inténtalo de nuevo más tarde.")

            token_nuevo = secrets.token_urlsafe(32)
            hash_nuevo = _hash(token_nuevo)
            control = self._crear_control()
            self._sesiones[hash_nuevo] = _Sesion(hash_nuevo, control, ahora)
            return control, token_nuevo

    def obtener_existente(self, token: str | None) -> ControlDemo | None:
        """Obtiene y renueva solo la sesión que presenta una cookie vigente."""

        if not token:
            return None
        ahora = self._reloj()
        with self._lock:
            self._eliminar_vencidas(ahora)
            sesion = self._sesiones.get(_hash(token))
            if sesion is None:
                return None
            sesion.ultimo_uso = ahora
            return sesion.control

    def cerrar(self) -> None:
        """Detiene los relojes y libera todos los controles al cerrar el proceso."""

        with self._lock:
            sesiones = tuple(self._sesiones.values())
            self._sesiones.clear()
        for sesion in sesiones:
            sesion.control.cerrar()

    def _eliminar_vencidas(self, ahora: float) -> None:
        vencidas = [
            clave
            for clave, sesion in self._sesiones.items()
            if ahora - sesion.ultimo_uso >= self._ttl
        ]
        for clave in vencidas:
            sesion = self._sesiones.pop(clave)
            sesion.control.cerrar()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
