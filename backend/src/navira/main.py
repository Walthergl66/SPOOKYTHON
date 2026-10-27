"""Punto de ensamblaje de la aplicación ASGI."""

import functools
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from navira.adapters.ordenes_memoria import RepositorioOrdenesMemoria
from navira.adapters.sesiones_memoria import RepositorioSesionesMemoria
from navira.api.routes import router
from navira.api.seguridad import ConfiguracionSeguridad
from navira.application.coordinador_juego import CoordinadorJuego
from navira.application.decidir_paso import DecidirPasoEspera
from navira.application.consultar_panel import ConsultarPanel
from navira.application.control_simulador_demo import ControlSimuladorDemoLocal
from navira.application.juego import ConsultarSesionJuego, UnirseAJuego
from navira.application.ordenes import RegistrarOrdenHumana
from navira.application.puerta_decisiones import PuertaDecisiones
from navira.application.reloj_juego import RelojJuegoLocal
from navira.demo import (
    MAPA_DEMO_POR_DEFECTO,
    MAPA_MANTA_POR_DEFECTO,
    IntensidadDemo,
    crear_contexto_demo,
    crear_contexto_juego_demo,
)


def crear_app(
    servicio_decision=None,
    consultar_panel: ConsultarPanel | None = None,
    unirse_juego: UnirseAJuego | None = None,
    registrar_orden_juego: RegistrarOrdenHumana | None = None,
    reloj_juego: RelojJuegoLocal | None = None,
    consultar_sesion_juego: ConsultarSesionJuego | None = None,
    control_simulador_demo: ControlSimuladorDemoLocal | None = None,
    seguridad: ConfiguracionSeguridad | None = None,
) -> FastAPI:
    """Ensamblaje inyectable; sin servicio recibe espera determinista y sin seguridad, la más cerrada."""

    @asynccontextmanager
    async def lifespan(_aplicacion: FastAPI):
        if reloj_juego is not None:
            reloj_juego.iniciar()
        print("Navira backend OK: arrancado.", flush=True)
        try:
            yield
        finally:
            if reloj_juego is not None:
                reloj_juego.detener()
            if control_simulador_demo is not None:
                control_simulador_demo.cerrar()

    aplicacion = FastAPI(
        title="Navira",
        description="Motor de evacuación dinámica para Escape de Manta Zombie.",
        version="0.1.0",
        lifespan=lifespan,
    )
    aplicacion.state.seguridad = seguridad or ConfiguracionSeguridad()
    aplicacion.state.decidir_paso = servicio_decision or DecidirPasoEspera()
    aplicacion.state.consultar_panel = consultar_panel
    aplicacion.state.consultar_sesion_juego = consultar_sesion_juego
    aplicacion.state.control_simulador_demo = control_simulador_demo
    aplicacion.state.unirse_juego = unirse_juego
    aplicacion.state.registrar_orden_juego = registrar_orden_juego
    aplicacion.include_router(router)
    return aplicacion


def crear_app_demo(
    *,
    ruta_mapa=MAPA_DEMO_POR_DEFECTO,
    semilla: int | None = None,
    escenario: str = "libre",
    cantidad_sobrevivientes: int = 1,
    intensidad: IntensidadDemo = "media",
    eventos_ciudad: bool = False,
    seguridad: ConfiguracionSeguridad | None = None,
) -> FastAPI:
    """Arranca explícitamente el mundo sintético local para desarrollo."""

    contexto = crear_contexto_demo(
        ruta_mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=cantidad_sobrevivientes,
        intensidad=intensidad,
        eventos_ciudad=eventos_ciudad,
    )
    return crear_app(
        contexto.servicio_decision,
        ConsultarPanel(contexto.snapshots, contexto.mapas, contexto.servicio_decision),
        seguridad=seguridad,
    )


