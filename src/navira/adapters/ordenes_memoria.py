"""Repositorio local de órdenes; no ofrece persistencia entre procesos."""

from __future__ import annotations

from threading import RLock

from navira.application.ordenes import (
    OrdenHumana,
    OrdenIdempotenciaConflict,
    RepositorioOrdenes,
)


class RepositorioOrdenesMemoria(RepositorioOrdenes):
    """Serializa idempotencia y reemplazo dentro de un solo proceso."""

    def __init__(self) -> None:
        self._por_accion: dict[tuple[str, str, str], OrdenHumana] = {}
        self._ultima_por_personaje_turno: dict[tuple[str, int, str], OrdenHumana] = {}
        self._secuencia_por_run: dict[str, int] = {}
        self._lock = RLock()

    def buscar_accion(self, run_id: str, personaje_id: str, accion_id: str) -> OrdenHumana | None:
        with self._lock:
            return self._por_accion.get((run_id, personaje_id, accion_id))

    def registrar(self, orden: OrdenHumana) -> OrdenHumana:
        clave_accion = (orden.run_id, orden.personaje_id, orden.accion_id)
        clave_turno = (orden.run_id, orden.turno, orden.personaje_id)
        with self._lock:
            existente = self._por_accion.get(clave_accion)
            if existente is not None:
                if _contenido(existente) != _contenido(orden):
                    raise OrdenIdempotenciaConflict("accionId ya fue usado con otro contenido.")
                return existente
            secuencia = self._secuencia_por_run.get(orden.run_id, 0) + 1
            confirmada = OrdenHumana(
                run_id=orden.run_id,
                turno=orden.turno,
                personaje_id=orden.personaje_id,
                accion_id=orden.accion_id,
                siguiente_nodo=orden.siguiente_nodo,
                secuencia=secuencia,
                version_snapshot=orden.version_snapshot,
            )
            self._secuencia_por_run[orden.run_id] = secuencia
            self._por_accion[clave_accion] = confirmada
            self._ultima_por_personaje_turno[clave_turno] = confirmada
            return confirmada

    def obtener_turno(self, run_id: str, turno: int) -> tuple[OrdenHumana, ...]:
        with self._lock:
            return tuple(
                sorted(
                    (
                        orden
                        for (partida, numero, _), orden in self._ultima_por_personaje_turno.items()
                        if partida == run_id and numero == turno
                    ),
                    key=lambda orden: orden.secuencia,
                )
            )


def _contenido(orden: OrdenHumana) -> tuple[str, int, str, str]:
    """Campos funcionales que deben coincidir ante el mismo accionId."""

    return (orden.run_id, orden.turno, orden.personaje_id, orden.siguiente_nodo)
