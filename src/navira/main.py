"""Punto de ensamblaje de la aplicación ASGI."""

from fastapi import FastAPI

from navira.api.routes import router

app = FastAPI(
    title="Navira",
    description="Motor de evacuación dinámica para Escape de Manta Zombie.",
    version="0.1.0",
)
app.include_router(router)
