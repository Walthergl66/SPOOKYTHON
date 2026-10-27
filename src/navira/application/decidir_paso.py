"""Política de ruta desde el único snapshot activo conocido por la aplicación."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Protocol

from navira.domain.mapa import Grafo
from navira.domain.modelo import (
    EstadoPartida,
    EstadoSobreviviente,
    EstadoZombie,
    FaseTurno,
    Partida,
    Sobreviviente,
    TipoZombie,
)
from navira.routing.dijkstra import PerfilCostos, Ruta, seleccionar_refugio
from navira.routing.prediccion import (
    SobrevivienteObservable,
    ZombieObservable,
    pronosticar_zombies_visibles,
)
from navira.routing.temporal import CondicionTurno, buscar_ruta_temporal
from navira.simulation.coordinador import SnapshotMundo


@dataclass(frozen=True, slots=True)
class SolicitudPaso:
    """Datos del sobreviviente recibidos para una decisión."""

    sobreviviente_id: str
    nodo_actual: str
    turno: int


@dataclass(frozen=True, slots=True)
class DecisionPaso:
    """Destino propuesto; el servidor resuelve y confirma el movimiento después."""

    siguiente_nodo: str


class PartidaNoDisponible(RuntimeError):
    """No existe un snapshot/mapa de partida vigente y usable."""


class PasoIncompatible(RuntimeError):
    """Turno, fase, personaje o posición no coinciden con el mundo vigente."""


class EntidadNoEncontrada(LookupError):
    """El personaje indicado no existe en la partida activa."""


class ProveedorSnapshotsActivos(Protocol):
    def obtener_activa(self) -> SnapshotMundo | None:
        """Devuelve la única partida activa o nada si no hay partida."""


class ProveedorMapas(Protocol):
    def obtener(self, version: str) -> Grafo | None:
        """Busca un grafo validado por su versión inmutable."""


class DecidirPaso:
    """Calcula un paso server-side con prioridad por exposición observable.

    La búsqueda temporal estima amenazas futuras a partir de observaciones
    públicas y las minimiza antes que duración/distancia. Si el pronóstico no
    alcanza el refugio o agota su presupuesto, usa Dijkstra como respaldo.
    Dormidos y RNG privado quedan fuera; menor exposición estimada no garantiza
    menos mordidas reales.
    """

    def __init__(
        self,
        snapshots: ProveedorSnapshotsActivos,
        mapas: ProveedorMapas,
        *,
        perfil: PerfilCostos = PerfilCostos(),
        horizonte_turnos: int = 12,
        presupuesto_temporal_ms: float = 25.0,
    ) -> None:
        self._snapshots = snapshots
        self._mapas = mapas
        self._perfil = perfil
        self._horizonte_turnos = horizonte_turnos
        self._presupuesto_temporal_ms = presupuesto_temporal_ms
        self._cache_pronostico_lock = Lock()
        self._cache_pronostico_clave: tuple[str, int, str] | None = None
        self._cache_pronostico_valor: tuple[CondicionTurno, tuple[CondicionTurno, ...]] | None = None
        self._cache_rutas_lock = Lock()
        self._cache_rutas_snapshot: tuple[str, int, str] | None = None
        self._cache_rutas: dict[str, tuple[str, ...]] = {}
        self._cache_rutas_por_personaje: dict[str, Lock] = {}
        self._cache_plan_lock = Lock()
        self._cache_plan_clave: tuple[str, int, str] | None = None
        self._cache_plan: dict[str, tuple[str, ...]] = {}

    def ejecutar(self, solicitud: SolicitudPaso) -> DecisionPaso:
        snapshot, sobreviviente, grafo = self._obtener_contexto(solicitud)
        trayecto = self._trayecto_cacheado(snapshot, grafo, sobreviviente)
        return DecisionPaso(trayecto[1] if len(trayecto) > 1 else sobreviviente.nodo)

    def prever_ruta(self, solicitud: SolicitudPaso) -> tuple[str, ...]:
        """Devuelve ruta dirigida desde el mismo snapshot y filtro que `/paso`.

        Es una vista previa de decisión, no un movimiento confirmado ni una
        garantía de seguridad. Si no hay ruta, la recomendación es esperar en
        el nodo actual.
        """

        snapshot, sobreviviente, grafo = self._obtener_contexto(solicitud)
        return self._trayecto_cacheado(snapshot, grafo, sobreviviente)

    def prever_ruta_en_snapshot(
        self, snapshot: SnapshotMundo, sobreviviente_id: str, grafo: Grafo
    ) -> tuple[str, ...]:
        """Calcula la ruta de la versión ya leída por el panel.

        Evita volver a consultar el snapshot activo mientras el panel proyecta
        otro: el reloj puede avanzar entre ambas lecturas y mezclar turnos.
        """

        if snapshot.partida.map_version != grafo.mapa.version:
            raise PartidaNoDisponible("El pronóstico y el snapshot usan versiones de mapa distintas.")
        sobreviviente = next(
            (item for item in snapshot.partida.sobrevivientes if item.id == sobreviviente_id),
            None,
        )
        if sobreviviente is None or sobreviviente.estado is not EstadoSobreviviente.ACTIVO:
            raise EntidadNoEncontrada("El sobreviviente activo no existe en el snapshot consultado.")
        return self._trayecto_cacheado(snapshot, grafo, sobreviviente)

    def _trayecto_cacheado(
        self, snapshot: SnapshotMundo, grafo: Grafo, sobreviviente: Sobreviviente
    ) -> tuple[str, ...]:
        """Shares the exact preview/action for one immutable snapshot.

        The temporal search has a wall-clock budget, so rerunning it could
        otherwise time out differently in the panel and automatic resolver.
        Keeping only one snapshot bounds memory and aligns the route line with
        the next server-authored move.
        """

        clave = (snapshot.partida.run_id, snapshot.version, grafo.mapa.version)
        # Plan all active residents together once per immutable world version.
        # This makes batch simulation, concurrent /paso calls and panel previews
        # consume the same coordinated first actions.
        with self._cache_plan_lock:
            if clave != self._cache_plan_clave:
                self._cache_plan = self._planificar_conjunto(snapshot, grafo)
                self._cache_plan_clave = clave
            coordinated = self._cache_plan.get(sobreviviente.id)
        if coordinated is not None:
            return coordinated

        with self._cache_rutas_lock:
            if clave != self._cache_rutas_snapshot:
                self._cache_rutas_snapshot = clave
                self._cache_rutas.clear()
                self._cache_rutas_por_personaje.clear()
            lock_personaje = self._cache_rutas_por_personaje.setdefault(sobreviviente.id, Lock())
        with lock_personaje:
            with self._cache_rutas_lock:
                trayecto = self._cache_rutas.get(sobreviviente.id) if clave == self._cache_rutas_snapshot else None
            if trayecto is not None:
                return trayecto
            trayecto = self._seleccionar_trayecto(snapshot, grafo, sobreviviente)
            with self._cache_rutas_lock:
                if clave == self._cache_rutas_snapshot:
                    self._cache_rutas[sobreviviente.id] = trayecto
            return trayecto

    def _planificar_conjunto(
        self, snapshot: SnapshotMundo, grafo: Grafo
    ) -> dict[str, tuple[str, ...]]:
        """Assigns a risk-first next step to every active survivor in one turn.

        For a group, each shortest legal route is a baseline. When predicted
        exposure or a contested first step warrants it, the planner considers
        legal outgoing alternatives with static tails and a shared forecast.
        It applies a soft per-turn congestion penalty only after exposure.
        Threat exposure always ranks before congestion and route length; this
        does not invent node capacity or alter resolver collision rules.
        """
        activos = tuple(
            s for s in snapshot.partida.sobrevivientes
            if s.estado is EstadoSobreviviente.ACTIVO
        )
        if not activos:
            return {}
        # Preserve the full bounded temporal search for a lone evacuee; group
        # planning below uses one shared observable forecast plus static tails
        # so a single /paso request does not fan out hundreds of 25 ms searches.
        if len(activos) == 1:
            survivor = activos[0]
            return {survivor.id: self._seleccionar_trayecto(snapshot, grafo, survivor)}
        nodos, cruces = peligros_visibles(snapshot, grafo)
        zombies = tuple(
            ZombieObservable(z.id, z.tipo, z.nodo)
            for z in snapshot.partida.zombies
            if z.estado is EstadoZombie.ACTIVO and z.tipo is not TipoZombie.DORMIDO
        )
        observables = tuple(SobrevivienteObservable(s.id, s.nodo) for s in activos)
        actual = CondicionTurno(
            nodos_bloqueados=frozenset(nodos), aristas_cerradas=snapshot.aristas_cerradas,
            segmentos_cerrados=snapshot.segmentos_cerrados,
            aristas_cruce_peligroso=cruces,
        )
        actual, futuras = self._pronostico_compartido(snapshot, grafo, actual, zombies, observables)
        riesgo_actual = actual.exposicion_nodo

        def exposicion_ruta(ruta: tuple[str, ...]) -> float:
            """Compare candidate paths on the same observable forecast horizon."""
            return sum(
                futuras[min(paso, len(futuras) - 1)].exposicion_nodo.get(nodo, 0.0)
                for paso, nodo in enumerate(ruta[1:])
            ) if futuras else 0.0

        # Resolve the most exposed residents first; stable IDs make ties replayable.
        orden = sorted(activos, key=lambda s: (-riesgo_actual.get(s.nodo, 0.0), s.id))
        asignados: dict[str, tuple[str, ...]] = {}
        ocupacion: dict[str, int] = {}
        rutas_restantes: dict[tuple[str, str | None], Ruta | None] = {}
        for survivor in orden:
            candidatos: dict[str, tuple[float, float, tuple[str, ...]]] = {}
            clave_base = (survivor.nodo, survivor.refugio_objetivo)
            if clave_base not in rutas_restantes:
                rutas_restantes[clave_base] = seleccionar_refugio(
                    grafo, survivor.nodo, refugio_objetivo=survivor.refugio_objetivo,
                    aristas_cerradas=actual.aristas_cerradas | actual.aristas_cruce_peligroso,
                    segmentos_cerrados=actual.segmentos_cerrados,
                    nodos_bloqueados=actual.nodos_bloqueados, perfil=self._perfil,
                )
            ruta_base = rutas_restantes[clave_base]
            if ruta_base is not None and ruta_base.calles:
                trayecto_base = (survivor.nodo, *(c.destino for c in ruta_base.calles))
                destino_base = trayecto_base[1]
                candidatos[destino_base] = (
                    exposicion_ruta(trayecto_base), ruta_base.costo_ponderado_m, trayecto_base
                )
                # Common low-risk case: keep the shortest legal route without
                # running alternatives for every resident in a large cohort.
                if candidatos[destino_base][0] == 0 and ocupacion.get(destino_base, 0) == 0:
                    asignados[survivor.id] = trayecto_base
                    ocupacion[destino_base] = 1
                    continue
            for calle in grafo.calles_desde(
                survivor.nodo,
                aristas_cerradas=actual.aristas_cerradas | actual.aristas_cruce_peligroso,
                segmentos_cerrados=actual.segmentos_cerrados,
            ):
                if calle.destino in actual.nodos_bloqueados:
                    continue
                clave_ruta = (calle.destino, survivor.refugio_objetivo)
                if clave_ruta not in rutas_restantes:
                    rutas_restantes[clave_ruta] = seleccionar_refugio(
                        grafo, calle.destino, refugio_objetivo=survivor.refugio_objetivo,
                        aristas_cerradas=actual.aristas_cerradas,
                        segmentos_cerrados=actual.segmentos_cerrados,
                        nodos_bloqueados=actual.nodos_bloqueados, perfil=self._perfil,
                    )
                ruta = rutas_restantes[clave_ruta]
                if ruta is None:
                    continue
                camino = (survivor.nodo, calle.destino, *(c.destino for c in ruta.calles))
                # Collapse a duplicate destination when it is itself the shelter.
                camino = tuple(dict.fromkeys(camino)) if ruta.destino == calle.destino else camino
                riesgo = exposicion_ruta(camino)
                costo = self._perfil.costo(calle) + ruta.costo_ponderado_m
                existente = candidatos.get(calle.destino)
                if existente is None or (riesgo, costo) < (existente[0], existente[1]):
                    candidatos[calle.destino] = (riesgo, costo, camino)
            if not candidatos:
                # A complete refuge path is unavailable. Take the cheapest
                # immediate safe exit by next-turn exposure; do not launch a
                # separate temporal search for every trapped resident.
                salidas = tuple(
                    calle for calle in grafo.calles_desde(
                        survivor.nodo,
                        aristas_cerradas=actual.aristas_cerradas | actual.aristas_cruce_peligroso,
                        segmentos_cerrados=actual.segmentos_cerrados,
                    )
                    if calle.destino not in actual.nodos_bloqueados
                )
                if salidas:
                    destino = min(
                        salidas,
                        key=lambda calle: (
                            futuras[0].exposicion_nodo.get(calle.destino, 0.0) if futuras else 0.0,
                            ocupacion.get(calle.destino, 0),
                            self._perfil.costo(calle),
                            calle.destino,
                        ),
                    ).destino
                    asignados[survivor.id] = (survivor.nodo, destino)
                    ocupacion[destino] = ocupacion.get(destino, 0) + 1
                else:
                    asignados[survivor.id] = (survivor.nodo,)
                continue
            destino = min(
                candidatos,
                key=lambda node: (
                    candidatos[node][0],
                    ocupacion.get(node, 0),
                    candidatos[node][1],
                    node,
                ),
            )
            asignados[survivor.id] = candidatos[destino][2]
            ocupacion[destino] = ocupacion.get(destino, 0) + 1
        return asignados

    def _obtener_contexto(self, solicitud: SolicitudPaso) -> tuple[SnapshotMundo, Sobreviviente, Grafo]:
        """Valida identidad temporal y carga el grafo antes de planificar."""

        try:
            snapshot = self._snapshots.obtener_activa()
        except RuntimeError as error:
            raise PartidaNoDisponible("El repositorio no tiene una única partida activa.") from error
        if snapshot is None:
            raise PartidaNoDisponible("No hay una partida activa.")
        partida = snapshot.partida
        self._validar_turno(partida, solicitud)
        sobreviviente = next(
            (item for item in partida.sobrevivientes if item.id == solicitud.sobreviviente_id),
            None,
        )
        if sobreviviente is None:
            raise EntidadNoEncontrada("El sobreviviente no existe en la partida activa.")
        if sobreviviente.estado is not EstadoSobreviviente.ACTIVO:
            raise PasoIncompatible("El sobreviviente ya no puede tomar decisiones.")
        if sobreviviente.nodo != solicitud.nodo_actual:
            raise PasoIncompatible("El nodo indicado no coincide con la posición confirmada.")

        grafo = self._mapas.obtener(partida.map_version)
        if grafo is None:
            raise PartidaNoDisponible("No está disponible la versión de mapa de la partida.")
        partida.validar_mapa(grafo.mapa)

        return snapshot, sobreviviente, grafo

    def _seleccionar_trayecto(
        self, snapshot: SnapshotMundo, grafo: Grafo, sobreviviente: Sobreviviente
    ) -> tuple[str, ...]:
        """Intenta exposición futura observable y conserva Dijkstra como respaldo."""
        nodos_bloqueados, cruces_peligrosos = peligros_visibles(snapshot, grafo)
        aristas_cerradas = snapshot.aristas_cerradas
        refugios = (
            frozenset({sobreviviente.refugio_objetivo})
            if sobreviviente.refugio_objetivo is not None
            else frozenset(refugio.id for refugio in grafo.mapa.refugios)
        )
        condicion_actual = CondicionTurno(
            nodos_bloqueados=frozenset(nodos_bloqueados),
            aristas_cerradas=aristas_cerradas,
            segmentos_cerrados=snapshot.segmentos_cerrados,
            aristas_cruce_peligroso=cruces_peligrosos,
        )
        zombies = tuple(
            ZombieObservable(zombie.id, zombie.tipo, zombie.nodo)
            for zombie in snapshot.partida.zombies
            if zombie.estado is EstadoZombie.ACTIVO and zombie.tipo is not TipoZombie.DORMIDO
        )
        observables = tuple(
            SobrevivienteObservable(item.id, item.nodo)
            for item in snapshot.partida.sobrevivientes
            if item.estado is EstadoSobreviviente.ACTIVO
        )
        condicion_actual, condiciones_futuras = self._pronostico_compartido(
            snapshot,
            grafo,
            condicion_actual,
            zombies,
            observables,
        )
        temporal = buscar_ruta_temporal(
            grafo,
            sobreviviente.nodo,
            refugios,
            peligros_actuales=condicion_actual,
            pronostico=condiciones_futuras,
            horizonte_turnos=self._horizonte_turnos,
            presupuesto_ms=self._presupuesto_temporal_ms,
            perfil=self._perfil,
        )
        if temporal.estado in {"ruta_encontrada", "en_refugio"} and temporal.trayecto:
            return temporal.trayecto

        ruta = seleccionar_refugio(
            grafo,
            sobreviviente.nodo,
            refugio_objetivo=sobreviviente.refugio_objetivo,
            aristas_cerradas=aristas_cerradas | cruces_peligrosos,
            segmentos_cerrados=snapshot.segmentos_cerrados,
            nodos_bloqueados=frozenset(nodos_bloqueados),
            perfil=self._perfil,
        )
        if ruta is None:
            return self._ruta_escape_inmediato(
                grafo,
                sobreviviente,
                condicion_actual,
                condiciones_futuras,
            )
        return (ruta.origen, *(calle.destino for calle in ruta.calles))

    def _ruta_escape_inmediato(
        self,
        grafo: Grafo,
        sobreviviente: Sobreviviente,
        actual: CondicionTurno,
        futuras: tuple[CondicionTurno, ...],
    ) -> tuple[str, ...]:
        """Leaves immediate danger if all complete routes to shelter are cut.

        Waiting on a node occupied by a zombie is a known bite, while a
        topologically valid move to a clear neighbor may buy another turn.
        Rank legal escape neighbors by next-turn forecast, then by remaining
        static cost to a refuge. If every exit is occupied or closed, waiting
        remains the only legal action.
        """

        riesgo_siguiente = futuras[0].exposicion_nodo if futuras else {}
        candidatos: list[tuple[float, float, float, str]] = []
        for calle in grafo.calles_desde(
            sobreviviente.nodo,
            aristas_cerradas=actual.aristas_cerradas | actual.aristas_cruce_peligroso,
            segmentos_cerrados=actual.segmentos_cerrados,
        ):
            if calle.destino in actual.nodos_bloqueados:
                continue
            ruta_refugio = seleccionar_refugio(
                grafo,
                calle.destino,
                refugio_objetivo=sobreviviente.refugio_objetivo,
                aristas_cerradas=actual.aristas_cerradas,
                segmentos_cerrados=actual.segmentos_cerrados,
                perfil=self._perfil,
            )
            costo_refugio = (
                sum(self._perfil.costo(tramo) for tramo in ruta_refugio.calles)
                if ruta_refugio is not None
                else float("inf")
            )
            candidatos.append(
                (
                    riesgo_siguiente.get(calle.destino, 0.0),
                    costo_refugio,
                    self._perfil.costo(calle),
                    calle.destino,
                )
            )
        if not candidatos:
            return (sobreviviente.nodo,)
        destino = min(candidatos)[-1]
        return (sobreviviente.nodo, destino)

    def _pronostico_compartido(
        self,
        snapshot: SnapshotMundo,
        grafo: Grafo,
        condicion_actual: CondicionTurno,
        zombies: tuple[ZombieObservable, ...],
        sobrevivientes: tuple[SobrevivienteObservable, ...],
    ) -> tuple[CondicionTurno, tuple[CondicionTurno, ...]]:
        """Calcula amenazas una vez por snapshot y comparte el valor inmutable.

        La versión de snapshot incluye turno, cierres y posiciones confirmadas;
        una nueva fase/turno invalida la caché. El lock evita repetir el costo
        de pronóstico si varias recomendaciones llegan a la vez.
        """

        clave = (snapshot.partida.run_id, snapshot.version, grafo.mapa.version)
        with self._cache_pronostico_lock:
            if clave == self._cache_pronostico_clave and self._cache_pronostico_valor is not None:
                return self._cache_pronostico_valor
            resultado = pronosticar_zombies_visibles(
                grafo,
                zombies,
                sobrevivientes,
                turno_actual=snapshot.partida.turno,
                horizonte_turnos=self._horizonte_turnos,
                aristas_cerradas=condicion_actual.aristas_cerradas,
                segmentos_cerrados=condicion_actual.segmentos_cerrados,
            )
            self._cache_pronostico_clave = clave
            self._cache_pronostico_valor = (condicion_actual, resultado.turnos)
            return self._cache_pronostico_valor

    @staticmethod
    def _validar_turno(partida: Partida, solicitud: SolicitudPaso) -> None:
        if partida.estado is not EstadoPartida.ACTIVA:
            raise PartidaNoDisponible("La partida activa no está disponible para decisiones.")
        if partida.turno != solicitud.turno or partida.fase is not FaseTurno.DECISIONES:
            raise PasoIncompatible("La solicitud pertenece a otro turno o fase.")


class DecidirPasoEspera:
    """Respaldo local cuando todavía no se ensambla un estado de juego."""

    def ejecutar(self, solicitud: SolicitudPaso) -> DecisionPaso:
        """Espera válida del contrato; no afirma que el nodo sea seguro."""

        return DecisionPaso(siguiente_nodo=solicitud.nodo_actual)


def peligros_visibles(
    snapshot: SnapshotMundo, grafo: Grafo
) -> tuple[set[str], frozenset[str]]:
    """Proyecta ocupación/horda y cruces visibles para decisión y panel.

    Solo considera zombies activos para no filtrar dormidos ocultos. Las hordas
    también bloquean vecinos entrantes/salientes según cierres vigentes.
    """

    partida = snapshot.partida
    nodos: set[str] = set()
    aristas_cruzadas: set[str] = set()
    for zombie in partida.zombies:
        if zombie.estado is not EstadoZombie.ACTIVO:
            continue
        nodos.add(zombie.nodo)
    nodos.update(nodos_horda_visibles(snapshot, grafo))

    for movimiento in snapshot.movimientos_zombies:
        for tramo in movimiento.tramos:
            aristas_cruzadas.update(
                calle.id
                for calle in grafo.mapa.calles
                if calle.segmento_id == tramo.segmento_id
                and calle.origen == tramo.destino
                and calle.destino == tramo.origen
            )
    return nodos, frozenset(aristas_cruzadas)


def nodos_horda_visibles(snapshot: SnapshotMundo, grafo: Grafo) -> frozenset[str]:
    """Lista nodos ocupados o vecinos bloqueados por hordas ya visibles."""

    bloqueados: set[str] = set()
    for zombie in snapshot.partida.zombies:
        if zombie.estado is not EstadoZombie.ACTIVO or zombie.tipo is not TipoZombie.HORDA:
            continue
        bloqueados.add(zombie.nodo)
        bloqueados.update(
            calle.destino
            for calle in grafo.calles_desde(
                zombie.nodo,
                aristas_cerradas=snapshot.aristas_cerradas,
                segmentos_cerrados=snapshot.segmentos_cerrados,
            )
        )
        bloqueados.update(
            calle.origen
            for calle in grafo.mapa.calles
            if calle.destino == zombie.nodo
            and calle.id not in snapshot.aristas_cerradas
            and calle.segmento_id not in snapshot.segmentos_cerrados
        )
    return frozenset(bloqueados)
