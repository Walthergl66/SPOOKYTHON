"""Sesión propietaria y aparición inicial del modo de juego humano."""

from __future__ import annotations

import copy
import random
import secrets
import uuid
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Callable, Protocol

from navira.application.decidir_paso import ProveedorMapas, peligros_visibles
from navira.application.snapshots import RepositorioSnapshots
from navira.domain.modelo import (
    ControlSobreviviente,
    EstadoPartida,
    EstadoSobreviviente,
    EstadoZombie,
    FaseTurno,
    ModoPartida,
    Sobreviviente,
)
from navira.routing.dijkstra import seleccionar_refugio
from navira.domain.snapshot import SnapshotMundo


class EstadoSesion(StrEnum):
    ESPERANDO_APARICION = "esperando_aparicion"
    ACTIVO = "activo"


@dataclass(frozen=True, slots=True)
class SesionJugador:
    """Propiedad efímera de un solo personaje en una partida."""

    run_id: str
    sobreviviente_id: str
    estado: EstadoSesion
    nodo: str | None = None


class RepositorioSesiones(Protocol):
    def reservar(self, token: str, run_id: str, sobreviviente_id: str) -> bool: ...
    def obtener(self, token: str) -> SesionJugador | None: ...
    def expirada(self, token: str) -> bool: ...
    def pendiente(self, run_id: str) -> SesionJugador | None: ...
    def activar(self, token: str, nodo: str) -> bool: ...
    def activar_pendiente(self, run_id: str, sobreviviente_id: str, nodo: str) -> bool: ...
    def liberar(self, token: str) -> None: ...


class JuegoNoDisponible(RuntimeError):
    """No hay una partida activa de juego o su snapshot no se puede usar."""


class AparicionNoDisponible(RuntimeError):
    """El mapa/estado vigente no contiene un nodo de aparición elegible."""


class PropietarioOcupado(RuntimeError):
    """La partida ya tiene una sesión propietaria humana."""


@dataclass(frozen=True, slots=True)
class ResultadoUnirse:
    token: str
    sesion: SesionJugador


@dataclass(frozen=True, slots=True)
class OrdenSesionActual:
    """Campos mínimos de una orden recibida que se pueden mostrar al dueño."""

    accion_id: str
    turno: int
    siguiente_nodo: str
    secuencia: int


class OrdenRecuperable(Protocol):
    accion_id: str
    turno: int
    siguiente_nodo: str
    secuencia: int


class ProveedorUltimaOrden(Protocol):
    def obtener_ultima(self, run_id: str, personaje_id: str) -> OrdenRecuperable | None: ...


class SesionNoEncontrada(PermissionError):
    """La cookie no identifica una sesión de jugador recuperable."""


class SesionExpirada(PermissionError):
    """La sesión venció y su reserva de personaje no se puede transferir."""


@dataclass(frozen=True, slots=True)
class EstadoSesionActual:
    """Estado privado mínimo para restaurar la vista de la persona propietaria."""

    sesion: SesionJugador
    nodo: str | None
    estado_personaje: str | None
    ultima_orden: OrdenSesionActual | None


