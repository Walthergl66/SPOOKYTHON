"""Rutas HTTP de la primera fase de Navira."""

import asyncio
from datetime import datetime, timezone
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, status

from navira.api import dependencias as deps
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
    SolicitudIniciarDemoSchema,
)
from navira.api.seguridad import (
    COOKIE_SESION_JUGADOR,
    borrar_cookie_sesion,
    exigir_operador_local,
    fijar_cookie_sesion,
    origen_mismo_host,
)
from navira.domain.mapa import Refugio, nodos_elegibles_refugio
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
    EntidadNoEncontrada,
    PartidaNoDisponible,
    PasoIncompatible,
    SolicitudPaso,
)

router = APIRouter()
_PANEL_WS_INTERVAL_SECONDS = 0.25
_PANEL_WS_HEARTBEAT_SECONDS = 2.0


def _error(codigo: int, error: Exception, headers: dict[str, str] | None = None) -> HTTPException:
    return HTTPException(status_code=codigo, detail=str(error), headers=headers)


def _sesion_expirada(request: Request, response: Response, error: Exception) -> HTTPException:
    """410 con la cookie vencida borrada en las cabeceras de la respuesta de error."""

    borrar_cookie_sesion(response, request.app.state.seguridad.cookie_segura)
    return _error(status.HTTP_410_GONE, error, dict(response.headers))


@router.get("/demo/simulador", tags=["demo local"])
async def estado_demo_simulador(request: Request) -> dict[str, object]:
    """Describe el control de simulador cuando el proceso lo habilita en localhost."""

    gestor = _control_demo_local(request)
    exigir_operador_local(request, exigir_origen=False)
    return gestor.estado()


@router.get("/demo/simulador/candidatos", tags=["demo local"])
async def candidatos_demo_simulador(request: Request) -> dict[str, object]:
    """Nodos elegibles para refugio, calles y refugios por defecto del mapa del simulador."""

    gestor = _control_demo_local(request)
    exigir_operador_local(request, exigir_origen=False)
    mapa = gestor.mapa
    if mapa is None:
        raise HTTPException(status_code=404, detail="El control local no expone un mapa.")
    return {
        "version": mapa.version,
        "nodos": [{"id": n.id, "lat": n.lat, "lng": n.lng} for n in nodos_elegibles_refugio(mapa)],
        "calles": [{"origen": c.origen, "destino": c.destino} for c in mapa.calles],
        "refugios": [{"id": r.id, "nodo": r.nodo} for r in mapa.refugios],
    }


def _refugios(solicitud: SolicitudIniciarDemoSchema) -> tuple[Refugio, ...] | None:
    """Refugios elegidos por el operador; None conserva los del mapa."""

    if solicitud.refugios is None:
        return None
    return tuple(Refugio(r.id, r.nodo) for r in solicitud.refugios)


@router.post("/demo/simulador/iniciar", tags=["demo local"])
async def iniciar_demo_simulador(
    solicitud: SolicitudIniciarDemoSchema,
    request: Request,
) -> dict[str, object]:
    gestor = _control_demo_local(request)
    exigir_operador_local(request)
    try:
        return gestor.iniciar(
            escenario=solicitud.escenario,
            cantidad_sobrevivientes=solicitud.sobrevivientes,
            intensidad=solicitud.intensidad,
            eventos_ciudad=solicitud.eventosCiudad,
            semilla=solicitud.semilla,
            refugios=_refugios(solicitud),
        )
    except (OSError, ValueError) as error:
        raise _error(422, error) from error


@router.post("/demo/simulador/pausar", tags=["demo local"])
async def pausar_demo_simulador(request: Request) -> dict[str, object]:
    gestor = _control_demo_local(request)
    exigir_operador_local(request)
    try:
        return gestor.pausar()
    except RuntimeError as error:
        raise _error(409, error) from error


@router.post("/demo/simulador/reanudar", tags=["demo local"])
async def reanudar_demo_simulador(request: Request) -> dict[str, object]:
    gestor = _control_demo_local(request)
    exigir_operador_local(request)
    try:
        return gestor.reanudar()
    except RuntimeError as error:
        raise _error(409, error) from error


@router.post("/demo/simulador/reiniciar", tags=["demo local"])
async def reiniciar_demo_simulador(
    solicitud: SolicitudIniciarDemoSchema,
    request: Request,
) -> dict[str, object]:
    gestor = _control_demo_local(request)
    exigir_operador_local(request)
    try:
        return gestor.reiniciar(
            escenario=solicitud.escenario,
            cantidad_sobrevivientes=solicitud.sobrevivientes,
            intensidad=solicitud.intensidad,
            eventos_ciudad=solicitud.eventosCiudad,
            refugios=_refugios(solicitud),
        )
    except (OSError, ValueError) as error:
        raise _error(422, error) from error


@router.get("/", tags=["operación"])
async def inicio() -> dict[str, str]:
    """Respuesta de comprobación al abrir el backend en el navegador."""

    print("Navira backend OK: / accedido.", flush=True)
    return {"mensaje": "Navira backend OK", "servicio": "navira", "salud": "/salud"}


@router.get("/salud", tags=["operación"])
async def salud() -> dict[str, str]:
    """Indica que el proceso HTTP está activo; no valida dependencias externas."""

    print("Navira backend OK: /salud accedido.", flush=True)
    return {"estado": "activo", "servicio": "navira"}


