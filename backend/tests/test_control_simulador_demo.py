"""Control local explícito del simulador y publicación de snapshots."""

from __future__ import annotations

import unittest
import time
from pathlib import Path

from fastapi.testclient import TestClient

from navira.api.seguridad import ConfiguracionSeguridad
from navira.main import crear_app, crear_control_simulador_demo
from navira.domain.mapa import nodos_protegidos_refugios

RAIZ = Path(__file__).resolve().parents[1]
LOCAL = ConfiguracionSeguridad(control_demo_local=True)


class ControlSimuladorDemoTests(unittest.TestCase):
    def test_operador_inicia_mapa_vacio_y_puede_colocar_piezas(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        headers = {"Origin": "http://localhost:5173"}
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43129)) as client:
            started = client.post("/demo/operador/iniciar", headers=headers)
            snapshot_inicial = control._snapshot()
            mapa_inicial = client.get("/panel/mapa", headers=headers)

            # Un mundo sin habitantes sigue avanzando para que el operador pueda
            # colocar sus primeras piezas cuando quiera.
            limite = time.monotonic() + 1.5
            while control._snapshot().partida.turno == 0 and time.monotonic() < limite:
                time.sleep(0.02)
            snapshot_avanzado = control._snapshot()

            grafo = control._contexto.mapas.obtener(snapshot_avanzado.partida.map_version)
            nodo_refugio = next(n.id for n in grafo.mapa.nodos if grafo.calles_desde(n.id))
            nodo_habitante = next(n.id for n in grafo.mapa.nodos if n.id != nodo_refugio and grafo.calles_desde(n.id))
            refuge = client.post("/demo/operador/elementos", headers=headers, json={"tipo": "refugio", "nodo": nodo_refugio})
            resident = client.post("/demo/operador/elementos", headers=headers, json={"tipo": "habitante", "nodo": nodo_habitante})
            status = client.get("/panel/estado", headers=headers)
            control.cerrar()

        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(started.json()["sobrevivientesIniciales"], 0)
        self.assertEqual(started.json()["zombiesIniciales"], 0)
        self.assertTrue(control._configuracion.get("mundo_vacio"))
        self.assertEqual(snapshot_inicial.partida.sobrevivientes, ())
        self.assertEqual(snapshot_inicial.partida.zombies, ())
        self.assertEqual(snapshot_inicial.eventos_programados, ())
        self.assertEqual(mapa_inicial.status_code, 200, mapa_inicial.text)
        self.assertEqual(mapa_inicial.json()["refugios"], [])
        self.assertGreater(snapshot_avanzado.partida.turno, 0)
        self.assertEqual(control.estado()["estado"], "activa")
        self.assertEqual(refuge.status_code, 200, refuge.text)
        self.assertEqual(resident.status_code, 200, resident.text)
        self.assertEqual(status.status_code, 200, status.text)
        self.assertEqual(status.json()["metricas"]["sobrevivientesActivos"], 1)

    def test_operador_puede_iniciar_nueva_partida_mientras_otra_esta_activa(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        headers = {"Origin": "http://localhost:5173"}
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43130)) as client:
            primera = client.post("/demo/operador/iniciar", headers=headers)
            snapshot_primera = control._snapshot()
            grafo = control._contexto.mapas.obtener(snapshot_primera.partida.map_version)
            nodo = next(n.id for n in grafo.mapa.nodos if grafo.calles_desde(n.id))
            colocado = client.post(
                "/demo/operador/elementos",
                headers=headers,
                json={"tipo": "habitante", "nodo": nodo},
            )

            nueva = client.post("/demo/operador/iniciar", headers=headers)
            snapshot_nuevo = control._snapshot()
            control.cerrar()

        self.assertEqual(primera.status_code, 200, primera.text)
        self.assertEqual(colocado.status_code, 200, colocado.text)
        self.assertEqual(nueva.status_code, 200, nueva.text)
        self.assertNotEqual(nueva.json()["runId"], primera.json()["runId"])
        self.assertEqual(nueva.json()["estado"], "activa")
        self.assertEqual(snapshot_nuevo.partida.sobrevivientes, ())
        self.assertEqual(snapshot_nuevo.partida.zombies, ())
        self.assertEqual(snapshot_nuevo.eventos_programados, ())

    def test_operador_coloca_habitante_refugio_e_incidente_en_el_mundo_activo(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        headers = {"Origin": "http://localhost:5173"}
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43127)) as client:
            started = client.post("/demo/simulador/iniciar", headers=headers, json={"escenario": "mixto", "sobrevivientes": 20, "zombies": 10, "semilla": 37})
            snapshot = control._snapshot()
            grafo = control._contexto.mapas.obtener(snapshot.partida.map_version)
            nodo = next(n.id for n in grafo.mapa.nodos if n.id not in nodos_protegidos_refugios(grafo))
            refuge_node = next(n.id for n in grafo.mapa.nodos if all(r.nodo != n.id for r in grafo.mapa.refugios))
            segment = next(c.segmento_id for c in grafo.mapa.calles if c.segmento_id not in snapshot.segmentos_cerrados)
            horde = client.post("/demo/operador/elementos", headers=headers, json={"tipo": "horda", "nodo": nodo})
            sleeper = client.post("/demo/operador/elementos", headers=headers, json={"tipo": "dormido", "nodo": nodo})
            hidden_state = client.get("/panel/estado", headers=headers)
            person = client.post("/demo/operador/elementos", headers=headers, json={"tipo": "habitante", "nodo": nodo})
            refuge = client.post("/demo/operador/elementos", headers=headers, json={"tipo": "refugio", "nodo": refuge_node})
            incident = client.post("/demo/operador/elementos", headers=headers, json={"tipo": "incidente", "segmentoId": segment})
            invalid_node = client.post("/demo/operador/elementos", headers=headers, json={"tipo": "habitante", "nodo": "fuera-del-mapa"})
            state = client.get("/panel/estado", headers=headers)
            map_response = client.get("/panel/mapa", headers=headers)
            control.cerrar()

        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(horde.status_code, 200, horde.text)
        self.assertEqual(sleeper.status_code, 200, sleeper.text)
        self.assertEqual(person.status_code, 200, person.text)
        self.assertNotIn(sleeper.json()["elementoId"], {z["id"] for z in hidden_state.json()["zombies"]})
        self.assertEqual(refuge.status_code, 200, refuge.text)
        self.assertEqual(incident.status_code, 200, incident.text)
        self.assertEqual(invalid_node.status_code, 422)
        self.assertEqual(state.status_code, 200, state.text)
        self.assertEqual(map_response.status_code, 200, map_response.text)
        self.assertEqual(map_response.json()["version"], state.json()["mapVersion"])
        self.assertIn(segment, state.json()["segmentosBloqueados"])
        self.assertGreaterEqual(len(map_response.json()["refugios"]), 5)

    def test_operador_rechaza_ronda_reto_y_ubicaciones_fuera_del_mapa(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        headers = {"Origin": "http://localhost:5173"}
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43128)) as client:
            reto = client.post("/reto/iniciar", headers=headers, json={"ronda": 1, "semilla": 37})
            blocked = client.post("/demo/operador/elementos", headers=headers, json={"tipo": "habitante", "nodo": "fuera-del-mapa"})
            control.cerrar()

        self.assertEqual(reto.status_code, 200, reto.text)
        self.assertEqual(blocked.status_code, 409)

    def test_reto_se_puede_pausar_y_continuar_sin_perder_la_ronda(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43125)) as client:
            headers = {"Origin": "http://localhost:5173"}
            started = client.post("/reto/iniciar", headers=headers, json={"ronda": 2, "semilla": 44})
            paused = client.post("/demo/simulador/pausar", headers=headers)
            resumed = client.post("/demo/simulador/reanudar", headers=headers)
            control.cerrar()

        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(paused.status_code, 200, paused.text)
        self.assertEqual(paused.json()["estado"], "pausada")
        self.assertEqual(paused.json()["rondaReto"], 2)
        self.assertEqual(resumed.status_code, 200, resumed.text)
        self.assertEqual(resumed.json()["estado"], "activa")
        self.assertEqual(resumed.json()["rondaReto"], 2)

    def test_nueva_ronda_reemplaza_reto_pausado_con_run_nuevo(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43126)) as client:
            headers = {"Origin": "http://localhost:5173"}
            original = client.post("/reto/iniciar", headers=headers, json={"ronda": 2, "semilla": 44})
            paused = client.post("/demo/simulador/pausar", headers=headers)
            nueva = client.post("/reto/iniciar", headers=headers, json={"ronda": 3, "semilla": 45})
            conflicto_activa = client.post("/reto/iniciar", headers=headers, json={"ronda": 1, "semilla": 46})
            control.cerrar()

        self.assertEqual(original.status_code, 200, original.text)
        self.assertEqual(paused.status_code, 200, paused.text)
        self.assertEqual(nueva.status_code, 200, nueva.text)
        self.assertNotEqual(nueva.json()["runId"], original.json()["runId"])
        self.assertEqual(nueva.json()["rondaReto"], 3)
        self.assertEqual(nueva.json()["sobrevivientesIniciales"], 200)
        self.assertEqual(conflicto_activa.status_code, 409)

    def test_ruta_reto_reinicia_la_ronda_actual_en_un_run_nuevo(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43123)) as client:
            headers = {"Origin": "http://localhost:5173"}
            original = client.post("/reto/iniciar", headers=headers, json={"ronda": 2, "semilla": 44})
            client.post("/demo/simulador/pausar", headers=headers)
            reiniciada = client.post("/reto/reiniciar", headers=headers)
            nuevo_snapshot = control._snapshot()
            control.cerrar()

        self.assertEqual(original.status_code, 200, original.text)
        self.assertEqual(reiniciada.status_code, 200, reiniciada.text)
        self.assertNotEqual(reiniciada.json()["runId"], original.json()["runId"])
        self.assertEqual(reiniciada.json()["rondaReto"], 2)
        self.assertEqual(reiniciada.json()["sobrevivientesIniciales"], 80)
        self.assertEqual(nuevo_snapshot.partida.escenario, "reto-ronda-2-reto_medianoche")

    def test_reiniciar_reto_sin_ronda_devuelve_conflicto(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43124)) as client:
            response = client.post("/reto/reiniciar", headers={"Origin": "http://localhost:5173"})
        self.assertEqual(response.status_code, 409)

    def test_ruta_reto_inicia_preset_sin_alterar_preferencia_de_demo(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43119)) as client:
            respuesta = client.post(
                "/reto/iniciar",
                headers={"Origin": "http://localhost:5173"},
                json={"ronda": 2, "semilla": 44},
            )
            control.pausar()
            snapshot = control._snapshot()
            control.cerrar()

        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        self.assertEqual(respuesta.json()["sobrevivientesIniciales"], 80)
        self.assertEqual(respuesta.json()["intensidad"], "media")
        self.assertEqual(respuesta.json()["rondaReto"], 2)
        self.assertEqual(respuesta.json()["velocidad"], 1.0)
        self.assertFalse(respuesta.json()["eventosCiudad"])
        self.assertEqual(len(snapshot.eventos_programados), 1)

    def test_reto_inicia_run_nuevo_al_cambiar_desde_una_partida_libre_pausada(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43118)) as client:
            headers = {"Origin": "http://localhost:5173"}
            libre = client.post("/demo/simulador/iniciar", headers=headers, json={"escenario": "libre", "sobrevivientes": 1})
            client.post("/demo/simulador/pausar", headers=headers)
            reto = client.post("/reto/iniciar", headers=headers, json={"ronda": 1})
            snapshot = control._snapshot()
            control.cerrar()
        self.assertEqual(libre.status_code, 200)
        self.assertEqual(reto.status_code, 200, reto.text)
        self.assertNotEqual(reto.json()["runId"], libre.json()["runId"])
        self.assertEqual(reto.json()["rondaReto"], 1)
        self.assertEqual(reto.json()["sobrevivientesIniciales"], 20)
        self.assertEqual(snapshot.partida.run_id, reto.json()["runId"])

    def test_reto_reemplaza_partida_jugar_activa_con_run_nuevo(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        headers = {"Origin": "http://localhost:5173"}
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43117)) as client:
            operador = client.post("/demo/operador/iniciar", headers=headers)
            reto = client.post("/reto/iniciar", headers=headers, json={"ronda": 2, "semilla": 44})
            snapshot = control._snapshot()
            control.cerrar()

        self.assertEqual(operador.status_code, 200, operador.text)
        self.assertEqual(reto.status_code, 200, reto.text)
        self.assertNotEqual(reto.json()["runId"], operador.json()["runId"])
        self.assertEqual(reto.json()["estado"], "activa")
        self.assertEqual(reto.json()["rondaReto"], 2)
        self.assertEqual(reto.json()["sobrevivientesIniciales"], 80)
        self.assertEqual(len(snapshot.partida.sobrevivientes), 80)
        self.assertEqual(snapshot.partida.run_id, reto.json()["runId"])

    def test_selector_publica_limites_y_rechaza_refugio_fuera_del_recorte(self) -> None:
        mapa_path = RAIZ / "data/maps/manta-hackathon-v1.json"
        control = crear_control_simulador_demo(str(mapa_path))
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        outside = next(nodo for nodo in control.mapa.nodos if nodo.lng < -80.807)
        refugios = [
            {"id": f"R-0{i}", "nodo": outside.id if i == 1 else control.mapa.refugios[i - 1].nodo}
            for i in range(1, 5)
        ]
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 43122)) as client:
            headers = {"Origin": "http://localhost:5180"}
            candidatos = client.get("/demo/simulador/candidatos", headers=headers)
            inicio = client.post(
                "/demo/simulador/iniciar",
                headers=headers,
                json={"escenario": "libre", "sobrevivientes": 1, "refugios": refugios},
            )
            control.cerrar()

        self.assertEqual(candidatos.status_code, 200)
        self.assertEqual(candidatos.json()["limitesJugables"], [[-80.807, -1.082], [-80.621, -0.897]])
        self.assertIn(outside.id, {n["id"] for n in candidatos.json()["nodos"]})
        self.assertEqual(inicio.status_code, 422)

    def test_inicio_usa_dificultad_media_si_no_se_envia_configuracion(self) -> None:
        control = crear_control_simulador_demo(
            str(RAIZ / "data/maps/manta-hackathon-v1.json")
        )
        app = crear_app(control_simulador_demo=control, seguridad=LOCAL)
        with TestClient(
            app,
            base_url="http://localhost",
            client=("127.0.0.1", 43121),
        ) as client:
            response = client.post(
                "/demo/simulador/iniciar",
                headers={"Origin": "http://localhost:5180"},
                json={"escenario": "mixto", "sobrevivientes": 20, "eventosCiudad": False},
            )
            snapshot = control._contexto.snapshots.obtener(response.json()["runId"])
            control.cerrar()

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["intensidad"], "media")
        self.assertTrue(response.json()["eventosCiudad"])
        self.assertTrue(snapshot.eventos_programados)

    def test_panel_y_runner_comparten_el_planificador_del_mismo_run(self) -> None:
        control = crear_control_simulador_demo(str(RAIZ / "data/maps/manta-hackathon-v1.json"))
        estado = control.iniciar(
            escenario="libre",
            cantidad_sobrevivientes=1,
            intensidad="baja",
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
        response = TestClient(app).get("/demo/simulador")

        self.assertEqual(response.status_code, 404)

    def test_inicio_pausa_y_panel_operan_sobre_la_misma_partida(self) -> None:
        app = crear_app(
            control_simulador_demo=crear_control_simulador_demo(
                str(RAIZ / "data/maps/manta-hackathon-v1.json")
            ),
            seguridad=LOCAL,
        )
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
                json={"escenario": "mixto", "sobrevivientes": 20, "zombies": 31, "semilla": 31, "intensidad": "alta", "eventosCiudad": False},
            )
            paused = client.post("/demo/simulador/pausar", headers=headers)
            resumed = client.post("/demo/simulador/reanudar", headers=headers)
            restarted = client.post(
                "/demo/simulador/reiniciar",
                headers=headers,
                json={"escenario": "caminantes", "sobrevivientes": 20, "eventosCiudad": False},
            )
            restarted_snapshot = app.state.control_simulador_demo._contexto.snapshots.obtener(
                restarted.json()["runId"]
            )
            status_response = client.get("/demo/simulador")
            panel = client.get("/panel/estado")
            map_response = client.get("/panel/mapa")

        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(started.json()["escenario"], "mixto")
        self.assertEqual(started.json()["sobrevivientesIniciales"], 20)
        self.assertEqual(started.json()["zombiesIniciales"], 31)
        self.assertEqual(started.json()["intensidad"], "alta")
        self.assertTrue(started.json()["eventosCiudad"])
        self.assertEqual(paused.status_code, 200, paused.text)
        self.assertEqual(paused.json()["estado"], "pausada")
        self.assertEqual(resumed.status_code, 200, resumed.text)
        self.assertEqual(resumed.json()["estado"], "activa")
        self.assertEqual(restarted.status_code, 200, restarted.text)
        self.assertNotEqual(restarted.json()["runId"], started.json()["runId"])
        self.assertEqual(restarted.json()["escenario"], "caminantes")
        self.assertEqual(restarted.json()["intensidad"], "media")
        self.assertTrue(restarted.json()["eventosCiudad"])
        self.assertTrue(restarted_snapshot.eventos_programados)
        self.assertEqual(status_response.json()["runId"], restarted.json()["runId"])
        self.assertEqual(panel.json()["runId"], restarted.json()["runId"])
        self.assertEqual(panel.json()["modo"], "simulador")
        self.assertEqual(map_response.status_code, 200)
        self.assertEqual(map_response.json()["version"], panel.json()["mapVersion"])

    def test_control_rechaza_origen_ajeno_y_conexion_no_local(self) -> None:
        app = crear_app(control_simulador_demo=crear_control_simulador_demo(), seguridad=LOCAL)
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
        app = crear_app(control_simulador_demo=crear_control_simulador_demo(), seguridad=LOCAL)
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
        app = crear_app(control_simulador_demo=crear_control_simulador_demo(), seguridad=LOCAL)
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