@dataclass(frozen=True, slots=True)
class ConsultarSesionJuego:
    """Recupera exclusivamente el personaje asociado a una cookie existente."""

    snapshots: RepositorioSnapshots
    sesiones: RepositorioSesiones
    ordenes: ProveedorUltimaOrden

    def ejecutar(self, token: str | None) -> EstadoSesionActual:
        if not token:
            raise SesionNoEncontrada("Se requiere la sesión propietaria.")
        sesion = self.sesiones.obtener(token)
        if sesion is None:
            if self.sesiones.expirada(token):
                raise SesionExpirada("La sesión venció por inactividad y no puede tomar otro personaje.")
            raise SesionNoEncontrada("La sesión de juego no existe o ya no está disponible.")
        snapshot = self.snapshots.obtener(sesion.run_id)
        if snapshot is None or snapshot.partida.modo is not ModoPartida.JUEGO:
            raise JuegoNoDisponible("La partida de esta sesión ya no está disponible.")
        personaje = next(
            (item for item in snapshot.partida.sobrevivientes if item.id == sesion.sobreviviente_id),
            None,
        )
        if personaje is None and sesion.estado is EstadoSesion.ACTIVO:
            raise JuegoNoDisponible("No se pudo recuperar el personaje de la sesión.")
        ultima = self.ordenes.obtener_ultima(sesion.run_id, sesion.sobreviviente_id)
        orden = (
            OrdenSesionActual(
                accion_id=ultima.accion_id,
                turno=ultima.turno,
                siguiente_nodo=ultima.siguiente_nodo,
                secuencia=ultima.secuencia,
            )
            if ultima is not None
            else None
        )
        return EstadoSesionActual(
            sesion=sesion,
            nodo=personaje.nodo if personaje is not None else None,
            estado_personaje=personaje.estado.value if personaje is not None else None,
            ultima_orden=orden,
        )


