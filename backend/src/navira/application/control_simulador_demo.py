"""Control de partidas sintéticas para uso explícito en desarrollo local."""

from __future__ import annotations

from threading import RLock
from dataclasses import replace
from typing import Literal, Protocol
import uuid

from navira.application.consultar_panel import ConsultarPanel
from navira.application.decidir_paso import DecidirPaso, ProveedorMapas
from navira.application.reloj_simulador import RelojSimuladorLocal, validar_velocidad
from navira.application.simulacion_automatica import EjecutarRondaAutomatica
from navira.application.snapshots import RepositorioSnapshots
from navira.domain.mapa import Grafo, Mapa, Refugio, nodos_protegidos_refugios
from navira.domain.modelo import EstadoPartida, EstadoSobreviviente, EstadoZombie, ModoPartida, Sobreviviente, TipoZombie, Zombie
from navira.domain.snapshot import EventoCierre, SnapshotMundo


class ContextoSimulacion(Protocol):
    """Dependencias de una partida que el control necesita para operarla."""

    @property
    def snapshots(self) -> RepositorioSnapshots: ...

    @property
    def mapas(self) -> ProveedorMapas: ...

    @property
    def servicio_decision(self) -> DecidirPaso: ...

    @property
    def run_id(self) -> str: ...


class FabricaContextoSimulacion(Protocol):
    """Crea una partida sintética nueva; la implementación concreta se inyecta."""

    def __call__(
        self,
        *,
        semilla: int | None,
        escenario: str,
        cantidad_sobrevivientes: int,
        cantidad_zombies: int | None,
        intensidad: str,
        eventos_ciudad: bool,
        refugios: tuple[Refugio, ...] | None = None,
        ronda_reto: int | None = None,
        mundo_vacio: bool = False,
    ) -> ContextoSimulacion: ...


