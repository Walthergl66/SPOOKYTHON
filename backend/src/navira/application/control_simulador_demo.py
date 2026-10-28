"""Control de partidas sintéticas para uso explícito en desarrollo local."""

from __future__ import annotations

from threading import RLock
from typing import Literal, Protocol

from navira.application.consultar_panel import ConsultarPanel
from navira.application.decidir_paso import DecidirPaso, ProveedorMapas
from navira.application.reloj_simulador import RelojSimuladorLocal, validar_velocidad
from navira.application.simulacion_automatica import EjecutarRondaAutomatica
from navira.application.snapshots import RepositorioSnapshots
from navira.domain.mapa import Mapa, Refugio


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
        intensidad: str,
        eventos_ciudad: bool,
        refugios: tuple[Refugio, ...] | None = None,
        ronda_reto: int | None = None,
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
                or not any(item.estado.value == "activo" for item in snapshot.partida.sobrevivientes)
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
        intensidad: str = "media",
        semilla: int | None = None,
        refugios: tuple[Refugio, ...] | None = None,
        ronda_reto: int | None = None,
    ) -> dict[str, object]:
        with self._lock:
            self._detener_reloj()
            argumentos_contexto = dict(
                semilla=semilla,
                escenario=escenario,
                cantidad_sobrevivientes=cantidad_sobrevivientes,
                intensidad=intensidad,
                eventos_ciudad=ronda_reto is None,
                refugios=refugios,
            )
            if ronda_reto is not None:
                argumentos_contexto["ronda_reto"] = ronda_reto
            contexto = self._crear_contexto(**argumentos_contexto)
            ejecutar = EjecutarRondaAutomatica(
                contexto.snapshots,
                contexto.mapas,
                decidir=contexto.servicio_decision,
            )
            # El flujo del reto usa la cadencia nominal; la preferencia de velocidad
            # de la demo libre se conserva y no se modifica.
            reloj = RelojSimuladorLocal(
                contexto.run_id,
                contexto.snapshots,
                ejecutar,
                velocidad=1.0 if ronda_reto is not None else self._velocidad,
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
                "intensidad": intensidad,
                "eventos_ciudad": ronda_reto is None,
                "ronda_reto": ronda_reto,
            }
            self._estado = "activa"
            reloj.iniciar()
            return self.estado()

    def iniciar_ronda_reto(self, ronda: int, semilla: int | None = None) -> dict[str, object]:
        """Inicia un preset automático de evaluación sin cambiar la configuración libre."""

        if ronda not in (1, 2, 3):
            raise ValueError("La ronda del reto debe ser 1, 2 o 3.")
        if self.estado()["estado"] in ("activa", "pausada"):
            raise RuntimeError("Finaliza la partida actual antes de iniciar una ronda del reto.")
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
        intensidad: str | None = None,
        refugios: tuple[Refugio, ...] | None = None,
    ) -> dict[str, object]:
        return self.iniciar(
            escenario=escenario or str(self._configuracion.get("escenario", "libre")),
            cantidad_sobrevivientes=cantidad_sobrevivientes or int(
                self._configuracion.get("cantidad_sobrevivientes", 20)
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
