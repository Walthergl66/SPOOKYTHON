"""Punto de ensamblaje de la aplicación ASGI."""

import os

from fastapi import FastAPI

from navira.api.routes import router
from navira.application.decidir_paso import DecidirPasoEspera
from navira.demo import MAPA_DEMO_POR_DEFECTO, crear_servicio_demo


def crear_app(servicio_decision=None) -> FastAPI:
    """Ensamblaje inyectable; sin servicio recibe espera determinista."""

    aplicacion = FastAPI(
        title="Navira",
        description="Motor de evacuación dinámica para Escape de Manta Zombie.",
        version="0.1.0",
    )
    aplicacion.state.decidir_paso = servicio_decision or DecidirPasoEspera()
    aplicacion.include_router(router)
    return aplicacion


def crear_app_demo(
    *,
    ruta_mapa=MAPA_DEMO_POR_DEFECTO,
    semilla: int = 31,
    escenario: str = "libre",
    cantidad_sobrevivientes: int = 1,
) -> FastAPI:
    """Arranca explícitamente el mundo sintético local para desarrollo."""

    return crear_app(
        crear_servicio_demo(
            ruta_mapa,
            semilla=semilla,
            escenario=escenario,
            cantidad_sobrevivientes=cantidad_sobrevivientes,
        )
    )


def _crear_app_configurada() -> FastAPI:
    """Activa demo solo con opt-in explícito del proceso local."""

    if os.environ.get("NAVIRA_DEMO") == "1":
        mapa = os.environ.get("NAVIRA_DEMO_MAP", str(MAPA_DEMO_POR_DEFECTO))
        semilla = int(os.environ.get("NAVIRA_DEMO_SEED", "31"))
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
