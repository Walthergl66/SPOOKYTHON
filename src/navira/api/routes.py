"""Rutas HTTP de la primera fase de Navira."""

import asyncio
import os
from datetime import datetime, timezone
from time import monotonic
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, status

from navira.api.auth import validar_api_key
from navira.api.schemas import (
    RespuestaEstadoPanelSchema,
    RespuestaMapaPanelSchema,
    RespuestaOrdenJuegoSchema,
    RespuestaPasoSchema,
    RespuestaSesionJuegoSchema,
    RespuestaUnirseJuegoSchema,
    SolicitudOrdenJuegoSchema,
    SolicitudPasoSchema,
)
from navira.application.consultar_panel import ConsultarPanel, PanelNoDisponible
from navira.application.juego import (
    AparicionNoDisponible,
    ConsultarSesionJuego,
    JuegoNoDisponible,
    PropietarioOcupado,
    SesionExpirada,
    SesionNoEncontrada,
    UnirseAJuego,
)
from navira.application.ordenes import (
    OrdenIdempotenciaConflict,
    OrdenIncompatible,
    RegistrarOrdenHumana,
    SesionNoAutorizada,
)
from navira.application.decidir_paso import (
    DecidirPasoEspera,
    EntidadNoEncontrada,
    PartidaNoDisponible,
    PasoIncompatible,
    SolicitudPaso,
)

router = APIRouter()
_PANEL_WS_INTERVAL_SECONDS = 0.25
_PANEL_WS_HEARTBEAT_SECONDS = 2.0
_COOKIE_SESION_JUGADOR = "navira_player_session"


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
    "/juego/unirse",
    response_model=RespuestaUnirseJuegoSchema,
    tags=["juego"],
)
async def unirse_juego(request: Request, response: Response) -> dict[str, object]:
    """Crea/recupera la única sesión humana con cookie opaca HttpOnly."""

    if not _origen_request_mismo_host(request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origen no permitido.")
    servicio: UnirseAJuego | None = getattr(request.app.state, "unirse_juego", None)
    if servicio is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modo de juego no está habilitado en esta instancia.",
        )
    try:
        resultado = servicio.ejecutar(request.cookies.get(_COOKIE_SESION_JUGADOR))
    except SesionExpirada as error:
        _borrar_cookie_sesion(response)
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=str(error),
            headers=dict(response.headers),
        ) from error
    except PropietarioOcupado as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except AparicionNoDisponible as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except JuegoNoDisponible as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error

    response.set_cookie(
        key=_COOKIE_SESION_JUGADOR,
        value=resultado.token,
        httponly=True,
        secure=os.getenv("NAVIRA_COOKIE_SECURE", "1") != "0",
        samesite="strict",
        path="/juego",
    )
    return {
        "runId": resultado.sesion.run_id,
        "jugadorId": resultado.sesion.sobreviviente_id,
        "estado": resultado.sesion.estado.value,
        "nodo": resultado.sesion.nodo,
    }


@router.get(
    "/juego/mi-personaje",
    response_model=RespuestaSesionJuegoSchema,
    tags=["juego"],
)
async def recuperar_sesion_juego(request: Request, response: Response) -> dict[str, object]:
    """Lee la sesión ya asociada a la cookie; nunca reserva personaje nuevo."""

    response.headers["Cache-Control"] = "no-store"
    servicio: ConsultarSesionJuego | None = getattr(
        request.app.state, "consultar_sesion_juego", None
    )
    if servicio is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La recuperación del modo juego no está habilitada.",
        )
    try:
        actual = servicio.ejecutar(request.cookies.get(_COOKIE_SESION_JUGADOR))
    except SesionExpirada as error:
        _borrar_cookie_sesion(response)
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=str(error),
            headers=dict(response.headers),
        ) from error
    except SesionNoEncontrada as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except JuegoNoDisponible as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error

    orden = actual.ultima_orden
    return {
        "runId": actual.sesion.run_id,
        "jugadorId": actual.sesion.sobreviviente_id,
        "estado": actual.sesion.estado.value,
        "nodo": actual.nodo,
        "estadoPersonaje": actual.estado_personaje,
        "ultimaOrden": {
            "accionId": orden.accion_id,
            "turno": orden.turno,
            "siguienteNodo": orden.siguiente_nodo,
            "secuencia": orden.secuencia,
        } if orden is not None else None,
    }


@router.post(
    "/juego/accion",
    response_model=RespuestaOrdenJuegoSchema,
    tags=["juego"],
)
async def registrar_accion_juego(
    solicitud: SolicitudOrdenJuegoSchema,
    request: Request,
    response: Response,
) -> dict[str, object]:
    """Acepta/repite una orden del propietario sin mover el mundo."""

    if not _origen_request_mismo_host(request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origen no permitido.")
    servicio: RegistrarOrdenHumana | None = getattr(request.app.state, "registrar_orden_juego", None)
    if servicio is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El registro de órdenes del modo juego no está habilitado.",
        )
    try:
        orden = servicio.ejecutar(
            request.cookies.get(_COOKIE_SESION_JUGADOR),
            run_id=solicitud.runId,
            turno=solicitud.turno,
            personaje_id=solicitud.personajeId,
            siguiente_nodo=solicitud.siguienteNodo,
            accion_id=solicitud.accionId,
        )
    except SesionExpirada as error:
        _borrar_cookie_sesion(response)
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=str(error),
            headers=dict(response.headers),
        ) from error
    except SesionNoAutorizada as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except (OrdenIdempotenciaConflict, OrdenIncompatible) as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    return {
        "accionId": orden.accion_id,
        "secuencia": orden.secuencia,
        "estado": "recibida",
        "turno": orden.turno,
    }


