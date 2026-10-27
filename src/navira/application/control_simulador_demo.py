"""Control de partidas sintéticas para uso explícito en desarrollo local."""

from __future__ import annotations

from threading import RLock
from typing import Literal

from navira.application.consultar_panel import ConsultarPanel
from navira.application.reloj_simulador import RelojSimuladorLocal
from navira.application.simulacion_automatica import EjecutarRondaAutomatica
from navira.demo import MAPA_MANTA_POR_DEFECTO, ContextoDemo, crear_contexto_demo


class ControlSimuladorDemoLocal:
    """Crea y controla una única partida sintética volátil."""

    def __init__(self, ruta_mapa: str = str(MAPA_MANTA_POR_DEFECTO)) -> None:
        self._ruta_mapa = ruta_mapa
        self._lock = RLock()
        self._contexto: ContextoDemo | None = None
        self._reloj: RelojSimuladorLocal | None = None
        self._panel: ConsultarPanel | None = None
        self._configuracion: dict[str, object] = {}
        self._estado: Literal["sin_partida", "activa", "pausada", "finalizada", "error"] = "sin_partida"

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
                "error": self._reloj.error if self._reloj is not None else None,
            }

    def iniciar(
        self,
        *,
        escenario: str,
        cantidad_sobrevivientes: int,
        intensidad: str = "alta",
        eventos_ciudad: bool = True,
        semilla: int | None = None,
    ) -> dict[str, object]:
        with self._lock:
            self._detener_reloj()
            contexto = crear_contexto_demo(
                self._ruta_mapa,
                semilla=semilla,
                escenario=escenario,
                cantidad_sobrevivientes=cantidad_sobrevivientes,
                intensidad=intensidad,  # type: ignore[arg-type]
                eventos_ciudad=eventos_ciudad,
            )
            ejecutar = EjecutarRondaAutomatica(contexto.snapshots, contexto.mapas)
            reloj = RelojSimuladorLocal(contexto.run_id, contexto.snapshots, ejecutar)
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
                "eventos_ciudad": eventos_ciudad,
            }
            self._estado = "activa"
            reloj.iniciar()
            return self.estado()

    def pausar(self) -> dict[str, object]:
        with self._lock:
            if self._reloj is None or not self._reloj.ejecutandose:
                raise RuntimeError("No hay una simulación local activa para pausar.")
            self._reloj.pausar()
            self._estado = "pausada"
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
        eventos_ciudad: bool | None = None,
    ) -> dict[str, object]:
        return self.iniciar(
            escenario=escenario or str(self._configuracion.get("escenario", "libre")),
            cantidad_sobrevivientes=cantidad_sobrevivientes or int(
                self._configuracion.get("cantidad_sobrevivientes", 20)
            ),
            intensidad=intensidad or str(self._configuracion.get("intensidad", "alta")),
            eventos_ciudad=(
                eventos_ciudad
                if eventos_ciudad is not None
                else bool(self._configuracion.get("eventos_ciudad", True))
            ),
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
