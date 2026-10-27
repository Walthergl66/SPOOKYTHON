"""Pruebas HTTP ASGI de salud, autenticación y contrato POST /paso."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from navira.main import app


class ApiHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cliente = TestClient(app)

    def test_salud_es_publica_y_minima(self) -> None:
        respuesta = self.cliente.get("/salud")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"estado": "activo", "servicio": "navira"})

    def test_sin_configuracion_de_clave_falla_cerrado(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            respuesta = self.cliente.post(
                "/paso",
                json={"sobrevivienteId": "S-1", "nodoActual": "N-1", "turno": 0},
            )
        self.assertEqual(respuesta.status_code, 503)

    def test_clave_incorrecta_recibe_401(self) -> None:
        with patch.dict(os.environ, {"NAVIRA_API_KEY": "clave-de-prueba"}, clear=True):
            respuesta = self.cliente.post(
                "/paso",
                headers={"x-api-key": "incorrecta"},
                json={"sobrevivienteId": "S-1", "nodoActual": "N-1", "turno": 0},
            )
        self.assertEqual(respuesta.status_code, 401)

    def test_contrato_aceptado_responde_solo_siguiente_nodo(self) -> None:
        with patch.dict(os.environ, {"NAVIRA_API_KEY": "clave-de-prueba"}, clear=True):
            respuesta = self.cliente.post(
                "/paso",
                headers={"x-api-key": "clave-de-prueba"},
                json={"sobrevivienteId": "S-0089", "nodoActual": "N-0117", "turno": 142},
            )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"siguienteNodo": "N-0117"})

    def test_esquema_rechaza_campo_extra_y_turno_negativo(self) -> None:
        with patch.dict(os.environ, {"NAVIRA_API_KEY": "clave-de-prueba"}, clear=True):
            headers = {"x-api-key": "clave-de-prueba"}
            campo_extra = self.cliente.post(
                "/paso",
                headers=headers,
                json={"sobrevivienteId": "S-1", "nodoActual": "N-1", "turno": 0, "runId": "x"},
            )
            turno_negativo = self.cliente.post(
                "/paso",
                headers=headers,
                json={"sobrevivienteId": "S-1", "nodoActual": "N-1", "turno": -1},
            )
        self.assertEqual(campo_extra.status_code, 422)
        self.assertEqual(turno_negativo.status_code, 422)


if __name__ == "__main__":
    unittest.main()