@router.websocket("/ws/panel")
async def observar_panel(websocket: WebSocket) -> None:
    """Envía snapshots observables completos al cambiar la versión confirmada.

    La conexión es de solo lectura. Cada conexión recibe el estado vigente antes
    de esperar nuevos cambios, por lo que un cliente que reconecta no necesita
    reproducir deltas perdidos.
    """

    if not _origen_mismo_host(websocket):
        await websocket.close(code=1008, reason="Origen no permitido")
        return

    await websocket.accept()
    consulta: ConsultarPanel | None = getattr(websocket.app.state, "consultar_panel", None)
    ultima_clave: tuple[str, int] | None | object = object()
    ultimo_latido = monotonic()
    try:
        while True:
            clave = _clave_panel(consulta)
            if clave != ultima_clave:
                estado = consulta.consultar_estado() if consulta is not None else {"estado": "sin_partida"}
                evento = _evento_snapshot(estado)
                await websocket.send_json(evento)
                ultima_clave = _clave_evento(evento)
                ultimo_latido = monotonic()
            elif monotonic() - ultimo_latido >= _PANEL_WS_HEARTBEAT_SECONDS:
                evento = _evento_latido(ultima_clave)
                await websocket.send_json(evento)
                ultimo_latido = monotonic()

            try:
                # La recepción acotada detecta cierres del cliente y limita la
                # demora máxima antes de observar una transición confirmada.
                mensaje = await asyncio.wait_for(
                    websocket.receive_text(), timeout=_PANEL_WS_INTERVAL_SECONDS
                )
            except TimeoutError:
                continue
            if mensaje:
                await websocket.close(code=1008, reason="Canal de solo lectura")
                return
    except WebSocketDisconnect:
        return
    except PanelNoDisponible:
        await websocket.close(code=1011, reason="Proyección temporalmente no disponible")


def _origen_mismo_host(websocket: WebSocket) -> bool:
    """Rechaza handshakes de navegador cross-origin para el canal público."""

    origen = websocket.headers.get("origin")
    host = websocket.headers.get("host")
    if not origen or not host:
        return False
    try:
        partes = urlsplit(origen)
    except ValueError:
        return False
    return partes.scheme in {"http", "https"} and partes.netloc.casefold() == host.casefold()


def _borrar_cookie_sesion(response: Response) -> None:
    """Retira del navegador una cookie vencida para permitir futuras partidas."""

    response.delete_cookie(
        key=_COOKIE_SESION_JUGADOR,
        path="/juego",
        httponly=True,
        secure=os.getenv("NAVIRA_COOKIE_SECURE", "1") != "0",
        samesite="strict",
    )


def _origen_request_mismo_host(request: Request) -> bool:
    """Protege la creación de sesión basada en cookie contra solicitudes cross-origin."""

    origen = request.headers.get("origin")
    host = request.headers.get("host")
    if not origen or not host:
        return False
    try:
        partes = urlsplit(origen)
    except ValueError:
        return False
    return partes.scheme in {"http", "https"} and partes.netloc.casefold() == host.casefold()


def _clave_panel(consulta: ConsultarPanel | None) -> tuple[str, int] | None:
    if consulta is None:
        return None
    return consulta.version_estado()


def _evento_snapshot(estado: dict[str, object]) -> dict[str, object]:
    """Enmarca estado completo; la versión del snapshot es cursor por partida."""

    activa = estado.get("estado") == "activa"
    return {
        "schemaVersion": 1,
        "tipo": "panel.snapshot",
        "runId": estado.get("runId") if activa else None,
        "secuencia": estado.get("snapshotVersion") if activa else 0,
        "turno": estado.get("turno") if activa else None,
        "fase": estado.get("fase") if activa else "sin_partida",
        "emitidoEn": _ahora_utc(),
        "datos": estado,
    }


def _evento_latido(clave: tuple[str, int] | None | object) -> dict[str, object]:
    run_id, secuencia = clave if isinstance(clave, tuple) else (None, 0)
    return {
        "schemaVersion": 1,
        "tipo": "panel.latido",
        "runId": run_id,
        "secuencia": secuencia,
        "emitidoEn": _ahora_utc(),
    }


def _clave_evento(evento: dict[str, object]) -> tuple[str, int] | None:
    run_id, secuencia = evento["runId"], evento["secuencia"]
    if not isinstance(run_id, str) or not isinstance(secuencia, int):
        return None
    return run_id, secuencia


def _ahora_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
