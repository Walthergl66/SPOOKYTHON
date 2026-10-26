"""Punto de ensamblaje de la aplicación ASGI."""

import os

from fastapi import FastAPI

from navira.api.routes import router
from navira.application.decidir_paso import DecidirPasoEspera
from navira.application.consultar_panel import ConsultarPanel
from navira.demo import MAPA_DEMO_POR_DEFECTO, crear_contexto_demo


def crear_app(servicio_decision=None, consultar_panel: ConsultarPanel | None = None) -> FastAPI:
    """Ensamblaje inyectable; sin servicio recibe espera determinista."""

    aplicacion = FastAPI(
        title="Navira",
        description="Motor de evacuación dinámica para Escape de Manta Zombie.",
        version="0.1.0",
    )
    aplicacion.state.decidir_paso = servicio_decision or DecidirPasoEspera()
    aplicacion.state.consultar_panel = consultar_panel
    aplicacion.include_router(router)
    return aplicacion


def crear_app_demo(
    *,
    ruta_mapa=MAPA_DEMO_POR_DEFECTO,
    semilla: int | None = None,
    escenario: str = "libre",
    cantidad_sobrevivientes: int = 1,
) -> FastAPI:
    """Arranca explícitamente el mundo sintético local para desarrollo."""

    contexto = crear_contexto_demo(
        ruta_mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=cantidad_sobrevivientes,
    )
    return crear_app(
        contexto.servicio_decision,
        ConsultarPanel(contexto.snapshots, contexto.mapas, contexto.servicio_decision),
    )


def _crear_app_configurada() -> FastAPI:
    """Activa demo solo con opt-in explícito del proceso local."""

    if os.environ.get("NAVIRA_DEMO") == "1":
        mapa = os.environ.get("NAVIRA_DEMO_MAP", str(MAPA_DEMO_POR_DEFECTO))
        valor_semilla = os.environ.get("NAVIRA_DEMO_SEED")
        semilla = int(valor_semilla) if valor_semilla is not None else None
        escenario = os.environ.get("NAVIRA_DEMO_SCENARIO", "libre")
        sobrevivientes = int(os.environ.get("NAVIRA_DEMO_SURVIVORS", "1"))
        return crear_app_demo(
            ruta_mapa=mapa,
            semilla=semilla,
            escenario=escenario,
            cantidad_sobrevivientes=sobrevivientes,
        )
    return crear_app()

app = _crear_app_configurada()
