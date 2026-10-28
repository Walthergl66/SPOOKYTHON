"""Proyecciones públicas de mapa y snapshot para el panel de observación."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from navira.application.decidir_paso import DecidirPaso, EntidadNoEncontrada, nodos_horda_visibles
from navira.application.puerta_decisiones import PuertaDecisiones
from navira.domain.mapa import Grafo
from navira.domain.modelo import EstadoPartida, EstadoSobreviviente, EstadoZombie, FaseTurno, TipoZombie
from navira.domain.snapshot import EventoCierre, SnapshotMundo


class ProveedorSnapshotsPanel(Protocol):
    def obtener_activa(self) -> SnapshotMundo | None:
        """Lee la única partida activa o devuelve nada si no hay partida."""


class ProveedorMapasPanel(Protocol):
    def obtener(self, version: str) -> Grafo | None:
        """Recupera el grafo inmutable que coincide con la versión de partida."""


class PanelNoDisponible(RuntimeError):
    """No existe una versión de mapa observable y consistente con la partida."""


@dataclass(frozen=True, slots=True)
class ConsultarPanel:
    """Proyecta estado confirmado y excluye el mundo privado.

    Solo publica zombies activos y movimientos de esos mismos zombies, cierres
    vigentes y conteos agregados. La semilla y el estado RNG nunca se leen.
    """

    snapshots: ProveedorSnapshotsPanel
    mapas: ProveedorMapasPanel
    planificador: DecidirPaso | None = None
    puerta_decisiones: PuertaDecisiones | None = None

    def version_estado(self) -> tuple[str, int] | None:
        """Lee solo la clave de cambio para que el transporte no reproyecte sin cambios."""

        try:
            snapshot = self.snapshots.obtener_activa()
        except RuntimeError as error:
            raise PanelNoDisponible("Hay más de una partida activa.") from error
        if snapshot is None:
            return None
        return snapshot.partida.run_id, snapshot.version

    def consultar_estado(self) -> dict[str, object]:
        """Devuelve `sin_partida` o una observación de la partida versionada."""

        try:
            snapshot = self.snapshots.obtener_activa()
        except RuntimeError as error:
            raise PanelNoDisponible("Hay más de una partida activa.") from error
        if snapshot is None:
            return {"estado": "sin_partida"}

        partida = snapshot.partida
        grafo = self.mapas.obtener(partida.map_version)
        if grafo is None:
            raise PanelNoDisponible("No está disponible la versión de mapa de la partida.")
        partida.validar_mapa(grafo.mapa)

        zombies_visibles = tuple(
            zombie for zombie in partida.zombies if zombie.estado is EstadoZombie.ACTIVO
        )
        ids_visibles = {zombie.id for zombie in zombies_visibles}
        nodos_horda = nodos_horda_visibles(snapshot, grafo)
        movimientos_visibles = tuple(
            {
                "id": movimiento.zombie_id,
                "trayecto": [movimiento.origen, *(tramo.destino for tramo in movimiento.tramos)],
            }
            for movimiento in snapshot.movimientos_zombies
            if movimiento.zombie_id in ids_visibles
        )
        aristas_cerradas = set(snapshot.aristas_cerradas)
        aristas_cerradas.update(
            calle.id
            for calle in grafo.mapa.calles
            if calle.segmento_id in snapshot.segmentos_cerrados
        )
        supervivientes = tuple(
            {
                "id": personaje.id,
                "nodo": personaje.nodo,
                "estado": personaje.estado.value,
                "control": personaje.control.value,
            }
            for personaje in partida.sobrevivientes
        )
        restante_decision_ms = (
            self.puerta_decisiones.restante_ms(partida.run_id, partida.turno)
            if (
                self.puerta_decisiones is not None
                and partida.modo.value == "juego"
                and partida.fase is FaseTurno.DECISIONES
            )
            else None
        )
        rutas_previstas = tuple(
            {
                "sobrevivienteId": personaje.id,
                "trayecto": list(
                    self.planificador.prever_ruta_en_snapshot(
                        snapshot, personaje.id, grafo
                    )
                ),
            }
            for personaje in partida.sobrevivientes
            if (
                personaje.estado is EstadoSobreviviente.ACTIVO
                and self.planificador is not None
                and partida.fase is FaseTurno.DECISIONES
            )
        )

        return {
            "estado": partida.estado.value,
            "runId": partida.run_id,
            "modo": partida.modo.value,
            "turno": partida.turno,
            "fase": partida.fase.value,
            "decisionRestanteMs": restante_decision_ms,
            "mapVersion": partida.map_version,
            "snapshotVersion": snapshot.version,
            "zombies": tuple(
                {"id": zombie.id, "tipo": zombie.tipo.value, "nodo": zombie.nodo}
                for zombie in zombies_visibles
            ),
            "movimientosZombies": movimientos_visibles,
            "sobrevivientes": supervivientes,
            "rutasPrevistas": rutas_previstas,
            "aristasBloqueadas": tuple(sorted(aristas_cerradas)),
            "segmentosBloqueados": tuple(sorted(snapshot.segmentos_cerrados)),
            "nodosHorda": tuple(sorted(nodos_horda)),
            # Solo se publica el evento después de quedar confirmado como aplicado;
            # el panel no puede anticipar el segmento que cerrará en el futuro.
            "eventosCiudad": tuple(
                proyeccion
                for evento in snapshot.eventos_programados
                if evento.id in snapshot.eventos_aplicados
                for proyeccion in (
                    self._proyectar_evento_ciudad(evento, grafo),
                )
            ),
            "metricas": {
                "sobrevivientesActivos": sum(
                    personaje.estado is EstadoSobreviviente.ACTIVO
                    for personaje in partida.sobrevivientes
                ),
                "mordidos": sum(
                    personaje.estado is EstadoSobreviviente.MORDIDO
                    for personaje in partida.sobrevivientes
                ),
                # Total terminal del mundo y mordidas de la resolución más reciente
                # son medidas distintas; conservar ambas evita inferir del turno.
                "mordidosUltimoTurno": len(snapshot.mordidos_ultimo_turno),
                "evacuados": sum(
                    personaje.estado is EstadoSobreviviente.EVACUADO
                    for personaje in partida.sobrevivientes
                ),
                "zombiesVisibles": len(zombies_visibles),
            },
        }

    def consultar_ruta(self, sobreviviente_id: str) -> dict[str, object]:
        """Calcula una sola ruta para la persona elegida, sobre el snapshot vigente.

        El panel no vuelve a calcular rutas de toda la población en cada fase:
        la selección interactiva pide únicamente el trayecto que necesita.
        """

        try:
            snapshot = self.snapshots.obtener_activa()
        except RuntimeError as error:
            raise PanelNoDisponible("Hay más de una partida activa.") from error
        if snapshot is None or snapshot.partida.estado is not EstadoPartida.ACTIVA:
            raise PanelNoDisponible("No hay una partida activa para consultar rutas.")

        partida = snapshot.partida
        grafo = self.mapas.obtener(partida.map_version)
        if grafo is None:
            raise PanelNoDisponible("No está disponible la versión de mapa de la partida.")
        if self.planificador is None:
            raise PanelNoDisponible("No está disponible el planificador de rutas.")
        partida.validar_mapa(grafo.mapa)
        sobreviviente = next(
            (item for item in partida.sobrevivientes if item.id == sobreviviente_id),
            None,
        )
        if sobreviviente is None or sobreviviente.estado is not EstadoSobreviviente.ACTIVO:
            raise EntidadNoEncontrada("El sobreviviente activo no existe en el snapshot consultado.")

        trayecto = ()
        if partida.modo.value == "simulador" or partida.fase is FaseTurno.DECISIONES:
            trayecto = self.planificador.prever_ruta_en_snapshot(
                snapshot, sobreviviente_id, grafo
            )
        return {
            "runId": partida.run_id,
            "turno": partida.turno,
            "snapshotVersion": snapshot.version,
            "sobrevivienteId": sobreviviente_id,
            "trayecto": list(trayecto),
        }

    @staticmethod
    def _proyectar_evento_ciudad(evento: EventoCierre, grafo: Grafo) -> dict[str, object]:
        """Expose only an applied incident and the midpoint of its closed road."""

        segmento = next(iter(evento.segmentos), None)
        calle = next(
            (
                candidata
                for candidata in grafo.mapa.calles
                if candidata.segmento_id in evento.segmentos
                or candidata.id in evento.aristas
            ),
            None,
        )
        proyeccion: dict[str, object] = {
            "id": evento.id,
            "turno": evento.turno_objetivo,
            "causa": evento.causa,
        }
        if calle is not None:
            origen = grafo.mapa.nodos_por_id[calle.origen]
            destino = grafo.mapa.nodos_por_id[calle.destino]
            proyeccion.update(
                {
                    "segmentoId": calle.segmento_id if segmento is None else segmento,
                    "lat": (origen.lat + destino.lat) / 2,
                    "lng": (origen.lng + destino.lng) / 2,
                }
            )
        return proyeccion

    def consultar_mapa(self) -> dict[str, object]:
        """Proyecta el mapa exacto de la partida activa, sin datos privados."""

        try:
            snapshot = self.snapshots.obtener_activa()
        except RuntimeError as error:
            raise PanelNoDisponible("Hay más de una partida activa.") from error
        if snapshot is None or snapshot.partida.estado is not EstadoPartida.ACTIVA:
            raise PanelNoDisponible("No hay un mapa de partida activo para mostrar.")
        grafo = self.mapas.obtener(snapshot.partida.map_version)
        if grafo is None:
            raise PanelNoDisponible("No está disponible la versión de mapa de la partida.")
        mapa = grafo.mapa
        snapshot.partida.validar_mapa(mapa)

        return {
            "version": mapa.version,
            "nodos": tuple(
                {"id": nodo.id, "lat": nodo.lat, "lng": nodo.lng}
                for nodo in mapa.nodos
            ),
            "calles": tuple(
                {
                    "id": calle.id,
                    "segmentoId": calle.segmento_id,
                    "origen": calle.origen,
                    "destino": calle.destino,
                    "distanciaM": calle.distancia_m,
                    "tipo": calle.tipo.value,
                }
                for calle in mapa.calles
            ),
            "refugios": tuple(
                {"id": refugio.id, "nodo": refugio.nodo}
                for refugio in mapa.refugios
            ),
        }
