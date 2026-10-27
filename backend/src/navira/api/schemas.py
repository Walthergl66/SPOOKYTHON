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


class RespuestaUnirseJuegoSchema(BaseModel):
    """Resultado de la sesión propietaria sin exponer estado del mundo privado."""

    model_config = ConfigDict(extra="forbid")

    runId: str
    jugadorId: str
    estado: Literal["esperando_aparicion", "activo"]
    nodo: str | None = None


class UltimaOrdenSesionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accionId: str
    turno: int = Field(ge=0)
    siguienteNodo: str
    secuencia: int = Field(ge=1)


class RespuestaSesionJuegoSchema(BaseModel):
    """Snapshot mínimo para que la cookie recupere únicamente su personaje."""

    model_config = ConfigDict(extra="forbid")

    runId: str
    jugadorId: str
    estado: Literal["esperando_aparicion", "activo"]
    nodo: str | None = None
    estadoPersonaje: Literal["activo", "mordido", "evacuado"] | None = None
    ultimaOrden: UltimaOrdenSesionSchema | None = None


class SolicitudOrdenJuegoSchema(BaseModel):
    """Orden del jugador; la identidad se contrasta con la cookie propietaria."""

    model_config = ConfigDict(extra="forbid")

    runId: str = Field(min_length=1, max_length=128)
    turno: int = Field(ge=0)
    personajeId: str = Field(min_length=1, max_length=128)
    siguienteNodo: str = Field(min_length=1, max_length=128)
    accionId: str = Field(min_length=1, max_length=128)


class RespuestaOrdenJuegoSchema(BaseModel):
    """Acuse de recepción; no representa un movimiento confirmado."""

    model_config = ConfigDict(extra="forbid")

    accionId: str
    secuencia: int = Field(ge=1)
    estado: Literal["recibida"]
    turno: int = Field(ge=0)


class RefugioDemoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    nodo: str


class SolicitudIniciarDemoSchema(BaseModel):
    """Configuración pública y sintética de una demo operada en localhost."""

    model_config = ConfigDict(extra="forbid")

    escenario: Literal["libre", "caminantes", "mixto", "horda"] = "mixto"
    sobrevivientes: int = Field(default=20, ge=1, le=200)
    semilla: int | None = Field(default=None, ge=0)
    intensidad: Literal["baja", "media", "alta"] = "media"
    eventosCiudad: bool = True
    refugios: list[RefugioDemoSchema] | None = None


class SolicitudVelocidadDemoSchema(BaseModel):
    """Factor de velocidad del reloj de simulación; solo los valores que ofrece el panel."""

    model_config = ConfigDict(extra="forbid")

    velocidad: Literal[1, 2, 4]


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


class EventoCiudadPanelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    turno: int = Field(ge=0)
    causa: str


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
    mordidos: int = Field(ge=0)
    mordidosUltimoTurno: int = Field(ge=0)
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
    decisionRestanteMs: int | None = Field(default=None, ge=0)
    mapVersion: str
    snapshotVersion: int
    zombies: list[ZombiePanelSchema]
    movimientosZombies: list[MovimientoZombiePanelSchema]
    sobrevivientes: list[SobrevivientePanelSchema]
    rutasPrevistas: list[RutaPrevistaPanelSchema]
    aristasBloqueadas: list[str]
    segmentosBloqueados: list[str]
    nodosHorda: list[str]
    eventosCiudad: list[EventoCiudadPanelSchema]
    metricas: MetricasPanelSchema


RespuestaEstadoPanelSchema = PanelSinPartidaSchema | PanelPartidaActivaSchema
