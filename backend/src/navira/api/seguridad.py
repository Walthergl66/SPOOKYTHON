"""Guardas de transporte: cookie de sesión humana y restricciones de operador local."""

import ipaddress
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from fastapi import HTTPException, Request, Response
from starlette.requests import HTTPConnection

COOKIE_SESION_JUGADOR = "navira_player_session"
HOSTS_LOOPBACK = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class ConfiguracionSeguridad:
    """Configuración de transporte leída una vez en el ensamblaje; el valor por defecto es el más cerrado."""

    api_key: str | None = field(default=None, repr=False)
    cookie_segura: bool = True
    control_demo_local: bool = False


def fijar_cookie_sesion(response: Response, token: str, secure: bool) -> None:
    response.set_cookie(
        key=COOKIE_SESION_JUGADOR,
        value=token,
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/juego",
    )


def borrar_cookie_sesion(response: Response, secure: bool) -> None:
    """Retira del navegador una cookie vencida para permitir futuras partidas."""

    response.delete_cookie(
        key=COOKIE_SESION_JUGADOR,
        path="/juego",
        httponly=True,
        secure=secure,
        samesite="strict",
    )


def exigir_operador_local(request: Request, *, exigir_origen: bool = True) -> None:
    """Restringe el control efímero a localhost y al origen del navegador."""

    cliente = request.client.host if request.client is not None else ""
    try:
        es_loopback = ipaddress.ip_address(cliente).is_loopback
    except ValueError:
        es_loopback = False
    host = request.url.hostname
    if not es_loopback or host not in HOSTS_LOOPBACK:
        raise HTTPException(status_code=403, detail="El control de demo solo acepta conexiones locales.")
    if exigir_origen and not origen_local_mismo_host(request):
        raise HTTPException(status_code=403, detail="Origen no permitido.")


def origen_local_mismo_host(request: Request) -> bool:
    """Compara hostname sin puerto, porque el proxy Vite cambia el puerto."""

    origen = request.headers.get("origin")
    host = request.headers.get("host")
    if not origen or not host:
        return False
    try:
        partes_origen = urlsplit(origen)
        hostname_request = urlsplit(f"//{host}").hostname
    except ValueError:
        return False
    return (
        partes_origen.scheme in {"http", "https"}
        and partes_origen.hostname is not None
        and hostname_request is not None
        and partes_origen.hostname.casefold() in HOSTS_LOOPBACK
        and hostname_request.casefold() in HOSTS_LOOPBACK
    )


def origen_mismo_host(conexion: HTTPConnection) -> bool:
    """Compara netloc completo de Origin y Host; vale para Request y WebSocket."""

    origen = conexion.headers.get("origin")
    host = conexion.headers.get("host")
    if not origen or not host:
        return False
    try:
        partes = urlsplit(origen)
    except ValueError:
        return False
    return partes.scheme in {"http", "https"} and partes.netloc.casefold() == host.casefold()
