"""Control local explícito del simulador y publicación de snapshots."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from navira.application.control_simulador_demo import ControlSimuladorDemoLocal
from navira.main import crear_app

RAIZ = Path(__file__).resolve().parents[1]


class ControlSimuladorDemoTests(unittest.TestCase):
    def test_panel_y_runner_comparten_el_planificador_del_mismo_run(self) -> None:
        control = ControlSimuladorDemoLocal(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        estado = control.iniciar(
            escenario="libre",
            cantidad_sobrevivientes=1,
            intensidad="baja",
            eventos_ciudad=False,
            semilla=31,
        )
        control.pausar()
        try:
            planificador = control.consultar_panel.planificador
            self.assertIs(planificador, control._reloj._ejecutar_ronda._decidir)
            self.assertEqual(estado["runId"], control._contexto.run_id)
        finally:
            control.cerrar()

    def test_control_no_se_expone_sin_opt_in_de_desarrollo(self) -> None:
        app = crear_app()
        with patch.dict(os.environ, {}, clear=True):
            response = TestClient(app).get("/demo/simulador")

        self.assertEqual(response.status_code, 404)

    def test_inicio_pausa_y_panel_operan_sobre_la_misma_partida(self) -> None:
        app = crear_app(
            control_simulador_demo=ControlSimuladorDemoLocal(
                str(RAIZ / "data/maps/manta-hackathon-v1.json")
            )
        )
        configuracion = {"NAVIRA_LOCAL_DEMO_CONTROL": "1"}
        with patch.dict(os.environ, configuracion, clear=True):
            with TestClient(
                app,
                base_url="http://localhost",
                client=("127.0.0.1", 43120),
            ) as client:
                # Vite proxies to the backend on another port but preserves hostname.
                headers = {"Origin": "http://localhost:5180"}
                started = client.post(
                    "/demo/simulador/iniciar",
                    headers=headers,
                    json={"escenario": "mixto", "sobrevivientes": 20, "semilla": 31, "intensidad": "alta", "eventosCiudad": True},
                )
                paused = client.post("/demo/simulador/pausar", headers=headers)
                resumed = client.post("/demo/simulador/reanudar", headers=headers)
                restarted = client.post(
                    "/demo/simulador/reiniciar",
                    headers=headers,
                    json={"escenario": "caminantes", "sobrevivientes": 20},
                )
                status_response = client.get("/demo/simulador")
                panel = client.get("/panel/estado")
                map_response = client.get("/panel/mapa")

        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(started.json()["escenario"], "mixto")
        self.assertEqual(started.json()["sobrevivientesIniciales"], 20)
        self.assertEqual(started.json()["intensidad"], "alta")
        self.assertTrue(started.json()["eventosCiudad"])
        self.assertEqual(paused.status_code, 200, paused.text)
        self.assertEqual(paused.json()["estado"], "pausada")
        self.assertEqual(resumed.status_code, 200, resumed.text)
        self.assertEqual(resumed.json()["estado"], "activa")
        self.assertEqual(restarted.status_code, 200, restarted.text)
        self.assertNotEqual(restarted.json()["runId"], started.json()["runId"])
        self.assertEqual(restarted.json()["escenario"], "caminantes")
        self.assertEqual(restarted.json()["intensidad"], "alta")
        self.assertEqual(status_response.json()["runId"], restarted.json()["runId"])
        self.assertEqual(panel.json()["runId"], restarted.json()["runId"])
        self.assertEqual(panel.json()["modo"], "simulador")
        self.assertEqual(map_response.status_code, 200)
        self.assertEqual(map_response.json()["version"], panel.json()["mapVersion"])

    def test_control_rechaza_origen_ajeno_y_conexion_no_local(self) -> None:
        app = crear_app(control_simulador_demo=ControlSimuladorDemoLocal())
        with patch.dict(os.environ, {"NAVIRA_LOCAL_DEMO_CONTROL": "1"}, clear=True):
            remote = TestClient(
                app,
                base_url="http://localhost",
                client=("192.0.2.8", 43210),
            ).post(
                "/demo/simulador/iniciar",
                headers={"Origin": "http://localhost"},
                json={"escenario": "libre", "sobrevivientes": 1},
            )
            cross_origin = TestClient(
                app,
                base_url="http://localhost",
                client=("127.0.0.1", 43211),
            ).post(
                "/demo/simulador/iniciar",
                headers={"Origin": "http://otro-sitio.example"},
                json={"escenario": "libre", "sobrevivientes": 1},
            )

        self.assertEqual(remote.status_code, 403)
        self.assertEqual(cross_origin.status_code, 403)

    def test_control_acepta_aliases_localhost_en_proxy_vite(self) -> None:
        app = crear_app(control_simulador_demo=ControlSimuladorDemoLocal())
        with patch.dict(os.environ, {"NAVIRA_LOCAL_DEMO_CONTROL": "1"}, clear=True):
            response = TestClient(
                app,
                base_url="http://127.0.0.1",
                client=("127.0.0.1", 43212),
            ).post(
                "/demo/simulador/iniciar",
                headers={"Origin": "http://localhost:5173"},
                json={"escenario": "libre", "sobrevivientes": 1, "semilla": 31},
            )

        self.assertEqual(response.status_code, 200, response.text)

    def test_configuracion_fuera_de_rango_es_rechazada(self) -> None:
        app = crear_app(control_simulador_demo=ControlSimuladorDemoLocal())
        with patch.dict(os.environ, {"NAVIRA_LOCAL_DEMO_CONTROL": "1"}, clear=True):
            response = TestClient(
                app,
                base_url="http://localhost",
                client=("127.0.0.1", 43122),
            ).post(
                "/demo/simulador/iniciar",
                headers={"Origin": "http://localhost"},
                json={"escenario": "mixto", "sobrevivientes": 201},
            )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
