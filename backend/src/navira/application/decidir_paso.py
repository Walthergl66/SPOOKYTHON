"""Política de ruta desde el único snapshot activo conocido por la aplicación."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock

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
from navira.routing.dijkstra import PerfilCostos, Ruta, RutasHaciaRefugios, seleccionar_refugio
from navira.routing.prediccion import (
    SobrevivienteObservable,
    ZombieObservable,
    exposicion_vecinal_zombie,
    pronosticar_zombies_visibles,
)
from navira.routing.temporal import CondicionTurno, buscar_ruta_temporal
from navira.domain.snapshot import CompromisoRuta, SnapshotMundo
from navira.application.puertos_paso import (  # noqa: F401
    EntidadNoEncontrada,
    PartidaNoDisponible,
    PasoIncompatible,
    ProveedorMapas,
    ProveedorSnapshotsActivos,
)
from navira.domain.visibilidad import nodos_horda_visibles, peligros_visibles  # noqa: F401


def _exposicion_pronosticada(ruta: tuple[str, ...], futuras: tuple[CondicionTurno, ...]) -> float:
    """Sum exposure only for steps with an explicit forecast.

    The forecast is a bounded scenario, not a steady-state hazard field. Reusing
    its last turn for every later route node invents risk and can make a valid
    refuge path look arbitrarily worse merely because it is longer.
    """

    return sum(
        futuras[paso].exposicion_nodo.get(nodo, 0.0)
        for paso, nodo in enumerate(ruta[1 : len(futuras) + 1])
    )


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
        radio_replanificacion_saltos: int = 3,
    ) -> None:
        self._snapshots = snapshots
        self._mapas = mapas
        self._perfil = perfil
        self._horizonte_turnos = horizonte_turnos
        self._presupuesto_temporal_ms = presupuesto_temporal_ms
        if radio_replanificacion_saltos < 0:
            raise ValueError("El radio de replanteamiento no puede ser negativo.")
        self._radio_replanificacion_saltos = radio_replanificacion_saltos
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

    def proponer_compromiso_en_snapshot(
        self, snapshot: SnapshotMundo, sobreviviente_id: str, grafo: Grafo
    ) -> CompromisoRuta | None:
        """Crea la ruta completa que se guardará solo si su primer paso se resuelve."""

        ruta = self.prever_ruta_en_snapshot(snapshot, sobreviviente_id, grafo)
        refugio = next((item for item in grafo.mapa.refugios if item.nodo == ruta[-1]), None)
        if refugio is None or len(ruta) < 2:
            return None
        return CompromisoRuta(sobreviviente_id, refugio.id, ruta)

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
        A shared snapshot may use soft congestion as an initial/replan tie-break,
        but it cannot invalidate an already committed route by itself.
        """
        activos = tuple(
            s for s in snapshot.partida.sobrevivientes
            if s.estado is EstadoSobreviviente.ACTIVO
        )
        if not activos:
            return {}
        compromisos = {ruta.sobreviviente_id: ruta for ruta in snapshot.rutas_comprometidas}
        asignados: dict[str, tuple[str, ...]] = {}
        pendientes: list[Sobreviviente] = []
        rutas_estaticas: list[Sobreviviente] = []
        for survivor in activos:
            compromiso = compromisos.get(survivor.id)
            retenida = self._ruta_comprometida_vigente(snapshot, grafo, survivor, compromiso)
            if retenida is not None:
                asignados[survivor.id] = retenida
            elif compromiso is None or self._hay_zombie_cerca(snapshot, grafo, survivor.nodo):
                pendientes.append(survivor)
            else:
                rutas_estaticas.append(survivor)

        if rutas_estaticas:
            # Invalidated commitments without nearby zombies use the same static
            # snapshot. Share the reverse Dijkstra field for each refuge instead
            # of traversing Manta once per resident.
            bloqueados, cruces = peligros_visibles(snapshot, grafo)
            por_refugio: dict[str | None, list[Sobreviviente]] = {}
            for survivor in rutas_estaticas:
                por_refugio.setdefault(survivor.refugio_objetivo, []).append(survivor)
            refugios_por_id = {refugio.id: refugio for refugio in grafo.mapa.refugios}
            campos_estaticos: dict[str | None, RutasHaciaRefugios] = {}
            for objetivo, grupo in por_refugio.items():
                nodos_destino = (
                    (refugios_por_id[objetivo].nodo,)
                    if objetivo is not None
                    else tuple(refugio.nodo for refugio in grafo.mapa.refugios)
                )
                # Keep the established selector for a blocked shelter: it has
                # special origin-at-shelter behavior which a shared field does
                # not encode. All other members can share one field.
                compatibles = [
                    survivor for survivor in grupo
                    if not (set(nodos_destino) & bloqueados)
                ]
                individuales = [survivor for survivor in grupo if survivor not in compatibles]
                for survivor in individuales:
                    asignados[survivor.id] = self._ruta_estatica(snapshot, grafo, survivor)
                if not compatibles:
                    continue
                campo = RutasHaciaRefugios(
                    grafo, refugio_objetivo=objetivo,
                    aristas_cerradas=snapshot.aristas_cerradas | cruces,
                    segmentos_cerrados=snapshot.segmentos_cerrados,
                    nodos_bloqueados=frozenset(bloqueados), perfil=self._perfil,
                )
                for survivor in compatibles:
                    ruta = campo.desde(survivor.nodo)
                    if ruta is None and objetivo is not None:
                        campo_alternativo = campos_estaticos.get(None)
                        if campo_alternativo is None:
                            campo_alternativo = RutasHaciaRefugios(
                                grafo, aristas_cerradas=snapshot.aristas_cerradas | cruces,
                                segmentos_cerrados=snapshot.segmentos_cerrados,
                                nodos_bloqueados=frozenset(bloqueados), perfil=self._perfil,
                            )
                            campos_estaticos[None] = campo_alternativo
                        ruta = campo_alternativo.desde(survivor.nodo)
                    asignados[survivor.id] = (
                        (ruta.origen, *(calle.destino for calle in ruta.calles))
                        if ruta is not None else (survivor.nodo,)
                    )
        activos = tuple(pendientes)
        if not activos:
            return asignados
        # Preserve the full bounded temporal search for a lone evacuee; group
        # planning below uses one shared observable forecast plus static tails
        # so a single /paso request does not fan out hundreds of 25 ms searches.
        if len(activos) == 1:
            survivor = activos[0]
            asignados[survivor.id] = self._seleccionar_trayecto(snapshot, grafo, survivor)
            return asignados
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
            exposicion_nodo=exposicion_vecinal_zombie(
                grafo,
                {
                    zombie.nodo: 1.0
                    for zombie in snapshot.partida.zombies
                    if zombie.estado is EstadoZombie.ACTIVO
                    and zombie.tipo not in {TipoZombie.DORMIDO, TipoZombie.HORDA}
                },
                aristas_cerradas=snapshot.aristas_cerradas,
                segmentos_cerrados=snapshot.segmentos_cerrados,
            ),
            aristas_cruce_peligroso=cruces,
        )
        actual, futuras = self._pronostico_compartido(snapshot, grafo, actual, zombies, observables)
        riesgo_actual = actual.exposicion_nodo

        def exposicion_ruta(ruta: tuple[str, ...]) -> float:
            return _exposicion_pronosticada(ruta, futuras)

        # Resolve the most exposed residents first; stable IDs make ties replayable.
        orden = sorted(activos, key=lambda s: (-riesgo_actual.get(s.nodo, 0.0), s.id))
        ocupacion: dict[str, int] = {}
        # At most one reverse search per target/filter set, shared by this
        # cohort only. Current crossings must not contaminate future tails.
        campos: dict[tuple[str | None, frozenset[str]], RutasHaciaRefugios] = {}

        def ruta_desde(origen: str, objetivo: str | None, *, paso_actual: bool = False) -> Ruta | None:
            cierres = actual.aristas_cerradas | actual.aristas_cruce_peligroso if paso_actual else actual.aristas_cerradas
            clave = (objetivo, cierres)
            if clave not in campos:
                campos[clave] = RutasHaciaRefugios(
                    grafo, refugio_objetivo=objetivo, aristas_cerradas=cierres,
                    segmentos_cerrados=actual.segmentos_cerrados,
                    nodos_bloqueados=actual.nodos_bloqueados, perfil=self._perfil,
                )
            ruta = campos[clave].desde(origen)
            if ruta is None and objetivo is not None:
                return ruta_desde(origen, None, paso_actual=paso_actual)
            return ruta

        for survivor in orden:
            candidatos: dict[str, tuple[float, float, tuple[str, ...]]] = {}
            ruta_base = ruta_desde(survivor.nodo, survivor.refugio_objetivo, paso_actual=True)
            destino_base = None
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
                ruta = ruta_desde(calle.destino, survivor.refugio_objetivo)
                if ruta is None:
                    continue
                camino = (survivor.nodo, calle.destino, *(c.destino for c in ruta.calles))
                # Collapse a duplicate destination when it is itself the shelter.
                camino = tuple(dict.fromkeys(camino)) if ruta.destino == calle.destino else camino
                if len(camino) != len(set(camino)):
                    continue
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
                    siguiente = futuras[0].exposicion_nodo if futuras else {}
                    destino = min(
                        salidas,
                        key=lambda calle: (
                            siguiente.get(calle.destino, 0.0),
                            ocupacion.get(calle.destino, 0),
                            self._perfil.costo(calle),
                            calle.destino,
                        ),
                    ).destino
                    # Guard B: waiting (R-03) is a zero-cost candidate; moving
                    # must strictly lower the forecast exposure of the node.
                    if (
                        survivor.nodo not in actual.nodos_bloqueados
                        and siguiente.get(destino, 0.0) >= siguiente.get(survivor.nodo, 0.0)
                    ):
                        destino = survivor.nodo
                    asignados[survivor.id] = (
                        (survivor.nodo,) if destino == survivor.nodo else (survivor.nodo, destino)
                    )
                    if destino != survivor.nodo:
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

    def _ruta_comprometida_vigente(
        self,
        snapshot: SnapshotMundo,
        grafo: Grafo,
        survivor: Sobreviviente,
        compromiso: CompromisoRuta | None,
    ) -> tuple[str, ...] | None:
        """Retains the route until nearby danger or a confirmed closure invalidates it."""

        if compromiso is None or self._hay_zombie_cerca(snapshot, grafo, survivor.nodo):
            return None
        refugio = next((r for r in grafo.mapa.refugios if r.id == compromiso.refugio_id), None)
        if (
            refugio is None
            or compromiso.nodos[0] != survivor.nodo
            or compromiso.nodos[-1] != refugio.nodo
        ):
            return None
        bloqueados, cruces = peligros_visibles(snapshot, grafo)
        if survivor.refugio_objetivo is not None and survivor.refugio_objetivo != refugio.id:
            ruta_objetivo = seleccionar_refugio(
                grafo,
                survivor.nodo,
                refugio_objetivo=survivor.refugio_objetivo,
                aristas_cerradas=snapshot.aristas_cerradas | cruces,
                segmentos_cerrados=snapshot.segmentos_cerrados,
                nodos_bloqueados=frozenset(bloqueados),
                perfil=self._perfil,
            )
            if ruta_objetivo is not None:
                return None
        if set(compromiso.nodos[1:]) & bloqueados:
            return None
        for indice, (origen, destino) in enumerate(zip(compromiso.nodos, compromiso.nodos[1:])):
            cierres = snapshot.aristas_cerradas | (cruces if indice == 0 else frozenset())
            if not any(
                calle.destino == destino
                for calle in grafo.calles_desde(
                    origen, aristas_cerradas=cierres, segmentos_cerrados=snapshot.segmentos_cerrados
                )
            ):
                return None
        return compromiso.nodos

    def _hay_zombie_cerca(self, snapshot: SnapshotMundo, grafo: Grafo, origen: str) -> bool:
        """Uses visible active zombies and undirected street hops, never hidden state."""

        zombies = {
            zombie.nodo
            for zombie in snapshot.partida.zombies
            if zombie.estado is EstadoZombie.ACTIVO and zombie.tipo is not TipoZombie.DORMIDO
        }
        if not zombies:
            return False
        distancias = {origen: 0}
        pendientes = deque([origen])
        entrantes = grafo.entrantes_habilitadas(frozenset(), frozenset())
        while pendientes:
            nodo = pendientes.popleft()
            distancia = distancias[nodo]
            if nodo in zombies:
                return True
            if distancia >= self._radio_replanificacion_saltos:
                continue
            vecinos = {calle.destino for calle in grafo.salientes(nodo)} | set(entrantes[nodo])
            for vecino in vecinos:
                if vecino not in distancias:
                    distancias[vecino] = distancia + 1
                    pendientes.append(vecino)
        return False

    def _ruta_estatica(
        self, snapshot: SnapshotMundo, grafo: Grafo, survivor: Sobreviviente
    ) -> tuple[str, ...]:
        """Keeps residents on a legal shortest path until a zombie is nearby."""

        bloqueados, cruces = peligros_visibles(snapshot, grafo)
        ruta = seleccionar_refugio(
            grafo,
            survivor.nodo,
            refugio_objetivo=survivor.refugio_objetivo,
            aristas_cerradas=snapshot.aristas_cerradas | cruces,
            segmentos_cerrados=snapshot.segmentos_cerrados,
            nodos_bloqueados=frozenset(bloqueados),
            perfil=self._perfil,
        )
        if ruta is None and survivor.refugio_objetivo is not None:
            ruta = seleccionar_refugio(
                grafo,
                survivor.nodo,
                aristas_cerradas=snapshot.aristas_cerradas | cruces,
                segmentos_cerrados=snapshot.segmentos_cerrados,
                nodos_bloqueados=frozenset(bloqueados),
                perfil=self._perfil,
            )
        if ruta is not None:
            return (ruta.origen, *(calle.destino for calle in ruta.calles))
        return (survivor.nodo,)

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
        # El snapshot es inmutable y sus transiciones completas validan el mapa
        # al preparar y resolver el turno. No recorras a toda la cohorte por cada
        # POST /paso; valida aquí la versión y el contexto del único actor pedido.
        if partida.map_version != grafo.mapa.version:
            raise PartidaNoDisponible("La versión de mapa no coincide con la partida.")
        if sobreviviente.nodo not in grafo.mapa.nodos_por_id:
            raise PartidaNoDisponible(
                f"{sobreviviente.id} referencia el nodo inexistente {sobreviviente.nodo}."
            )
        if sobreviviente.refugio_objetivo is not None and not any(
            refugio.id == sobreviviente.refugio_objetivo for refugio in grafo.mapa.refugios
        ):
            raise PartidaNoDisponible(
                f"{sobreviviente.id} referencia el refugio inexistente "
                f"{sobreviviente.refugio_objetivo}."
            )

        return snapshot, sobreviviente, grafo

    def _seleccionar_trayecto(
        self, snapshot: SnapshotMundo, grafo: Grafo, sobreviviente: Sobreviviente
    ) -> tuple[str, ...]:
        """Intenta exposición futura observable y conserva Dijkstra como respaldo."""
        nodos_bloqueados, cruces_peligrosos = peligros_visibles(snapshot, grafo)
        aristas_cerradas = snapshot.aristas_cerradas
        refugio_objetivo = sobreviviente.refugio_objetivo
        refugios = (
            frozenset({refugio_objetivo})
            if refugio_objetivo is not None
            else frozenset(refugio.id for refugio in grafo.mapa.refugios)
        )
        condicion_actual = CondicionTurno(
            nodos_bloqueados=frozenset(nodos_bloqueados),
            aristas_cerradas=aristas_cerradas,
            segmentos_cerrados=snapshot.segmentos_cerrados,
            exposicion_nodo=exposicion_vecinal_zombie(
                grafo,
                {
                    zombie.nodo: 1.0
                    for zombie in snapshot.partida.zombies
                    if zombie.estado is EstadoZombie.ACTIVO
                    and zombie.tipo not in {TipoZombie.DORMIDO, TipoZombie.HORDA}
                },
                aristas_cerradas=aristas_cerradas,
                segmentos_cerrados=snapshot.segmentos_cerrados,
            ),
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
        if refugio_objetivo is not None:
            ruta_objetivo = seleccionar_refugio(
                grafo,
                sobreviviente.nodo,
                refugio_objetivo=refugio_objetivo,
                aristas_cerradas=aristas_cerradas | cruces_peligrosos,
                segmentos_cerrados=snapshot.segmentos_cerrados,
                nodos_bloqueados=frozenset(nodos_bloqueados),
                perfil=self._perfil,
            )
            if ruta_objetivo is None:
                # The configured destination has no currently legal route.
                # Replan to the closest reachable refuge instead of waiting.
                refugios = frozenset(refugio.id for refugio in grafo.mapa.refugios)
                refugio_objetivo = None
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
            refugio_objetivo=refugio_objetivo,
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
        mejor = min(candidatos)
        # Guard B: wait unless moving strictly lowers forecast exposure (R-03).
        if (
            sobreviviente.nodo not in actual.nodos_bloqueados
            and mejor[0] >= riesgo_siguiente.get(sobreviviente.nodo, 0.0)
        ):
            return (sobreviviente.nodo,)
        return (sobreviviente.nodo, mejor[-1])

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
