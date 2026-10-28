"""Negociación sencilla de gzip para respuestas HTTP grandes."""

from __future__ import annotations


def cliente_acepta_gzip(cabecera: str) -> bool:
    """Acepta gzip solo cuando su calidad explícita es mayor que cero."""

    for valor in cabecera.split(","):
        partes = [parte.strip() for parte in valor.split(";")]
        if not partes or partes[0].lower() != "gzip":
            continue
        calidad = next(
            (parte[2:] for parte in partes[1:] if parte.lower().startswith("q=")),
            "1",
        )
        try:
            return 0 < float(calidad) <= 1
        except ValueError:
            return False
    return False
