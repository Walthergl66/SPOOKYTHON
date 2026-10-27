"""Autenticación de servicio para rutas del simulador."""

import hmac

from fastapi import Header, HTTPException, Request, status


async def validar_api_key(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    """Compara la clave de servicio sin filtrar diferencias de tiempo.

    Si falta configuración, la API falla cerrada con 503 en vez de exponer
    accidentalmente un endpoint sin autenticación.
    """

    clave_configurada = request.app.state.seguridad.api_key
    if not clave_configurada:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticación de servicio no configurada.",
        )

    clave_recibida = x_api_key.encode("utf-8") if x_api_key is not None else b""
    clave_esperada = clave_configurada.encode("utf-8")
    if not hmac.compare_digest(clave_recibida, clave_esperada):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial de servicio inválida.",
        )
