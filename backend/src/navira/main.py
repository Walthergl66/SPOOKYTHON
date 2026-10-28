"""Punto de ensamblaje de la aplicación ASGI."""

import functools
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from navira.adapters.ordenes_memoria import RepositorioOrdenesMemoria
from navira.adapters.sesiones_memoria import RepositorioSesionesMemoria
from navira.adapters.sesiones_demo_memoria import LimiteSesionesDemo, RegistroSesionesDemoMemoria
from navira.api.routes import router
from navira.api.seguridad import ConfiguracionSeguridad, fijar_cookie_demo
from navira.application.coordinador_juego import CoordinadorJuego
from navira.application.decidir_paso import DecidirPasoEspera
from navira.application.consultar_panel import ConsultarPanel
from navira.application.control_simulador_demo import ControlSimuladorDemoLocal
from navira.application.juego import ConsultarSesionJuego, UnirseAJuego
from navira.application.ordenes import RegistrarOrdenHumana
from navira.application.puerta_decisiones import PuertaDecisiones
from navira.application.reloj_juego import RelojJuegoLocal
from navira.domain.mapa import cargar_mapa
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
    sesiones_demo_publicas: RegistroSesionesDemoMemoria | None = None,
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
            if sesiones_demo_publicas is not None:
                sesiones_demo_publicas.cerrar()

    aplicacion = FastAPI(
        title="Navira",
        description="Motor de evacuación dinámica para Escape de Manta Zombie.",
        version="0.1.0",
        lifespan=lifespan,
    )
    # The full OSM graph is large; compress JSON map projections for browsers.
    aplicacion.add_middleware(GZipMiddleware, minimum_size=1000)
    aplicacion.state.seguridad = seguridad or ConfiguracionSeguridad()
    aplicacion.state.decidir_paso = servicio_decision or DecidirPasoEspera()
    aplicacion.state.consultar_panel = consultar_panel
    aplicacion.state.consultar_sesion_juego = consultar_sesion_juego
    aplicacion.state.control_simulador_demo = control_simulador_demo
    aplicacion.state.reloj_juego = reloj_juego
    aplicacion.state.sesiones_demo_publicas = sesiones_demo_publicas
    if sesiones_demo_publicas is not None:
        ttl_cookie = int(os.environ.get("NAVIRA_PUBLIC_SESSION_COOKIE_SECONDS", "86400"))

        @aplicacion.middleware("http")
        async def asignar_sesion_demo(request, call_next):
            """Asigna cada petición pública a su mundo y cookie independientes."""

            if not request.url.path.startswith(("/panel/", "/demo/", "/reto/", "/juego/", "/paso")):
                return await call_next(request)
            try:
                control, token_nuevo = sesiones_demo_publicas.obtener_o_crear(
                    request.cookies.get("navira_demo_session")
                )
            except LimiteSesionesDemo as error:
                return JSONResponse(
                    status_code=429,
                    content={"detail": str(error)},
                    headers={"Retry-After": "30"},
                )
            request.state.control_demo_publico = control
            response = await call_next(request)
            if token_nuevo is not None:
                fijar_cookie_demo(
                    response,
                    token_nuevo,
                    aplicacion.state.seguridad.cookie_segura,
                    ttl_cookie,
                )
            return response
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

    return ControlSimuladorDemoLocal(
        functools.partial(crear_contexto_demo, ruta_mapa),
        mapa=cargar_mapa(ruta_mapa),
    )


class _SesionDemoPublica:
    """Mundo anónimo por navegador con simulador y juego aislados entre sí."""

    _OPERACIONES_SIMULADOR = frozenset({
        "iniciar", "reiniciar", "iniciar_mundo_operador", "colocar_elemento",
        "iniciar_ronda_reto", "reiniciar_ronda_reto", "pausar", "reanudar",
        "fijar_velocidad",
    })

    def __init__(self, ruta_mapa: str, seguridad: ConfiguracionSeguridad) -> None:
        self._simulador = crear_control_simulador_demo(ruta_mapa)
        self._ruta_mapa = ruta_mapa
        self._seguridad = seguridad
        self._app_juego: FastAPI | None = None
        self._modo_activo = "simulador"

    @property
    def mapa(self):
        return self._simulador.mapa

    def estado(self):
        return self._simulador.estado()

    def __getattr__(self, nombre: str):
        """Delega acciones del tablero y marca qué modo alimenta sus paneles."""

        if nombre not in self._OPERACIONES_SIMULADOR:
            raise AttributeError(nombre)
        operacion = getattr(self._simulador, nombre)

        def ejecutar(*args, **kwargs):
            self._activar_simulador()
            return operacion(*args, **kwargs)

        return ejecutar

    @property
    def consultar_panel(self):
        if self._modo_activo == "juego" and self._app_juego is not None:
            return self._app_juego.state.consultar_panel
        return self._simulador.consultar_panel

    @property
    def decidir_paso(self):
        if self._modo_activo == "juego" and self._app_juego is not None:
            return self._app_juego.state.decidir_paso
        return self._simulador.decidir_paso

    @property
    def unirse_juego(self):
        self._activar_juego()
        return _UnirsePublicoConReloj(
            self._app_juego.state.unirse_juego,
            self._app_juego.state.reloj_juego,
        )

    @property
    def consultar_sesion_juego(self):
        self._activar_juego()
        return self._app_juego.state.consultar_sesion_juego

    @property
    def registrar_orden_juego(self):
        self._activar_juego()
        return self._app_juego.state.registrar_orden_juego

    def _activar_simulador(self) -> None:
        if self._modo_activo == "juego" and self._app_juego is not None:
            self._app_juego.state.reloj_juego.detener()
        self._modo_activo = "simulador"

    def _activar_juego(self) -> None:
        self._modo_activo = "juego"
        if self._app_juego is None:
            self._app_juego = crear_app_juego_demo(
                ruta_mapa=self._ruta_mapa,
                seguridad=self._seguridad,
            )

    def cerrar(self) -> None:
        if self._app_juego is not None:
            self._app_juego.state.reloj_juego.detener()
        self._simulador.cerrar()


class _UnirsePublicoConReloj:
    """Arranca el reloj del juego solo después de que el jugador aparece."""

    def __init__(self, servicio, reloj) -> None:
        self._servicio = servicio
        self._reloj = reloj

    def ejecutar(self, token: str | None):
        resultado = self._servicio.ejecutar(token)
        if self._reloj is not None:
            self._reloj.iniciar()
        return resultado


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
        control_demo_publico=os.environ.get("NAVIRA_PUBLIC_DEMO_CONTROL") == "1",
    )

    if seguridad.control_demo_publico:
        mapa = os.environ.get("NAVIRA_DEMO_MAP", str(MAPA_MANTA_POR_DEFECTO))
        max_sesiones = int(os.environ.get("NAVIRA_PUBLIC_MAX_SESSIONS", "3"))
        ttl_sesion = float(os.environ.get("NAVIRA_PUBLIC_SESSION_IDLE_SECONDS", "10800"))
        sesiones = RegistroSesionesDemoMemoria(
            lambda: _SesionDemoPublica(mapa, seguridad),
            max_sesiones=max_sesiones,
            inactividad_segundos=ttl_sesion,
        )
        return crear_app(
            sesiones_demo_publicas=sesiones,
            seguridad=seguridad,
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
