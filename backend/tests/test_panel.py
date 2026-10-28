"""Contrato de proyecciones públicas usadas por el panel de observación."""

from __future__ import annotations

import unittest
from dataclasses import replace
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from navira.application.decidir_paso import SolicitudPaso
from navira.application.consultar_panel import ConsultarPanel
from navira.domain.modelo import EstadoSobreviviente, EstadoZombie, FaseTurno, ModoPartida, TipoZombie, Zombie
from navira.demo import MAPA_MANTA_POR_DEFECTO, crear_contexto_demo
from navira.main import crear_app, crear_app_demo
from navira.simulation.coordinador import (
    abrir_siguiente_turno,
    preparar_turno_versionado,
    resolver_turno_versionado,
)


class PanelPublicoTests(unittest.TestCase):
    def test_estado_sin_partida_no_revela_detalles(self) -> None:
        respuesta = TestClient(crear_app()).get("/panel/estado")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"estado": "sin_partida"})

    def test_estado_activo_omite_zombies_dormidos_y_semilla(self) -> None:
        app = crear_app_demo(
            ruta_mapa=MAPA_MANTA_POR_DEFECTO,
            semilla=0,
            escenario="mixto",
            intensidad="alta",
        )
        respuesta = TestClient(app).get("/panel/estado")

        self.assertEqual(respuesta.status_code, 200)
        estado = respuesta.json()
        serializado = respuesta.text
        self.assertEqual(estado["estado"], "activa")
        self.assertEqual(estado["modo"], "simulador")
        self.assertEqual(estado["snapshotVersion"], 1)
        self.assertIn("Z-COR-001", {zombie["id"] for zombie in estado["zombies"]})
        snapshot = app.state.consultar_panel.snapshots.obtener_activa()
        assert snapshot is not None
        for zombie in snapshot.partida.zombies:
            if zombie.estado is EstadoZombie.DORMIDO:
                self.assertNotIn(zombie.id, serializado)
        self.assertNotIn("semilla", serializado.lower())
        self.assertNotIn("estado_rng", serializado.lower())
        self.assertGreater(estado["metricas"]["zombiesVisibles"], 50)
        self.assertEqual(estado["metricas"]["mordidos"], 0)
        self.assertEqual(estado["metricas"]["mordidosUltimoTurno"], 0)
        self.assertEqual(estado["eventosCiudad"], [])

    def test_panel_cuenta_una_vez_a_cada_sobreviviente_mordido_en_la_resolucion(self) -> None:
        contexto = crear_contexto_demo(semilla=9, escenario="libre")
        snapshot = contexto.snapshots.obtener(contexto.run_id)
        assert snapshot is not None
        sobreviviente = snapshot.partida.sobrevivientes[0]
        partida_decisiones = replace(
            snapshot.partida,
            zombies=(
                Zombie("Z-HORDA-1", TipoZombie.HORDA, sobreviviente.nodo),
                Zombie("Z-HORDA-2", TipoZombie.HORDA, sobreviviente.nodo),
            ),
            fase=FaseTurno.DECISIONES,
        )
        decisiones = replace(snapshot, partida=partida_decisiones, version=snapshot.version + 1)
        self.assertTrue(contexto.snapshots.guardar_si_version(contexto.run_id, snapshot.version, decisiones))

        resuelto, resultado = resolver_turno_versionado(
            decisiones,
            contexto.grafo,
            version_esperada=decisiones.version,
        )
        self.assertEqual(resultado.mordidos, (sobreviviente.id,))
        self.assertTrue(contexto.snapshots.guardar_si_version(contexto.run_id, decisiones.version, resuelto))

        panel = ConsultarPanel(contexto.snapshots, contexto.mapas, contexto.servicio_decision)
        metricas = panel.consultar_estado()["metricas"]
        self.assertEqual(metricas["mordidos"], 1)
        self.assertEqual(metricas["mordidosUltimoTurno"], 1)
        self.assertEqual(
            sum(item.estado is EstadoSobreviviente.MORDIDO for item in resuelto.partida.sobrevivientes),
            metricas["mordidos"],
        )

    def test_panel_publica_incidente_solo_despues_de_aplicarlo(self) -> None:
        from pathlib import Path

        ruta = Path(__file__).resolve().parents[1] / "data/maps/manta-hackathon-v1.json"
        contexto = crear_contexto_demo(
            ruta,
            semilla=42,
            escenario="libre",
            eventos_ciudad=True,
            preparar_inicial=False,
        )
        panel = ConsultarPanel(contexto.snapshots, contexto.mapas, contexto.servicio_decision)
        actual = contexto.snapshots.obtener(contexto.run_id)
        assert actual is not None
        inicial = panel.consultar_estado()
        self.assertEqual(inicial["eventosCiudad"], ())
        self.assertNotIn("EV-CIUDAD-001", str(inicial))

        for _ in range(2):
            decisiones, _ = preparar_turno_versionado(
                actual, contexto.grafo, version_esperada=actual.version
            )
            self.assertTrue(contexto.snapshots.guardar_si_version(contexto.run_id, actual.version, decisiones))
            resuelto, _ = resolver_turno_versionado(
                decisiones, contexto.grafo, version_esperada=decisiones.version
            )
            self.assertTrue(contexto.snapshots.guardar_si_version(contexto.run_id, decisiones.version, resuelto))
            siguiente = abrir_siguiente_turno(resuelto, version_esperada=resuelto.version)
            self.assertTrue(contexto.snapshots.guardar_si_version(contexto.run_id, resuelto.version, siguiente))
            actual = siguiente
        decisiones, eventos = preparar_turno_versionado(
            actual, contexto.grafo, version_esperada=actual.version
        )
        self.assertEqual(eventos, ("EV-CIUDAD-001",))
        self.assertTrue(contexto.snapshots.guardar_si_version(contexto.run_id, actual.version, decisiones))

        estado = panel.consultar_estado()
        evento_publicado = estado["eventosCiudad"][0]
        self.assertEqual(evento_publicado["id"], "EV-CIUDAD-001")
        self.assertEqual(evento_publicado["turno"], 2)
        self.assertTrue(-90 <= evento_publicado["lat"] <= 90)
        self.assertTrue(-180 <= evento_publicado["lng"] <= 180)
        self.assertIn(evento_publicado["segmentoId"], estado["segmentosBloqueados"])
        nodos = contexto.grafo.mapa.nodos_por_id
        segmentos_por_par = {
            (calle.origen, calle.destino): calle.segmento_id
            for calle in contexto.grafo.mapa.calles
        }
        for ruta in estado["rutasPrevistas"]:
            tramos = zip(ruta["trayecto"], ruta["trayecto"][1:])
            self.assertTrue(
                all(
                    segmentos_por_par.get((origen, destino)) not in estado["segmentosBloqueados"]
                    for origen, destino in tramos
                )
            )
        evento_segmento = next(
            calle for calle in contexto.grafo.mapa.calles
            if calle.segmento_id == evento_publicado["segmentoId"]
        )
        origen, destino = nodos[evento_segmento.origen], nodos[evento_segmento.destino]
        self.assertAlmostEqual(evento_publicado["lat"], (origen.lat + destino.lat) / 2)
        self.assertAlmostEqual(evento_publicado["lng"], (origen.lng + destino.lng) / 2)

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

    def test_panel_calcula_bajo_demanda_la_ruta_seleccionada_fuera_de_decisiones(self) -> None:
        contexto = crear_contexto_demo(semilla=12, escenario="libre")
        snapshot = contexto.snapshots.obtener(contexto.run_id)
        assert snapshot is not None
        resuelto = replace(
            snapshot,
            partida=replace(snapshot.partida, fase=FaseTurno.RESUELTA),
            version=snapshot.version + 1,
        )
        self.assertTrue(
            contexto.snapshots.guardar_si_version(
                contexto.run_id, snapshot.version, resuelto
            )
        )

        panel = ConsultarPanel(
            contexto.snapshots, contexto.mapas, contexto.servicio_decision
        )
        estado = panel.consultar_estado()
        seleccionado = next(
            persona["id"]
            for persona in estado["sobrevivientes"]
            if persona["estado"] == EstadoSobreviviente.ACTIVO.value
        )

        # El snapshot liviano no calcula rutas para toda la población fuera de
        # decisiones; la selección interactiva calcula exclusivamente una.
        self.assertEqual(estado["rutasPrevistas"], ())
        ruta = panel.consultar_ruta(seleccionado)
        self.assertEqual(ruta["sobrevivienteId"], seleccionado)
        self.assertEqual(ruta["turno"], resuelto.partida.turno)
        self.assertEqual(ruta["snapshotVersion"], resuelto.version)
        self.assertTrue(ruta["trayecto"])
        self.assertEqual(ruta["trayecto"][0], next(
            persona["nodo"] for persona in estado["sobrevivientes"]
            if persona["id"] == seleccionado
        ))

    def test_endpoint_de_ruta_devuelve_un_solo_habitante_seleccionado(self) -> None:
        app = crear_app_demo(semilla=12, escenario="libre")
        cliente = TestClient(app)
        estado = cliente.get("/panel/estado").json()
        seleccionado = next(
            persona["id"] for persona in estado["sobrevivientes"]
            if persona["estado"] == EstadoSobreviviente.ACTIVO.value
        )

        respuesta = cliente.get(f"/panel/ruta/{seleccionado}")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["sobrevivienteId"], seleccionado)
        self.assertTrue(respuesta.json()["trayecto"])

    def test_panel_no_publica_rutas_humanas_fuera_de_fase_de_decisiones(self) -> None:
        contexto = crear_contexto_demo(
            semilla=13, escenario="libre", modo=ModoPartida.JUEGO
        )
        snapshot = contexto.snapshots.obtener(contexto.run_id)
        assert snapshot is not None
        resuelto = replace(
            snapshot,
            partida=replace(snapshot.partida, fase=FaseTurno.RESUELTA),
            version=snapshot.version + 1,
        )
        self.assertTrue(
            contexto.snapshots.guardar_si_version(
                contexto.run_id, snapshot.version, resuelto
            )
        )

        estado = ConsultarPanel(
            contexto.snapshots, contexto.mapas, contexto.servicio_decision
        ).consultar_estado()

        self.assertEqual(estado["rutasPrevistas"], ())

    def test_mapa_sin_partida_devuelve_servicio_no_disponible(self) -> None:
        respuesta = TestClient(crear_app()).get("/panel/mapa")

        self.assertEqual(respuesta.status_code, 503)

    def test_horda_activa_se_proyecta_como_area_visible(self) -> None:
        app = crear_app_demo(
            ruta_mapa=MAPA_MANTA_POR_DEFECTO,
            semilla=0,
            escenario="horda",
            intensidad="alta",
        )
        cliente = TestClient(app)
        estado = cliente.get("/panel/estado").json()

        zombie_horda = next(zombie for zombie in estado["zombies"] if zombie["tipo"] == "horda")
        self.assertIn(zombie_horda["nodo"], estado["nodosHorda"])
        mapa = cliente.get("/panel/mapa").json()
        vecinos = {
            node
            for calle in mapa["calles"]
            for node in (calle["origen"], calle["destino"])
            if zombie_horda["nodo"] in (calle["origen"], calle["destino"])
        }
        self.assertTrue(vecinos <= set(estado["nodosHorda"]))
        snapshot = app.state.consultar_panel.snapshots.obtener_activa()
        assert snapshot is not None
        ids_visibles = {zombie["id"] for zombie in estado["zombies"]}
        for zombie in snapshot.partida.zombies:
            if zombie.estado is EstadoZombie.DORMIDO:
                self.assertNotIn(zombie.id, ids_visibles)


