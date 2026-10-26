"""Caso de uso mínimo del contrato de recomendación."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SolicitudPaso:
    """Datos del sobreviviente recibidos para una decisión."""

    sobreviviente_id: str
    nodo_actual: str
    turno: int


@dataclass(frozen=True, slots=True)
class DecisionPaso:
    """Destino propuesto; repetir la solicitud produce el mismo resultado."""

    siguiente_nodo: str


class DecidirPaso:
    """Devuelve una espera legal hasta integrar mapa y política de rutas.

    El mismo nodo está permitido por el contrato oficial. Esta política de
    arranque mantiene el endpoint seguro y determinista; no afirma que la
    posición sea segura y será reemplazada por el planificador de P2.
    """

    def ejecutar(self, solicitud: SolicitudPaso) -> DecisionPaso:
        return DecisionPaso(siguiente_nodo=solicitud.nodo_actual)