class ControlSimuladorDemoLocal:
    """Crea y controla una única partida sintética volátil."""

    def __init__(self, crear_contexto: FabricaContextoSimulacion, mapa: Mapa | None = None) -> None:
        self._crear_contexto = crear_contexto
        self.mapa = mapa  # mapa base del simulador; sirve para ofrecer candidatos de refugio
        self._lock = RLock()
        self._contexto: ContextoSimulacion | None = None
        self._reloj: RelojSimuladorLocal | None = None
        self._panel: ConsultarPanel | None = None
        self._configuracion: dict[str, object] = {}
        self._estado: Literal["sin_partida", "activa", "pausada", "finalizada", "error"] = "sin_partida"
        # La velocidad es del operador, no de una partida: sobrevive a iniciar y reiniciar.
        self._velocidad: float = 4.0

    @property
    def consultar_panel(self) -> ConsultarPanel | None:
        return self._panel

    @property
    def decidir_paso(self):
        return self._contexto.servicio_decision if self._contexto is not None else None

    def estado(self) -> dict[str, object]:
        with self._lock:
            snapshot = self._snapshot()
            if snapshot is not None and self._reloj is not None and self._reloj.error:
                self._estado = "error"
            elif snapshot is not None and (
                snapshot.partida.estado.value != "activa"
                or (
                    not self._configuracion.get("mundo_vacio", False)
                    and not any(item.estado.value == "activo" for item in snapshot.partida.sobrevivientes)
                )
            ):
                self._estado = "finalizada"
            elif self._reloj is not None and self._reloj.pausado:
                self._estado = "pausada"
            elif self._reloj is not None and self._reloj.ejecutandose and self._reloj.error is None:
                self._estado = "activa"
            return {
                "habilitado": True,
                "estado": self._estado,
                "runId": snapshot.partida.run_id if snapshot is not None else None,
                "turno": snapshot.partida.turno if snapshot is not None else None,
                "escenario": self._configuracion.get("escenario"),
                "sobrevivientesIniciales": self._configuracion.get("cantidad_sobrevivientes"),
                "zombiesIniciales": self._configuracion.get("cantidad_zombies"),
                "intensidad": self._configuracion.get("intensidad"),
                "eventosCiudad": self._configuracion.get("eventos_ciudad"),
                "rondaReto": self._configuracion.get("ronda_reto"),
                "velocidad": 1.0 if self._configuracion.get("ronda_reto") is not None else self._velocidad,
                "error": self._reloj.error if self._reloj is not None else None,
            }

    def iniciar(
        self,
        *,
        escenario: str,
        cantidad_sobrevivientes: int,
        cantidad_zombies: int | None = None,
        intensidad: str = "media",
        semilla: int | None = None,
        refugios: tuple[Refugio, ...] | None = None,
        ronda_reto: int | None = None,
        mundo_vacio: bool = False,
    ) -> dict[str, object]:
        with self._lock:
            self._detener_reloj()
            if mundo_vacio and ronda_reto is not None:
                raise ValueError("Un mundo vacío de operador no puede iniciar como Reto.")
            argumentos_contexto = dict(
                semilla=semilla,
                escenario=escenario,
                cantidad_sobrevivientes=cantidad_sobrevivientes,
                cantidad_zombies=cantidad_zombies,
                intensidad=intensidad,
                eventos_ciudad=ronda_reto is None and not mundo_vacio,
                refugios=refugios,
            )
            if mundo_vacio:
                argumentos_contexto["mundo_vacio"] = True
            if ronda_reto is not None:
                argumentos_contexto["ronda_reto"] = ronda_reto
            contexto = self._crear_contexto(**argumentos_contexto)
            ejecutar = EjecutarRondaAutomatica(
                contexto.snapshots,
                contexto.mapas,
                decidir=contexto.servicio_decision,
                bloqueo_operador=self._lock,
            )
            # El flujo del reto usa la cadencia nominal; la preferencia de velocidad
            # de la demo libre se conserva y no se modifica.
            reloj = RelojSimuladorLocal(
                contexto.run_id,
                contexto.snapshots,
                ejecutar,
                velocidad=1.0 if ronda_reto is not None else self._velocidad,
                bloqueo_estado=self._lock,
                continuar_sin_sobrevivientes=mundo_vacio,
            )
            self._contexto = contexto
            self._reloj = reloj
            self._panel = ConsultarPanel(
                contexto.snapshots,
                contexto.mapas,
                contexto.servicio_decision,
            )
            self._configuracion = {
                "escenario": escenario,
                "cantidad_sobrevivientes": cantidad_sobrevivientes,
                "cantidad_zombies": len(contexto.snapshots.obtener(contexto.run_id).partida.zombies),
                "intensidad": intensidad,
                "eventos_ciudad": ronda_reto is None and not mundo_vacio,
                "ronda_reto": ronda_reto,
                "mundo_vacio": mundo_vacio,
            }
            self._estado = "activa"
            reloj.iniciar()
            return self.estado()

    def iniciar_mundo_operador(self) -> dict[str, object]:
        """Inicia una partida sobre el mapa de Manta sin piezas ni eventos.

        El operador coloca refugios, habitantes, zombies e incidentes después
        del inicio; el reloj vacío permanece vivo hasta que cierre la partida.
        """
        return self.iniciar(
            escenario="mixto",
            cantidad_sobrevivientes=0,
            cantidad_zombies=0,
            intensidad="media",
            refugios=(),
            mundo_vacio=True,
        )

    def colocar_elemento(self, *, tipo: str, nodo: str | None = None, segmento_id: str | None = None) -> dict[str, object]:
        """Aplica una intervención de operador al mundo activo mediante CAS.

        La posición solo se acepta si pertenece al mapa versionado actual. Los
        incidentes cierran el segmento de inmediato y las altas invalidan las
        rutas comprometidas para que la próxima resolución recalcule el plan.
        """
        with self._lock:
            if self._contexto is None or self._reloj is None or not self._reloj.ejecutandose:
                raise RuntimeError("Inicia o continúa un mundo en ejecución antes de colocar elementos.")
            if self._configuracion.get("ronda_reto") is not None:
                raise RuntimeError("El modo operador no puede modificar una ronda del Reto.")
            snapshot = self._contexto.snapshots.obtener(self._contexto.run_id)
            if snapshot is None or snapshot.partida.estado is not EstadoPartida.ACTIVA:
                raise RuntimeError("No hay un mundo automático activo para modificar.")
            partida = snapshot.partida
            grafo = self._contexto.mapas.obtener(partida.map_version)
            if grafo is None:
                raise RuntimeError("No está disponible el mapa de la partida.")

            partida_siguiente = partida
            snapshot_siguiente = snapshot
            elemento_id = f"OP-{uuid.uuid4().hex[:12]}"
            if tipo == "incidente":
                if not segmento_id:
                    raise ValueError("Selecciona una calle del mapa para colocar un incidente.")
                segmentos = {calle.segmento_id for calle in grafo.mapa.calles}
                if segmento_id not in segmentos:
                    raise ValueError("La calle seleccionada no pertenece al mapa de la partida.")
                if segmento_id in snapshot.segmentos_cerrados:
                    raise ValueError("Esa calle ya está cerrada.")
                evento = EventoCierre(elemento_id, partida.turno, segmentos=frozenset({segmento_id}), causa="Incidente vial del operador")
                snapshot_siguiente = replace(
                    snapshot,
                    version=snapshot.version + 1,
                    segmentos_cerrados=snapshot.segmentos_cerrados | {segmento_id},
                    eventos_programados=(*snapshot.eventos_programados, evento),
                    eventos_aplicados=(*snapshot.eventos_aplicados, evento.id),
                    rutas_comprometidas=(),
                )
            else:
                if not nodo or nodo not in grafo.mapa.nodos_por_id:
                    raise ValueError("Selecciona una intersección válida del mapa.")
                if tipo == "habitante":
                    if len(partida.sobrevivientes) >= 200:
                        raise ValueError("El mundo alcanzó el límite local de 200 habitantes.")
                    persona = Sobreviviente(elemento_id, nodo)
                    partida_siguiente = replace(partida, sobrevivientes=(*partida.sobrevivientes, persona))
                elif tipo in {item.value for item in TipoZombie}:
                    if len(partida.zombies) >= 200:
                        raise ValueError("El mundo alcanzó el límite local de 200 zombies.")
                    protegido = nodos_protegidos_refugios(grafo)
                    if nodo in protegido:
                        raise ValueError("No se pueden colocar zombies en un refugio ni en su cuadra vecina.")
                    zombie_tipo = TipoZombie(tipo)
                    zombie = Zombie(
                        elemento_id,
                        zombie_tipo,
                        nodo,
                        estado=EstadoZombie.DORMIDO if zombie_tipo is TipoZombie.DORMIDO else EstadoZombie.ACTIVO,
                        turno_activacion=partida.turno + 5 if zombie_tipo is TipoZombie.DORMIDO else None,
                    )
                    partida_siguiente = replace(partida, zombies=(*partida.zombies, zombie))
                elif tipo == "refugio":
                    if any(refugio.nodo == nodo for refugio in grafo.mapa.refugios):
                        raise ValueError("Ya existe un refugio en esa intersección.")
                    if len(grafo.mapa.refugios) >= 8:
                        raise ValueError("El mundo alcanzó el límite local de 8 refugios.")
                    refugio = Refugio(elemento_id, nodo)
                    mapa_nuevo = replace(grafo.mapa, version=f"{grafo.mapa.version}-op-{elemento_id.lower()}", refugios=(*grafo.mapa.refugios, refugio))
                    grafo_nuevo = Grafo(mapa_nuevo)
                    registrar = getattr(self._contexto.mapas, "registrar", None)
                    if registrar is None:
                        raise RuntimeError("El catálogo de mapas no admite refugios dinámicos.")
                    registrar(grafo_nuevo)
                    partida_siguiente = replace(partida, map_version=mapa_nuevo.version)
                else:
                    raise ValueError("Herramienta de operador no reconocida.")
                snapshot_siguiente = replace(snapshot, partida=partida_siguiente, version=snapshot.version + 1, rutas_comprometidas=())

            if not self._contexto.snapshots.guardar_si_version(partida.run_id, snapshot.version, snapshot_siguiente):
                raise RuntimeError("El mundo avanzó mientras colocabas el elemento. Vuelve a seleccionarlo.")
            self._panel = ConsultarPanel(self._contexto.snapshots, self._contexto.mapas, self._contexto.servicio_decision)
            return {"aceptado": True, "elementoId": elemento_id, "tipo": tipo, "runId": partida.run_id, "snapshotVersion": snapshot_siguiente.version}

    def iniciar_ronda_reto(self, ronda: int, semilla: int | None = None) -> dict[str, object]:
        """Inicia un preset Reto; solo reemplaza otra ronda Reto si está pausada."""

        if ronda not in (1, 2, 3):
            raise ValueError("La ronda del reto debe ser 1, 2 o 3.")
        with self._lock:
            actual = self.estado()
            if actual["estado"] == "activa":
                raise RuntimeError("Pausa la ronda actual antes de iniciar otra ronda del reto.")
            if actual["estado"] == "pausada" and self._configuracion.get("ronda_reto") not in (1, 2, 3):
                raise RuntimeError("No se puede reemplazar una partida libre pausada desde el modo Reto.")
            return self.iniciar(
                escenario={1: "caminantes", 2: "reto_medianoche", 3: "mixto"}[ronda],
                cantidad_sobrevivientes={1: 20, 2: 80, 3: 200}[ronda],
                intensidad="media",
                semilla=semilla,
                ronda_reto=ronda,
            )

    def reiniciar_ronda_reto(self) -> dict[str, object]:
        """Recrea la ronda Reto actual como un run nuevo con semilla aleatoria."""

        with self._lock:
            ronda = self._configuracion.get("ronda_reto")
            if ronda not in (1, 2, 3) or self._contexto is None:
                raise RuntimeError("No hay una ronda del reto para reiniciar.")
            return self.iniciar(
                escenario={1: "caminantes", 2: "reto_medianoche", 3: "mixto"}[ronda],
                cantidad_sobrevivientes={1: 20, 2: 80, 3: 200}[ronda],
                intensidad="media",
                ronda_reto=ronda,
            )

    def pausar(self) -> dict[str, object]:
        with self._lock:
            if self._reloj is None or not self._reloj.ejecutandose:
                raise RuntimeError("No hay una simulación local activa para pausar.")
            self._reloj.pausar()
            self._estado = "pausada"
            return self.estado()

    def fijar_velocidad(self, velocidad: float) -> dict[str, object]:
        with self._lock:
            self._velocidad = validar_velocidad(velocidad)
            if self._reloj is not None:
                self._reloj.fijar_velocidad(self._velocidad)
            return self.estado()

    def reanudar(self) -> dict[str, object]:
        with self._lock:
            if self._reloj is None or not self._reloj.ejecutandose:
                raise RuntimeError("No hay una simulación local pausada para continuar.")
            self._reloj.reanudar()
            self._estado = "activa"
            return self.estado()

    def reiniciar(
        self,
        *,
        escenario: str | None = None,
        cantidad_sobrevivientes: int | None = None,
        cantidad_zombies: int | None = None,
        intensidad: str | None = None,
        refugios: tuple[Refugio, ...] | None = None,
    ) -> dict[str, object]:
        zombies_configurados = self._configuracion.get("cantidad_zombies")
        if cantidad_zombies is None and not isinstance(zombies_configurados, int):
            zombies_configurados = None
        return self.iniciar(
            escenario=escenario or str(self._configuracion.get("escenario", "libre")),
            cantidad_sobrevivientes=cantidad_sobrevivientes or int(
                self._configuracion.get("cantidad_sobrevivientes", 20)
            ),
            cantidad_zombies=(
                cantidad_zombies
                if cantidad_zombies is not None
                else zombies_configurados
            ),
            intensidad=intensidad or str(self._configuracion.get("intensidad", "media")),
            refugios=refugios,
        )

    def cerrar(self) -> None:
        with self._lock:
            self._detener_reloj()

    def _snapshot(self):
        if self._contexto is None:
            return None
        return self._contexto.snapshots.obtener(self._contexto.run_id)

    def _detener_reloj(self) -> None:
        if self._reloj is not None:
            self._reloj.detener()
