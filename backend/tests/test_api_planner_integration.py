"""Contrato HTTP cuando la aplicación se ensambla con estado y grafo."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from navira.adapters.mapas_memoria import CatalogoMapasMemoria
from navira.application.decidir_paso import DecidirPaso
from navira.domain.mapa import Grafo, cargar_mapa
from navira.domain.modelo import EstadoPartida, FaseTurno, ModoPartida, Partida, Sobreviviente
from navira.main import crear_app
from navira.simulation.coordinador import SnapshotMundo


FIXTURE = Path(__file__).parent / "fixtures" / "mapa-minimo.json"


class SnapshotActivo:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def obtener_activa(self):
        return self.snapshot


def crear_cliente(*, snapshot_disponible: bool = True) -> TestClient:
    grafo = Grafo(cargar_mapa(FIXTURE))
    partida = Partida(
        run_id="run-api-route",
        modo=ModoPartida.SIMULADOR,
        escenario="fixture",
        map_version=grafo.mapa.version,
        sobrevivientes=(Sobreviviente("S-1", "N-0001", refugio_objetivo="R-0004"),),
        estado=EstadoPartida.ACTIVA,
        turno=2,
        fase=FaseTurno.DECISIONES,
    )
    snapshot = SnapshotMundo(partida, version=1) if snapshot_disponible else None
    servicio = DecidirPaso(
        SnapshotActivo(snapshot), CatalogoMapasMemoria((grafo,))
    )
    return TestClient(crear_app(servicio))


class ApiPlannerIntegrationTests(unittest.TestCase):
    def test_paso_con_estado_devuelve_ruta_y_conserva_cuerpo(self) -> None:
        cliente = crear_cliente()
        with patch.dict(os.environ, {"NAVIRA_API_KEY": "clave-prueba"}, clear=True):
            respuesta = cliente.post(
                "/paso",
                headers={"x-api-key": "clave-prueba"},
                json={"sobrevivienteId": "S-1", "nodoActual": "N-0001", "turno": 2},
            )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"siguienteNodo": "N-0002"})

    def test_estado_incompatible_y_ausente_tienen_errores_del_contrato(self) -> None:
        cliente = crear_cliente()
        cliente_sin_estado = crear_cliente(snapshot_disponible=False)
        headers = {"x-api-key": "clave-prueba"}
        solicitud = {"sobrevivienteId": "S-1", "nodoActual": "N-0001", "turno": 2}
        with patch.dict(os.environ, {"NAVIRA_API_KEY": "clave-prueba"}, clear=True):
            turno_viejo = cliente.post("/paso", headers=headers, json={**solicitud, "turno": 1})
            sin_estado = cliente_sin_estado.post("/paso", headers=headers, json=solicitud)
        self.assertEqual(turno_viejo.status_code, 409)
        self.assertEqual(sin_estado.status_code, 503)

    def test_personaje_desconocido_recibe_404(self) -> None:
        cliente = crear_cliente()
        with patch.dict(os.environ, {"NAVIRA_API_KEY": "clave-prueba"}, clear=True):
            respuesta = cliente.post(
                "/paso",
                headers={"x-api-key": "clave-prueba"},
                json={"sobrevivienteId": "S-404", "nodoActual": "N-0001", "turno": 2},
            )
        self.assertEqual(respuesta.status_code, 404)


if __name__ == "__main__":
    unittest.main()
