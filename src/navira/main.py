"""Punto de ensamblaje de la aplicación ASGI."""

from fastapi import FastAPI

from navira.api.routes import router
from navira.application.decidir_paso import DecidirPasoEspera


def crear_app(servicio_decision=None) -> FastAPI:
    """Ensamblaje inyectable; el proceso base espera si no recibe estado/mapa."""

    aplicacion = FastAPI(
        title="Navira",
        description="Motor de evacuación dinámica para Escape de Manta Zombie.",
        version="0.1.0",
    )
    aplicacion.state.decidir_paso = servicio_decision or DecidirPasoEspera()
    aplicacion.include_router(router)
    return aplicacion


app = crear_app()