@dataclass(frozen=True, slots=True)
class UnirseAJuego:
    """Abre o recupera la única sesión humana y solicita una aparición válida.

    Si el turno ya superó PREPARACION, se reserva el cupo como pendiente; el
    coordinador de juego debe llamar `incorporar_aparicion_pendiente()` antes
    del movimiento zombie del siguiente turno.
    """

    snapshots: RepositorioSnapshots
    mapas: ProveedorMapas
    sesiones: RepositorioSesiones
    generar_id_jugador: Callable[[], str] = lambda: f"J-{uuid.uuid4().hex[:12]}"

    def ejecutar(self, token_actual: str | None = None) -> ResultadoUnirse:
        snapshot = self._snapshot_juego()
        if token_actual:
            sesion = self.sesiones.obtener(token_actual)
            if sesion is not None:
                if sesion.run_id != snapshot.partida.run_id:
                    raise PropietarioOcupado("La sesión pertenece a otra partida.")
                if sesion.estado is EstadoSesion.ESPERANDO_APARICION:
                    personaje = next(
                        (
                            item
                            for item in snapshot.partida.sobrevivientes
                            if item.id == sesion.sobreviviente_id
                        ),
                        None,
                    )
                    if personaje is not None:
                        self.sesiones.activar(token_actual, personaje.nodo)
                        sesion = self.sesiones.obtener(token_actual) or sesion
                return ResultadoUnirse(token_actual, sesion)
            if self.sesiones.expirada(token_actual):
                raise SesionExpirada("La sesión venció; no se puede crear otro personaje en esta partida.")

        token = secrets.token_urlsafe(32)
        sobreviviente_id = self.generar_id_jugador()
        if not self.sesiones.reservar(token, snapshot.partida.run_id, sobreviviente_id):
            raise PropietarioOcupado("La partida ya tiene un jugador propietario.")
        if snapshot.partida.fase is FaseTurno.PREPARACION:
            try:
                actualizado, nodo = self._incorporar(snapshot, sobreviviente_id)
            except Exception:
                self.sesiones.liberar(token)
                raise
            if not self.snapshots.guardar_si_version(
                snapshot.partida.run_id, snapshot.version, actualizado
            ):
                self.sesiones.liberar(token)
                raise JuegoNoDisponible("El estado cambió mientras se registraba la aparición.")
            if not self.sesiones.activar(token, nodo):
                raise JuegoNoDisponible("No se pudo confirmar la propiedad de la aparición.")
        sesion = self.sesiones.obtener(token)
        if sesion is None:
            raise JuegoNoDisponible("No se pudo guardar la sesión.")
        return ResultadoUnirse(token, sesion)

    def incorporar_aparicion_pendiente(self, run_id: str, version_esperada: int) -> SnapshotMundo:
        """Inserta una sesión pendiente únicamente antes de mover zombies."""

        sesion = self.sesiones.pendiente(run_id)
        if sesion is None:
            snapshot = self.snapshots.obtener(run_id)
            if snapshot is None:
                raise JuegoNoDisponible("La partida ya no existe.")
            return snapshot
        snapshot = self.snapshots.obtener(run_id)
        if snapshot is None or snapshot.version != version_esperada:
            raise JuegoNoDisponible("El snapshot de la partida cambió.")
        existente = next(
            (item for item in snapshot.partida.sobrevivientes if item.id == sesion.sobreviviente_id),
            None,
        )
        if existente is not None:
            if not self.sesiones.activar_pendiente(run_id, sesion.sobreviviente_id, existente.nodo):
                raise JuegoNoDisponible("No se pudo recuperar la sesión propietaria pendiente.")
            return snapshot
        actualizado, nodo = self._incorporar(snapshot, sesion.sobreviviente_id)
        if not self.snapshots.guardar_si_version(run_id, version_esperada, actualizado):
            raise JuegoNoDisponible("Otra transición confirmó primero el snapshot.")
        if not self.sesiones.activar_pendiente(run_id, sesion.sobreviviente_id, nodo):
            raise JuegoNoDisponible("No se pudo confirmar la sesión tras la aparición.")
        return actualizado

    def _snapshot_juego(self) -> SnapshotMundo:
        try:
            snapshot = self.snapshots.obtener_activa()
        except RuntimeError as error:
            raise JuegoNoDisponible("No hay una única partida activa.") from error
        if (
            snapshot is None
            or snapshot.partida.estado is not EstadoPartida.ACTIVA
            or snapshot.partida.modo is not ModoPartida.JUEGO
        ):
            raise JuegoNoDisponible("No hay una partida activa en modo juego.")
        return snapshot

    def _incorporar(self, snapshot: SnapshotMundo, sobreviviente_id: str) -> tuple[SnapshotMundo, str]:
        partida = snapshot.partida
        if partida.estado is not EstadoPartida.ACTIVA or partida.modo is not ModoPartida.JUEGO:
            raise JuegoNoDisponible("La aparición requiere una partida de juego activa.")
        if partida.fase is not FaseTurno.PREPARACION:
            raise JuegoNoDisponible("La aparición solo puede aplicarse antes del movimiento zombie.")
        grafo = self.mapas.obtener(partida.map_version)
        if grafo is None or snapshot._estado_rng is None:
            raise JuegoNoDisponible("Falta el mapa versionado o el estado aleatorio del servidor.")
        partida.validar_mapa(grafo.mapa)
        nodos_bloqueados, aristas_peligrosas = peligros_visibles(snapshot, grafo)
        cerradas = snapshot.aristas_cerradas | aristas_peligrosas
        refugios = {refugio.nodo for refugio in grafo.mapa.refugios}
        ocupados = {item.nodo for item in partida.sobrevivientes}
        zombies_visibles = {
            item.nodo for item in partida.zombies if item.estado is EstadoZombie.ACTIVO
        }
        candidatos = []
        for nodo in sorted(grafo.mapa.nodos_por_id):
            if nodo in refugios or nodo in ocupados or nodo in zombies_visibles or nodo in nodos_bloqueados:
                continue
            if seleccionar_refugio(
                grafo,
                nodo,
                aristas_cerradas=cerradas,
                segmentos_cerrados=snapshot.segmentos_cerrados,
                nodos_bloqueados=frozenset(nodos_bloqueados),
            ) is not None:
                candidatos.append(nodo)
        if not candidatos:
            raise AparicionNoDisponible("No hay nodos elegibles con ruta vigente a un refugio.")
        rng = random.Random()
        rng.setstate(copy.deepcopy(snapshot._estado_rng))
        nodo = rng.choice(candidatos)
        nuevo_personaje = Sobreviviente(
            sobreviviente_id,
            nodo,
            control=ControlSobreviviente.HUMANO,
            estado=EstadoSobreviviente.ACTIVO,
        )
        actualizado = replace(
            snapshot,
            partida=replace(partida, sobrevivientes=partida.sobrevivientes + (nuevo_personaje,)),
            version=snapshot.version + 1,
            _estado_rng=copy.deepcopy(rng.getstate()),
        )
        return actualizado, nodo
