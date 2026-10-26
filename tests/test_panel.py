"""Contrato de proyecciones públicas usadas por el panel de observación."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from navira.application.decidir_paso import SolicitudPaso
from navira.demo import crear_contexto_demo
from navira.main import crear_app, crear_app_demo


class PanelPublicoTests(unittest.TestCase):
    def test_estado_sin_partida_no_revela_detalles(self) -> None:
        respuesta = TestClient(crear_app()).get("/panel/estado")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"estado": "sin_partida"})

    def test_estado_activo_omite_zombies_dormidos_y_semilla(self) -> None:
        respuesta = TestClient(crear_app_demo(semilla=0, escenario="mixto")).get("/panel/estado")

        self.assertEqual(respuesta.status_code, 200)
        estado = respuesta.json()
        serializado = respuesta.text
        self.assertEqual(estado["estado"], "activa")
        self.assertEqual(estado["modo"], "simulador")
        self.assertEqual(estado["snapshotVersion"], 1)
        self.assertIn("Z-COR-001", {zombie["id"] for zombie in estado["zombies"]})
        self.assertNotIn("Z-DOR-001", serializado)
        self.assertNotIn("semilla", serializado.lower())
        self.assertNotIn("estado_rng", serializado.lower())
        self.assertEqual(estado["metricas"]["zombiesVisibles"], 1)

    def test_mapa_corresponde_a_la_version_activa_y_no_incluye_estado(self) -> None:
        contexto = crear_contexto_demo(semilla=9)
        respuesta = TestClient(crear_app_demo(semilla=9)).get("/panel/mapa")

        self.assertEqual(respuesta.status_code, 200)
        mapa = respuesta.json()
        self.assertEqual(mapa["version"], contexto.grafo.mapa.version)
        self.assertEqual(len(mapa["nodos"]), len(contexto.grafo.mapa.nodos))
        self.assertEqual(len(mapa["calles"]), len(contexto.grafo.mapa.calles))
        self.assertEqual(len(mapa["refugios"]), len(contexto.grafo.mapa.refugios))
        self.assertNotIn("zombies", mapa)

    def test_ruta_prevista_coincide_con_la_primera_decision_del_motor(self) -> None:
        app = crear_app_demo(semilla=0, escenario="libre")
        cliente = TestClient(app)
        estado = cliente.get("/panel/estado").json()
        personaje = estado["sobrevivientes"][0]
        ruta = next(
            ruta for ruta in estado["rutasPrevistas"]
            if ruta["sobrevivienteId"] == personaje["id"]
        )["trayecto"]
        decision = app.state.decidir_paso.ejecutar(
            SolicitudPaso(personaje["id"], personaje["nodo"], estado["turno"])
        )

        self.assertEqual(ruta[0], personaje["nodo"])
        self.assertEqual(ruta[1] if len(ruta) > 1 else ruta[0], decision.siguiente_nodo)
        self.assertIn(ruta[-1], {refugio["nodo"] for refugio in cliente.get("/panel/mapa").json()["refugios"]})

    def test_mapa_sin_partida_devuelve_servicio_no_disponible(self) -> None:
        respuesta = TestClient(crear_app()).get("/panel/mapa")

        self.assertEqual(respuesta.status_code, 503)

    def test_horda_activa_se_proyecta_como_area_visible(self) -> None:
        estado = TestClient(crear_app_demo(semilla=0, escenario="horda")).get(
            "/panel/estado"
        ).json()

        zombie_horda = next(zombie for zombie in estado["zombies"] if zombie["tipo"] == "horda")
        self.assertIn(zombie_horda["nodo"], estado["nodosHorda"])
        mapa = TestClient(crear_app_demo(semilla=0, escenario="horda")).get("/panel/mapa").json()
        vecinos = {
            node
            for calle in mapa["calles"]
            for node in (calle["origen"], calle["destino"])
            if zombie_horda["nodo"] in (calle["origen"], calle["destino"])
        }
        self.assertTrue(vecinos <= set(estado["nodosHorda"]))
        self.assertNotIn("Z-DOR-002", {zombie["id"] for zombie in estado["zombies"]})


if __name__ == "__main__":
    unittest.main()