def crear_app_juego_demo(
    *,
    ruta_mapa=MAPA_DEMO_POR_DEFECTO,
    semilla: int | None = None,
    escenario: str = "libre",
    cantidad_sobrevivientes: int = 1,
    intensidad: IntensidadDemo = "media",
    seguridad: ConfiguracionSeguridad | None = None,
) -> FastAPI:
    """Ensamblaje explícito de juego local sintético, con reloj del servidor."""

    contexto = crear_contexto_juego_demo(
        ruta_mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=cantidad_sobrevivientes,
        intensidad=intensidad,
    )
    sesiones = RepositorioSesionesMemoria(
        inactividad_segundos=float(os.environ.get("NAVIRA_GAME_SESSION_IDLE_SECONDS", "1800")),
        reloj_monotonico=time.monotonic,
    )
    ordenes = RepositorioOrdenesMemoria()
    puerta = PuertaDecisiones()
    unirse = UnirseAJuego(contexto.snapshots, contexto.mapas, sesiones)
    registrar = RegistrarOrdenHumana(
        contexto.snapshots,
        contexto.mapas,
        sesiones,
        ordenes,
        puerta,
    )
    coordinador = CoordinadorJuego(
        contexto.snapshots,
        contexto.mapas,
        unirse,
        ordenes,
        contexto.servicio_decision,
        puerta,
    )
    reloj = RelojJuegoLocal(
        contexto.run_id,
        contexto.snapshots,
        coordinador,
        puerta,
    )
    return crear_app(
        contexto.servicio_decision,
        ConsultarPanel(contexto.snapshots, contexto.mapas, contexto.servicio_decision, puerta),
        unirse,
        registrar,
        reloj,
        ConsultarSesionJuego(contexto.snapshots, sesiones, ordenes),
        seguridad=seguridad,
    )


def crear_control_simulador_demo(
    ruta_mapa: str = str(MAPA_MANTA_POR_DEFECTO),
) -> ControlSimuladorDemoLocal:
    """Ensambla el control local con la fábrica de contexto de demo."""

    return ControlSimuladorDemoLocal(functools.partial(crear_contexto_demo, ruta_mapa))


def _leer_parametros_demo() -> tuple[str, int | None, str, int]:
    """Lee mapa, semilla opcional, escenario y sobrevivientes de la demo desde el entorno."""

    mapa = os.environ.get("NAVIRA_DEMO_MAP", str(MAPA_DEMO_POR_DEFECTO))
    valor_semilla = os.environ.get("NAVIRA_DEMO_SEED")
    semilla = int(valor_semilla) if valor_semilla is not None else None
    escenario = os.environ.get("NAVIRA_DEMO_SCENARIO", "libre")
    sobrevivientes = int(os.environ.get("NAVIRA_DEMO_SURVIVORS", "1"))
    return mapa, semilla, escenario, sobrevivientes


def _crear_app_configurada() -> FastAPI:
    """Activa demo solo con opt-in explícito del proceso local.

    Punto de lectura del entorno junto con la inactividad de sesión de juego
    (NAVIRA_GAME_SESSION_IDLE_SECONDS), que se lee en crear_app_juego_demo.
    """

    seguridad = ConfiguracionSeguridad(
        api_key=os.environ.get("NAVIRA_API_KEY") or None,
        cookie_segura=os.environ.get("NAVIRA_COOKIE_SECURE", "1") != "0",
        control_demo_local=os.environ.get("NAVIRA_LOCAL_DEMO_CONTROL") == "1",
    )

    if os.environ.get("NAVIRA_GAME_DEMO") == "1":
        mapa, semilla, escenario, sobrevivientes = _leer_parametros_demo()
        return crear_app_juego_demo(
            ruta_mapa=mapa,
            semilla=semilla,
            escenario=escenario,
            cantidad_sobrevivientes=sobrevivientes,
            seguridad=seguridad,
        )
    if os.environ.get("NAVIRA_LOCAL_DEMO_CONTROL") == "1":
        mapa = os.environ.get("NAVIRA_DEMO_MAP", str(MAPA_MANTA_POR_DEFECTO))
        return crear_app(
            control_simulador_demo=crear_control_simulador_demo(mapa),
            seguridad=seguridad,
        )
    if os.environ.get("NAVIRA_DEMO") == "1":
        mapa, semilla, escenario, sobrevivientes = _leer_parametros_demo()
        return crear_app_demo(
            ruta_mapa=mapa,
            semilla=semilla,
            escenario=escenario,
            cantidad_sobrevivientes=sobrevivientes,
            seguridad=seguridad,
        )
    return crear_app(seguridad=seguridad)


app = _crear_app_configurada()
