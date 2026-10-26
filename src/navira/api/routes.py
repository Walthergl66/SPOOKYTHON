"""Rutas HTTP de la primera fase de Navira."""

from fastapi import APIRouter, Depends

from navira.api.auth import validar_api_key
from navira.api.schemas import RespuestaPasoSchema, SolicitudPasoSchema
from navira.application.decidir_paso import DecidirPaso, SolicitudPaso

router = APIRouter()
_decidir_paso = DecidirPaso()


@router.get("/salud", tags=["operación"])
async def salud() -> dict[str, str]:
    """Indica que el proceso HTTP está activo; no valida dependencias externas."""

    return {"estado": "activo", "servicio": "navira"}


@router.post(
    "/paso",
    response_model=RespuestaPasoSchema,
    tags=["motor"],
    dependencies=[Depends(validar_api_key)],
)
async def paso(solicitud: SolicitudPasoSchema) -> RespuestaPasoSchema:
    """Devuelve el destino siguiente con el contrato requerido por el reto."""

    decision = _decidir_paso.ejecutar(
        SolicitudPaso(
            sobreviviente_id=solicitud.sobrevivienteId,
            nodo_actual=solicitud.nodoActual,
            turno=solicitud.turno,
        )
    )
    return RespuestaPasoSchema(siguienteNodo=decision.siguiente_nodo)