class PanelTiempoRealTests(unittest.TestCase):
    def test_websocket_entrega_snapshot_inicial_completo_y_solo_lectura(self) -> None:
        app = crear_app_demo(semilla=0, escenario="mixto")
        with TestClient(app).websocket_connect(
            "/ws/panel", headers={"origin": "http://testserver"}
        ) as websocket:
            evento = websocket.receive_json()

        self.assertEqual(evento["schemaVersion"], 1)
        self.assertEqual(evento["tipo"], "panel.snapshot")
        self.assertEqual(evento["runId"], app.state.consultar_panel.version_estado()[0])
        self.assertEqual(evento["secuencia"], evento["datos"]["snapshotVersion"])
        self.assertEqual(evento["fase"], evento["datos"]["fase"])
        self.assertNotIn("Z-DOR-001", str(evento))
        self.assertNotIn("semilla", str(evento).lower())

    def test_cambio_version_emite_otra_instantanea_completa(self) -> None:
        app = crear_app_demo(semilla=2, escenario="libre")
        contexto = app.state.consultar_panel
        with TestClient(app).websocket_connect(
            "/ws/panel", headers={"origin": "http://testserver"}
        ) as websocket:
            inicial = websocket.receive_json()
            actual = contexto.snapshots.obtener_activa()
            assert actual is not None
            siguiente, _ = resolver_turno_versionado(
                actual, contexto.mapas.obtener(actual.partida.map_version),
                version_esperada=actual.version,
            )
            self.assertTrue(contexto.snapshots.guardar_si_version(
                actual.partida.run_id, actual.version, siguiente
            ))
            actualizado = websocket.receive_json()

        self.assertEqual(actualizado["runId"], inicial["runId"])
        self.assertEqual(actualizado["secuencia"], inicial["secuencia"] + 1)
        self.assertEqual(actualizado["datos"]["snapshotVersion"], actualizado["secuencia"])
        self.assertEqual(actualizado["datos"]["fase"], "resuelta")

    def test_reconexion_recibe_estado_vigente_sin_reproducir_deltas_viejos(self) -> None:
        app = crear_app_demo(semilla=3, escenario="libre")
        consulta = app.state.consultar_panel
        cliente = TestClient(app)
        with cliente.websocket_connect("/ws/panel", headers={"origin": "http://testserver"}) as socket:
            primero = socket.receive_json()
        actual = consulta.snapshots.obtener_activa()
        assert actual is not None
        siguiente, _ = resolver_turno_versionado(
            actual, consulta.mapas.obtener(actual.partida.map_version),
            version_esperada=actual.version,
        )
        self.assertTrue(consulta.snapshots.guardar_si_version(actual.partida.run_id, actual.version, siguiente))
        resuelto_version = siguiente.version
        siguiente = abrir_siguiente_turno(siguiente, version_esperada=resuelto_version)
        self.assertTrue(consulta.snapshots.guardar_si_version(actual.partida.run_id, resuelto_version, siguiente))

        with cliente.websocket_connect("/ws/panel", headers={"origin": "http://testserver"}) as socket:
            recuperado = socket.receive_json()

        self.assertEqual(recuperado["runId"], primero["runId"])
        self.assertEqual(recuperado["secuencia"], primero["secuencia"] + 2)
        self.assertEqual(recuperado["datos"]["snapshotVersion"], recuperado["secuencia"])

    def test_socket_del_panel_sigue_el_contexto_local_cuando_inicia_otra_partida(self) -> None:
        primera = crear_contexto_demo(semilla=5)
        segunda = crear_contexto_demo(semilla=6)

        class ControlDemoMutable:
            actual = ConsultarPanel(primera.snapshots, primera.mapas, primera.servicio_decision)

            @property
            def consultar_panel(self):
                return self.actual

        control = ControlDemoMutable()
        app = crear_app(control_simulador_demo=control)
        with TestClient(app).websocket_connect(
            "/ws/panel", headers={"origin": "http://testserver"}
        ) as websocket:
            inicial = websocket.receive_json()
            control.actual = ConsultarPanel(segunda.snapshots, segunda.mapas, segunda.servicio_decision)
            cambiado = websocket.receive_json()

        self.assertNotEqual(inicial["runId"], cambiado["runId"])
        self.assertEqual(cambiado["secuencia"], 1)
        self.assertEqual(cambiado["datos"]["runId"], segunda.run_id)

    def test_rechaza_websocket_con_origen_distinto(self) -> None:
        with self.assertRaises(WebSocketDisconnect):
            with TestClient(crear_app()).websocket_connect(
                "/ws/panel", headers={"origin": "https://sitio-ajeno.example"}
            ):
                self.fail("El handshake de otro origen no debe aceptarse.")

    def test_envia_heartbeat_sin_cambios_para_detectar_conexion_viva(self) -> None:
        with patch("navira.api.routes._PANEL_WS_HEARTBEAT_SECONDS", 0.01):
            with TestClient(crear_app()).websocket_connect(
                "/ws/panel", headers={"origin": "http://testserver"}
            ) as websocket:
                inicial = websocket.receive_json()
                latido = websocket.receive_json()

        self.assertEqual(inicial["tipo"], "panel.snapshot")
        self.assertEqual(latido["tipo"], "panel.latido")
        self.assertEqual(latido["runId"], None)


if __name__ == "__main__":
    unittest.main()