@router.get("/panel/estado", response_model=RespuestaEstadoPanelSchema, tags=["panel"])
async def estado_panel(
    consulta: ConsultarPanel | None = Depends(deps.consulta_panel),
) -> dict[str, object]:
    """Lee snapshot confirmado con filtrado de zombies ocultos."""

    if consulta is None:
        return {"estado": "sin_partida"}
    try:
        return consulta.consultar_estado()
    except PanelNoDisponible as error:
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, error) from error


@router.get("/panel/mapa", response_model=RespuestaMapaPanelSchema, tags=["panel"])
async def mapa_panel(
    consulta: ConsultarPanel | None = Depends(deps.consulta_panel),
) -> dict[str, object]:
    """Lee el grafo de la versión asociada a la partida activa."""

    if consulta is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No hay mapa activo.")
    try:
        return consulta.consultar_mapa()
    except PanelNoDisponible as error:
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, error) from error


@router.post(
    "/juego/unirse",
    response_model=RespuestaUnirseJuegoSchema,
    tags=["juego"],
)
async def unirse_juego(
    request: Request,
    response: Response,
    servicio: UnirseAJuego | None = Depends(deps.unirse_juego),
) -> dict[str, object]:
    """Crea/recupera la única sesión humana con cookie opaca HttpOnly."""

    if not origen_mismo_host(request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origen no permitido.")
    if servicio is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modo de juego no está habilitado en esta instancia.",
        )
    try:
        resultado = servicio.ejecutar(request.cookies.get(COOKIE_SESION_JUGADOR))
    except SesionExpirada as error:
        raise _sesion_expirada(request, response, error) from error
    except PropietarioOcupado as error:
        raise _error(status.HTTP_409_CONFLICT, error) from error
    except AparicionNoDisponible as error:
        raise _error(status.HTTP_409_CONFLICT, error) from error
    except JuegoNoDisponible as error:
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, error) from error

    fijar_cookie_sesion(response, resultado.token, request.app.state.seguridad.cookie_segura)
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
async def recuperar_sesion_juego(
    request: Request,
    response: Response,
    servicio: ConsultarSesionJuego | None = Depends(deps.consultar_sesion_juego),
) -> dict[str, object]:
    """Lee la sesión ya asociada a la cookie; nunca reserva personaje nuevo."""

    response.headers["Cache-Control"] = "no-store"
    if servicio is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La recuperación del modo juego no está habilitada.",
        )
    try:
        actual = servicio.ejecutar(request.cookies.get(COOKIE_SESION_JUGADOR))
    except SesionExpirada as error:
        raise _sesion_expirada(request, response, error) from error
    except SesionNoEncontrada as error:
        raise _error(status.HTTP_403_FORBIDDEN, error) from error
    except JuegoNoDisponible as error:
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, error) from error

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
    servicio: RegistrarOrdenHumana | None = Depends(deps.registrar_orden_juego),
) -> dict[str, object]:
    """Acepta/repite una orden del propietario sin mover el mundo."""

    if not origen_mismo_host(request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origen no permitido.")
    if servicio is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El registro de órdenes del modo juego no está habilitado.",
        )
    try:
        orden = servicio.ejecutar(
            request.cookies.get(COOKIE_SESION_JUGADOR),
            run_id=solicitud.runId,
            turno=solicitud.turno,
            personaje_id=solicitud.personajeId,
            siguiente_nodo=solicitud.siguienteNodo,
            accion_id=solicitud.accionId,
        )
    except SesionExpirada as error:
        raise _sesion_expirada(request, response, error) from error
    except SesionNoAutorizada as error:
        raise _error(status.HTTP_403_FORBIDDEN, error) from error
    except (OrdenIdempotenciaConflict, OrdenIncompatible) as error:
        raise _error(status.HTTP_409_CONFLICT, error) from error

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

    if not origen_mismo_host(websocket):
        await websocket.close(code=1008, reason="Origen no permitido")
        return

    await websocket.accept()
    ultima_clave: tuple[str, int] | None | object = object()
    ultimo_latido = monotonic()
    try:
        while True:
            # The local demo swaps its in-memory game context when a new run starts.
            # Resolve the panel each poll so an open socket follows that new run.
            consulta = deps.consulta_panel(websocket)
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


def _control_demo_local(request: Request):
    """Evita registrar controles operativos en el ensamblaje normal."""

    if not request.app.state.seguridad.control_demo_local:
        raise HTTPException(status_code=404, detail="El control local de demo está deshabilitado.")
    gestor = request.app.state.control_simulador_demo
    if gestor is None:
        raise HTTPException(status_code=404, detail="El control local de demo está deshabilitado.")
    return gestor


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
async def paso(
    solicitud: SolicitudPasoSchema,
    servicio=Depends(deps.decidir_paso),
) -> RespuestaPasoSchema:
    """Devuelve el siguiente destino usando el servicio ensamblado por la app."""

    try:
        decision = servicio.ejecutar(
            SolicitudPaso(
                sobreviviente_id=solicitud.sobrevivienteId,
                nodo_actual=solicitud.nodoActual,
                turno=solicitud.turno,
            )
        )
    except EntidadNoEncontrada as error:
        raise _error(status.HTTP_404_NOT_FOUND, error) from error
    except PasoIncompatible as error:
        raise _error(status.HTTP_409_CONFLICT, error) from error
    except PartidaNoDisponible as error:
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, error) from error
    return RespuestaPasoSchema(siguienteNodo=decision.siguiente_nodo)
