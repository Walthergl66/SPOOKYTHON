"""Esquemas de transporte para el contrato HTTP obligatorio."""

from typing import Literal

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


class NodoPanelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    lat: float
    lng: float


class CallePanelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    segmentoId: str
    origen: str
    destino: str
    distanciaM: float
    tipo: str


class RefugioPanelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    nodo: str


class RespuestaMapaPanelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    nodos: list[NodoPanelSchema]
    calles: list[CallePanelSchema]
    refugios: list[RefugioPanelSchema]


class ZombiePanelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tipo: str
    nodo: str


class MovimientoZombiePanelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    trayecto: list[str]


class SobrevivientePanelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    nodo: str
    estado: str
    control: str


class RutaPrevistaPanelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sobrevivienteId: str
    trayecto: list[str]


class MetricasPanelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sobrevivientesActivos: int
    mordidos: int
    evacuados: int
    zombiesVisibles: int


class PanelSinPartidaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: Literal["sin_partida"]


class PanelPartidaActivaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: Literal["activa"]
    runId: str
    modo: Literal["simulador", "juego"]
    turno: int
    fase: str
    mapVersion: str
    snapshotVersion: int
    zombies: list[ZombiePanelSchema]
    movimientosZombies: list[MovimientoZombiePanelSchema]
    sobrevivientes: list[SobrevivientePanelSchema]
    rutasPrevistas: list[RutaPrevistaPanelSchema]
    aristasBloqueadas: list[str]
    segmentosBloqueados: list[str]
    nodosHorda: list[str]
    metricas: MetricasPanelSchema


RespuestaEstadoPanelSchema = PanelSinPartidaSchema | PanelPartidaActivaSchema
