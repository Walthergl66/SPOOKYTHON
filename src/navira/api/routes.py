"""Rutas HTTP de la primera fase de Navira."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from navira.api.auth import validar_api_key
from navira.api.schemas import (
    RespuestaEstadoPanelSchema,
    RespuestaMapaPanelSchema,
    RespuestaPasoSchema,
    SolicitudPasoSchema,
)
from navira.application.consultar_panel import ConsultarPanel, PanelNoDisponible
from navira.application.decidir_paso import (
    DecidirPasoEspera,
    EntidadNoEncontrada,
    PartidaNoDisponible,
    PasoIncompatible,
    SolicitudPaso,
)

router = APIRouter()


@router.get("/salud", tags=["operación"])
async def salud() -> dict[str, str]:
    """Indica que el proceso HTTP está activo; no valida dependencias externas."""

    return {"estado": "activo", "servicio": "navira"}


@router.get("/panel/estado", response_model=RespuestaEstadoPanelSchema, tags=["panel"])
async def estado_panel(request: Request) -> dict[str, object]:
    """Lee snapshot confirmado con filtrado de zombies ocultos."""

    consulta: ConsultarPanel | None = getattr(request.app.state, "consultar_panel", None)
    if consulta is None:
        return {"estado": "sin_partida"}
    try:
        return consulta.consultar_estado()
    except PanelNoDisponible as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


@router.get("/panel/mapa", response_model=RespuestaMapaPanelSchema, tags=["panel"])
async def mapa_panel(request: Request) -> dict[str, object]:
    """Lee el grafo de la versión asociada a la partida activa."""

    consulta: ConsultarPanel | None = getattr(request.app.state, "consultar_panel", None)
    if consulta is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No hay mapa activo.")
    try:
        return consulta.consultar_mapa()
    except PanelNoDisponible as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


@router.post(
    "/paso",
    response_model=RespuestaPasoSchema,
    tags=["motor"],
    dependencies=[Depends(validar_api_key)],
)
async def paso(solicitud: SolicitudPasoSchema, request: Request) -> RespuestaPasoSchema:
    """Devuelve el siguiente destino usando el servicio ensamblado por la app."""

    servicio = getattr(request.app.state, "decidir_paso", None) or DecidirPasoEspera()
    try:
        decision = servicio.ejecutar(
            SolicitudPaso(
                sobreviviente_id=solicitud.sobrevivienteId,
                nodo_actual=solicitud.nodoActual,
                turno=solicitud.turno,
            )
        )
    except EntidadNoEncontrada as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except PasoIncompatible as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except PartidaNoDisponible as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    return RespuestaPasoSchema(siguienteNodo=decision.siguiente_nodo)
