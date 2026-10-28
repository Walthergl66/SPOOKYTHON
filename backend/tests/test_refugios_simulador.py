"""Candidatos de refugio y refugios personalizados del simulador local."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from navira.api.seguridad import ConfiguracionSeguridad
from navira.main import crear_app, crear_control_simulador_demo

LOCAL = ConfiguracionSeguridad(control_demo_local=True)
CABECERAS = {"Origin": "http://localhost:5180"}
VALIDOS = [{"id": f"R-0{i}", "nodo": f"N-{i}"} for i in range(1, 5)]


def _escribir_mapa(directorio: str) -> str:
    """Anillo bidireccional de 8 nodos más N-SUMIDERO, que solo tiene entrada."""

    nodos = [{"id": f"N-{i}", "lat": -0.95 - i * 1e-3, "lng": -80.7} for i in range(8)]
    nodos.append({"id": "N-SUMIDERO", "lat": -0.96, "lng": -80.71})
    calles = []
    for i in range(8):
        for a, b in ((i, (i + 1) % 8), ((i + 1) % 8, i)):
            calles.append({"id": f"E-{a}-{b}", "segmentoId": f"S-{min(a, b)}-{max(a, b)}",
                           "origen": f"N-{a}", "destino": f"N-{b}",
                           "distancia_m": 100, "tipo": "calle", "velocidad_kmh": 30})
    calles.append({"id": "E-0-S", "segmentoId": "S-S", "origen": "N-0", "destino": "N-SUMIDERO",
                   "distancia_m": 100, "tipo": "calle", "velocidad_kmh": 30})
    refugios = [{"id": f"R-0{i}", "nodo": f"N-{i + 3}"} for i in range(1, 5)]
    ruta = Path(directorio) / "mapa.json"
    ruta.write_text(json.dumps({"version": "mini-v1", "nodos": nodos, "calles": calles, "refugios": refugios}))
    return str(ruta)


class RefugiosSimuladorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.control = crear_control_simulador_demo(_escribir_mapa(self._tmp.name))
        self.addCleanup(self.control.cerrar)

    def _cliente(self, seguridad=LOCAL) -> TestClient:
        app = crear_app(control_simulador_demo=self.control, seguridad=seguridad)
        return TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43125))

    def _iniciar(self, client: TestClient, refugios, accion: str = "iniciar"):
        cuerpo = {"escenario": "libre", "sobrevivientes": 1, "eventosCiudad": False}
        if refugios is not None:
            cuerpo["refugios"] = refugios
        return client.post(f"/demo/simulador/{accion}", headers=CABECERAS, json=cuerpo)

    def test_candidatos_404_si_el_control_esta_deshabilitado(self) -> None:
        with self._cliente(ConfiguracionSeguridad()) as client:
            self.assertEqual(client.get("/demo/simulador/candidatos").status_code, 404)

    def test_candidatos_solo_incluye_nodos_con_entrada_y_salida(self) -> None:
        with self._cliente() as client:
            respuesta = client.get("/demo/simulador/candidatos")
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        cuerpo = respuesta.json()
        ids = {nodo["id"] for nodo in cuerpo["nodos"]}
        self.assertEqual(cuerpo["version"], "mini-v1")
        self.assertEqual(ids, {f"N-{i}" for i in range(8)})
        self.assertEqual(len(cuerpo["refugios"]), 4)
        self.assertEqual(len(cuerpo["calles"]), 17)
        self.assertEqual(set(cuerpo["calles"][0]), {"origen", "destino"})

    def test_iniciar_con_refugios_validos_usa_el_mapa_personalizado(self) -> None:
        with self._cliente() as client:
            self.assertEqual(self._iniciar(client, VALIDOS).status_code, 200)
            grafo = self.control._contexto.grafo
            self.assertEqual({r.id: r.nodo for r in grafo.mapa.refugios}, {r["id"]: r["nodo"] for r in VALIDOS})
            snapshot = self.control._snapshot()
            self.assertTrue(snapshot.partida.map_version.startswith("mini-v1+refugios-"))
            self.assertIs(self.control._contexto.mapas.obtener(snapshot.partida.map_version), grafo)

    def test_iniciar_rechaza_refugios_invalidos_con_422(self) -> None:
        casos = {
            "tres": VALIDOS[:3],
            "ids repetidos": [VALIDOS[0], VALIDOS[0], VALIDOS[2], VALIDOS[3]],
            "nodo inexistente": VALIDOS[:3] + [{"id": "R-04", "nodo": "N-NO-EXISTE"}],
            "nodo sin salida": VALIDOS[:3] + [{"id": "R-04", "nodo": "N-SUMIDERO"}],
            "nodos repetidos": VALIDOS[:3] + [{"id": "R-04", "nodo": "N-1"}],
        }
        with self._cliente() as client:
            for nombre, refugios in casos.items():
                with self.subTest(nombre):
                    self.assertEqual(self._iniciar(client, refugios).status_code, 422)

    def test_reiniciar_con_refugios_validos_usa_el_mapa_personalizado(self) -> None:
        with self._cliente() as client:
            self.assertEqual(self._iniciar(client, None).status_code, 200)
            respuesta = self._iniciar(client, VALIDOS, "reiniciar")
            self.assertEqual(respuesta.status_code, 200, respuesta.text)
            self.assertEqual(respuesta.json()["zombiesIniciales"], 0)
            grafo = self.control._contexto.grafo
            self.assertEqual({r.id: r.nodo for r in grafo.mapa.refugios}, {r["id"]: r["nodo"] for r in VALIDOS})

    def test_reiniciar_rechaza_refugios_invalidos_con_422(self) -> None:
        with self._cliente() as client:
            self.assertEqual(self._iniciar(client, None).status_code, 200)
            self.assertEqual(self._iniciar(client, VALIDOS[:3], "reiniciar").status_code, 422)

    def test_sin_refugios_conserva_los_del_mapa(self) -> None:
        with self._cliente() as client:
            self.assertEqual(self._iniciar(client, None).status_code, 200)
            self.assertEqual(self.control._snapshot().partida.map_version, "mini-v1")


if __name__ == "__main__":
    unittest.main()
