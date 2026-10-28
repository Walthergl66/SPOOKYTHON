"""Proveedores para Depends(). No lanzan errores: cada ruta conserva su orden de validación."""

from fastapi import Request
from starlette.requests import HTTPConnection

from navira.application.consultar_panel import ConsultarPanel
from navira.application.decidir_paso import DecidirPasoEspera
from navira.application.juego import ConsultarSesionJuego, UnirseAJuego
from navira.application.ordenes import RegistrarOrdenHumana


def unirse_juego(request: Request) -> UnirseAJuego | None:
    return getattr(request.app.state, "unirse_juego", None)


def consultar_sesion_juego(request: Request) -> ConsultarSesionJuego | None:
    return getattr(request.app.state, "consultar_sesion_juego", None)


def registrar_orden_juego(request: Request) -> RegistrarOrdenHumana | None:
    return getattr(request.app.state, "registrar_orden_juego", None)


def consulta_panel(conexion: HTTPConnection) -> ConsultarPanel | None:
    """Resuelve la proyección actual, incluida la partida local recién creada."""

    consulta = getattr(conexion.app.state, "consultar_panel", None)
    sesiones = getattr(conexion.app.state, "sesiones_demo_publicas", None)
    control_sesion = getattr(conexion.state, "control_demo_publico", None)
    if control_sesion is None and sesiones is not None:
        control_sesion = sesiones.obtener_existente(
            conexion.cookies.get("navira_demo_session")
        )
    if control_sesion is not None:
        return control_sesion.consultar_panel
    gestor = getattr(conexion.app.state, "control_simulador_demo", None)
    return consulta or (gestor.consultar_panel if gestor is not None else None)


def decidir_paso(request: Request):
    sesiones = getattr(request.app.state, "sesiones_demo_publicas", None)
    control_sesion = getattr(request.state, "control_demo_publico", None)
    if control_sesion is None and sesiones is not None:
        control_sesion = sesiones.obtener_existente(
            request.cookies.get("navira_demo_session")
        )
    if control_sesion is not None:
        return control_sesion.decidir_paso
    gestor = getattr(request.app.state, "control_simulador_demo", None)
    return (
        (gestor.decidir_paso if gestor is not None else None)
        or getattr(request.app.state, "decidir_paso", None)
        or DecidirPasoEspera()
    )
