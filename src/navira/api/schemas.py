"""Esquemas de transporte para el contrato HTTP obligatorio."""

from pydantic import BaseModel, ConfigDict, Field


class SolicitudPasoSchema(BaseModel):
    """Cuerpo exacto solicitado por el simulador para POST /paso."""

    model_config = ConfigDict(extra="forbid")

    sobrevivienteId: str = Field(min_length=1)
    nodoActual: str = Field(min_length=1)
    turno: int = Field(ge=0)


class RespuestaPasoSchema(BaseModel):
    """Respuesta de éxito: un único destino siguiente."""

    model_config = ConfigDict(extra="forbid")

    siguienteNodo: str = Field(min_length=1)
