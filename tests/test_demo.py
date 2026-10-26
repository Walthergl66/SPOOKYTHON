"""Arranque local explícito con el mapa sintético de Navira."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from navira.application.decidir_paso import SolicitudPaso
from navira.demo import crear_servicio_demo
from navira.main import crear_app, crear_app_demo


class DemoBootstrapTests(unittest.TestCase):
    def test_demo_abre_turno_activo_y_planifica_hacia_refugio(self) -> None:
        servicio = crear_servicio_demo()

        decision = servicio.ejecutar(SolicitudPaso("S-DEMO-001", "D-001", 0))

        self.assertEqual(decision.siguiente_nodo, "D-002")

    def test_app_demo_usa_planificador_en_la_ruta_http(self) -> None:
        app = crear_app_demo()
        with patch.dict(os.environ, {"NAVIRA_API_KEY": "demo-test-key"}, clear=True):
            respuesta = TestClient(app).post(
                "/paso",
                headers={"x-api-key": "demo-test-key"},
                json={
                    "sobrevivienteId": "S-DEMO-001",
                    "nodoActual": "D-001",
                    "turno": 0,
                },
            )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"siguienteNodo": "D-002"})

    def test_demo_se_activa_solo_con_variable_explicita(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            aplicacion = crear_app()

        self.assertEqual(
            aplicacion.state.decidir_paso.ejecutar(
                SolicitudPaso("desconocido", "D-001", 0)
            ).siguiente_nodo,
            "D-001",
        )


if __name__ == "__main__":
    unittest.main()
