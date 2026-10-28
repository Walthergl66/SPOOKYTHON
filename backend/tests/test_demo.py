"""Arranque local explícito con el mapa sintético de Navira."""

from __future__ import annotations

import os
import random
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from navira.application.decidir_paso import SolicitudPaso
from navira.api.seguridad import ConfiguracionSeguridad
from navira.demo import (
    CENTRO_URBANO_RETO,
    RADIO_FOCO_AMENAZAS_RETO_M,
    RADIO_ZONA_SPAWN_RETO_M,
    SECTORES_SPAWN_RETO,
    _distancia_metros,
    _nodos_inicio_elegibles,
    crear_contexto_demo,
)
from navira.domain.modelo import EstadoZombie
from navira.domain.mapa import Refugio, cargar_mapa, nodos_protegidos_refugios
from navira.main import _crear_app_configurada, crear_app, crear_app_demo
from navira.simulation.escenarios import crear_eventos_ciudad


class DemoBootstrapTests(unittest.TestCase):
    def test_partida_manta_recorta_apariciones_y_rechaza_refugio_fuera_de_zona(self) -> None:
        ruta_manta = Path(__file__).resolve().parents[1] / "data/maps/manta-hackathon-v1.json"
        mapa_original = cargar_mapa(ruta_manta)
        fuera = next(
            nodo for nodo in mapa_original.nodos
            if nodo.lng < -80.807 or nodo.lng > -80.621 or nodo.lat < -1.082 or nodo.lat > -0.897
        )
        contexto = crear_contexto_demo(ruta_manta, semilla=88, cantidad_sobrevivientes=20, intensidad="alta")
        partida = contexto.snapshots.obtener(contexto.run_id).partida

        self.assertTrue(all(nodo in contexto.grafo.mapa.nodos_por_id for nodo in (s.nodo for s in partida.sobrevivientes)))
        self.assertTrue(all(nodo in contexto.grafo.mapa.nodos_por_id for nodo in (z.nodo for z in partida.zombies)))
        protegidos = nodos_protegidos_refugios(contexto.grafo)
        self.assertTrue(all(zombie.nodo not in protegidos for zombie in partida.zombies))
        self.assertTrue(all(calle.origen in contexto.grafo.mapa.nodos_por_id and calle.destino in contexto.grafo.mapa.nodos_por_id for calle in contexto.grafo.mapa.calles))
        with self.assertRaisesRegex(ValueError, "no existe en el mapa"):
            crear_contexto_demo(ruta_manta, refugios=(
                Refugio("R-01", fuera.id),
                Refugio("R-02", mapa_original.refugios[1].nodo),
                Refugio("R-03", mapa_original.refugios[2].nodo),
                Refugio("R-04", mapa_original.refugios[3].nodo),
            ))

    def test_intensidad_alta_distribuye_composicion_sintetica_por_la_ciudad(self) -> None:
        ruta_manta = Path(__file__).resolve().parents[1] / "data/maps/manta-hackathon-v1.json"
        contexto = crear_contexto_demo(
            ruta_manta,
            semilla=812,
            escenario="mixto",
            cantidad_sobrevivientes=20,
            intensidad="alta",
            preparar_inicial=False,
        )
        partida = contexto.snapshots.obtener(contexto.run_id).partida
        nodos = [zombie.nodo for zombie in partida.zombies]
        celdas = {
            (round(contexto.grafo.mapa.nodos_por_id[nodo].lat, 3), round(contexto.grafo.mapa.nodos_por_id[nodo].lng, 3))
            for nodo in nodos
        }

        self.assertGreaterEqual(len(nodos), 65)
        self.assertEqual(len(nodos), len(set(nodos)))
        self.assertGreaterEqual(len(celdas), 10)
        self.assertEqual({z.tipo.value for z in partida.zombies}, {"caminante", "corredor", "horda", "dormido"})
        self.assertTrue(all(z.estado is EstadoZombie.DORMIDO for z in partida.zombies if z.tipo.value == "dormido"))

    def test_cantidad_explicita_de_zombies_se_respeta_en_el_escenario(self) -> None:
        ruta_manta = Path(__file__).resolve().parents[1] / "data/maps/manta-hackathon-v1.json"
        contexto = crear_contexto_demo(
            ruta_manta,
            semilla=321,
            escenario="mixto",
            cantidad_sobrevivientes=20,
            cantidad_zombies=17,
            preparar_inicial=False,
        )
        partida = contexto.snapshots.obtener(contexto.run_id).partida
        self.assertEqual(len(partida.zombies), 17)
        self.assertEqual({z.tipo.value for z in partida.zombies}, {"caminante", "corredor", "horda", "dormido"})

    def test_misma_semilla_reproduce_amenazas_y_eventos_ciudad(self) -> None:
        ruta_manta = Path(__file__).resolve().parents[1] / "data/maps/manta-hackathon-v1.json"
        argumentos = dict(
            semilla=77,
            escenario="mixto",
            cantidad_sobrevivientes=20,
            intensidad="alta",
            eventos_ciudad=True,
        )
        primero = crear_contexto_demo(ruta_manta, **argumentos)
        repetido = crear_contexto_demo(ruta_manta, **argumentos)
        inicial = primero.snapshots.obtener(primero.run_id)
        repetido_inicial = repetido.snapshots.obtener(repetido.run_id)

        self.assertEqual(
            tuple((z.tipo, z.nodo, z.fase_movimiento) for z in inicial.partida.zombies),
            tuple((z.tipo, z.nodo, z.fase_movimiento) for z in repetido_inicial.partida.zombies),
        )
        self.assertEqual(inicial.eventos_programados, repetido_inicial.eventos_programados)
        self.assertGreaterEqual(len(inicial.eventos_programados), 1)
        self.assertLessEqual(len(inicial.eventos_programados), 10)
        self.assertEqual(
            tuple(evento.turno_objetivo for evento in inicial.eventos_programados),
            tuple(2 + 3 * indice for indice in range(len(inicial.eventos_programados))),
        )
        self.assertEqual(
            len({segmento for evento in inicial.eventos_programados for segmento in evento.segmentos}),
            len(inicial.eventos_programados),
        )
        cantidades = {
            len(crear_eventos_ciudad(primero.grafo, "alta", random.Random(semilla)))
            for semilla in range(20)
        }
        self.assertGreater(len(cantidades), 1)

    def test_presets_de_reto_respetan_tipos_y_eventos_reproducibles(self) -> None:
        ruta_manta = Path(__file__).resolve().parents[1] / "data/maps/manta-hackathon-v1.json"
        uno = crear_contexto_demo(ruta_manta, semilla=123, ronda_reto=1, preparar_inicial=False)
        dos_a = crear_contexto_demo(ruta_manta, semilla=123, ronda_reto=2, preparar_inicial=False)
        dos_b = crear_contexto_demo(ruta_manta, semilla=123, ronda_reto=2, preparar_inicial=False)
        dos_otra_semilla = crear_contexto_demo(ruta_manta, semilla=124, ronda_reto=2, preparar_inicial=False)
        tres_a = crear_contexto_demo(ruta_manta, semilla=123, ronda_reto=3, preparar_inicial=False)
        tres_b = crear_contexto_demo(ruta_manta, semilla=123, ronda_reto=3, preparar_inicial=False)
        s1 = uno.snapshots.obtener(uno.run_id)
        s2a, s2b = dos_a.snapshots.obtener(dos_a.run_id), dos_b.snapshots.obtener(dos_b.run_id)
        s3a, s3b = tres_a.snapshots.obtener(tres_a.run_id), tres_b.snapshots.obtener(tres_b.run_id)

        self.assertEqual(len(s1.partida.sobrevivientes), 20)
        self.assertEqual(_conteos_por_sector(uno.grafo, s1.partida.sobrevivientes), (5, 5, 5, 5))
        self.assertEqual({z.tipo.value for z in s1.partida.zombies}, {"caminante"})
        self.assertEqual(s1.eventos_programados, ())
        self.assertEqual(len(s2a.partida.sobrevivientes), 80)
        self.assertEqual(_conteos_por_sector(dos_a.grafo, s2a.partida.sobrevivientes), (20, 20, 20, 20))
        self.assertEqual(
            tuple(item.nodo for item in s2a.partida.sobrevivientes),
            tuple(item.nodo for item in s2b.partida.sobrevivientes),
        )
        self.assertNotEqual(
            tuple(item.nodo for item in s2a.partida.sobrevivientes),
            tuple(
                item.nodo
                for item in dos_otra_semilla.snapshots.obtener(dos_otra_semilla.run_id).partida.sobrevivientes
            ),
        )
        self.assertEqual({z.tipo.value for z in s2a.partida.zombies}, {"caminante", "corredor", "horda"})
        self.assertEqual(s2a.eventos_programados, s2b.eventos_programados)
        self.assertEqual(len(s2a.eventos_programados), 1)
        puente_id = next(iter(s2a.eventos_programados[0].segmentos))
        self.assertEqual(s2a.eventos_programados[0].turno_objetivo, 0)
        self.assertTrue(any(c.segmento_id == puente_id and c.tipo.value == "puente" for c in dos_a.grafo.mapa.calles))
        r2_listo = crear_contexto_demo(ruta_manta, semilla=123, ronda_reto=2)
        snapshot_r2_listo = r2_listo.snapshots.obtener(r2_listo.run_id)
        self.assertIn("EV-RETO-R2-PUENTE", snapshot_r2_listo.eventos_aplicados)
        self.assertIn(puente_id, snapshot_r2_listo.segmentos_cerrados)
        self.assertEqual(len(s3a.partida.sobrevivientes), 200)
        self.assertEqual(_conteos_por_sector(tres_a.grafo, s3a.partida.sobrevivientes), (50, 50, 50, 50))
        self.assertEqual({z.tipo.value for z in s3a.partida.zombies}, {"caminante", "corredor", "horda", "dormido"})
        self.assertEqual(s3a.eventos_programados, s3b.eventos_programados)
        self.assertEqual(len(s3a.eventos_programados), 2)
        self.assertEqual({e.turno_objetivo for e in s3a.eventos_programados}, {50, 100})

    def test_reto_usa_nodos_unicos_elegibles_en_los_cuatro_sectores(self) -> None:
        ruta_manta = Path(__file__).resolve().parents[1] / "data/maps/manta-hackathon-v1.json"
        contexto = crear_contexto_demo(
            ruta_manta,
            semilla=7081,
            ronda_reto=3,
            preparar_inicial=False,
        )
        habitantes = contexto.snapshots.obtener(contexto.run_id).partida.sobrevivientes
        refugios = {refugio.nodo for refugio in contexto.grafo.mapa.refugios}
        nodos_elegibles = set(_nodos_inicio_elegibles(contexto.grafo, refugios))

        self.assertEqual(len({persona.nodo for persona in habitantes}), len(habitantes))
        self.assertTrue(
            all(persona.nodo in nodos_elegibles for persona in habitantes)
        )
        self.assertEqual(_conteos_por_sector(contexto.grafo, habitantes), (50, 50, 50, 50))

    def test_reto_concentra_cada_tipo_de_zombie_y_eventos_en_el_centro(self) -> None:
        ruta_manta = Path(__file__).resolve().parents[1] / "data/maps/manta-hackathon-v1.json"
        for ronda in (1, 2, 3):
            contexto = crear_contexto_demo(
                ruta_manta, semilla=900 + ronda, ronda_reto=ronda, preparar_inicial=False
            )
            snapshot = contexto.snapshots.obtener(contexto.run_id)
            coordenadas = {
                nodo.id: (nodo.lat, nodo.lng) for nodo in contexto.grafo.mapa.nodos
            }
            por_tipo: dict[str, list] = {}
            for zombie in snapshot.partida.zombies:
                por_tipo.setdefault(zombie.tipo.value, []).append(zombie)
            for zombies in por_tipo.values():
                centrales = sum(
                    _distancia_metros(coordenadas[zombie.nodo], CENTRO_URBANO_RETO)
                    <= RADIO_FOCO_AMENAZAS_RETO_M
                    for zombie in zombies
                )
                self.assertGreaterEqual(centrales, round(len(zombies) * 0.8))

            for evento in snapshot.eventos_programados:
                for segmento in evento.segmentos:
                    puntos = [
                        (
                            (coordenadas[calle.origen][0] + coordenadas[calle.destino][0]) / 2,
                            (coordenadas[calle.origen][1] + coordenadas[calle.destino][1]) / 2,
                        )
                        for calle in contexto.grafo.mapa.calles
                        if calle.segmento_id == segmento
                    ]
                    centro_segmento = (
                        sum(lat for lat, _ in puntos) / len(puntos),
                        sum(lng for _, lng in puntos) / len(puntos),
                    )
                    self.assertLessEqual(
                        _distancia_metros(centro_segmento, CENTRO_URBANO_RETO),
                        RADIO_FOCO_AMENAZAS_RETO_M,
                    )

    def test_simulador_libre_no_usa_el_foco_urbano_de_reto(self) -> None:
        ruta_manta = Path(__file__).resolve().parents[1] / "data/maps/manta-hackathon-v1.json"
        contexto = crear_contexto_demo(
            ruta_manta,
            semilla=44,
            escenario="mixto",
            cantidad_sobrevivientes=20,
            intensidad="alta",
            preparar_inicial=False,
        )
        coordenadas = {nodo.id: (nodo.lat, nodo.lng) for nodo in contexto.grafo.mapa.nodos}
        zombies = contexto.snapshots.obtener(contexto.run_id).partida.zombies

        self.assertTrue(
            any(
                _distancia_metros(coordenadas[zombie.nodo], CENTRO_URBANO_RETO)
                > RADIO_FOCO_AMENAZAS_RETO_M
                for zombie in zombies
            )
        )

    def test_simulador_libre_conserva_spawn_en_toda_la_zona_jugable(self) -> None:
        ruta_manta = Path(__file__).resolve().parents[1] / "data/maps/manta-hackathon-v1.json"
        contexto = crear_contexto_demo(
            ruta_manta,
            semilla=123,
            cantidad_sobrevivientes=20,
            preparar_inicial=False,
        )
        coordenadas = {nodo.id: (nodo.lat, nodo.lng) for nodo in contexto.grafo.mapa.nodos}
        posiciones = (
            coordenadas[persona.nodo]
            for persona in contexto.snapshots.obtener(contexto.run_id).partida.sobrevivientes
        )

        self.assertTrue(
            any(
                min(
                    _distancia_metros(posicion, (lat, lng))
                    for _, lat, lng in SECTORES_SPAWN_RETO
                )
                > RADIO_ZONA_SPAWN_RETO_M
                for posicion in posiciones
            )
        )

    def test_nueva_partida_obtiene_semilla_y_run_id_independientes(self) -> None:
        with patch("navira.demo.secrets.randbits", side_effect=(101, 202)):
            primera = crear_contexto_demo()
            segunda = crear_contexto_demo()

        self.assertEqual((primera.semilla, segunda.semilla), (101, 202))
        self.assertNotEqual(primera.run_id, segunda.run_id)

    def test_demo_abre_turno_activo_y_planifica_hacia_refugio(self) -> None:
        contexto = crear_contexto_demo(semilla=31)
        sobreviviente = contexto.snapshots.obtener(contexto.run_id).partida.sobrevivientes[0]

        decision = contexto.servicio_decision.ejecutar(
            SolicitudPaso(sobreviviente.id, sobreviviente.nodo, 0)
        )

        self.assertIn(decision.siguiente_nodo, contexto.grafo.vecinos_desde(sobreviviente.nodo))

    def test_repetir_solicitud_no_avanza_ni_cambia_decision_del_snapshot(self) -> None:
        contexto = crear_contexto_demo(semilla=303)
        sobreviviente = contexto.snapshots.obtener(contexto.run_id).partida.sobrevivientes[0]
        solicitud = SolicitudPaso(sobreviviente.id, sobreviviente.nodo, 0)

        primera = contexto.servicio_decision.ejecutar(solicitud)
        repetida = contexto.servicio_decision.ejecutar(solicitud)

        self.assertEqual(primera, repetida)
        self.assertEqual(contexto.snapshots.obtener(contexto.run_id).version, 1)

    def test_app_demo_usa_planificador_en_la_ruta_http(self) -> None:
        contexto = crear_contexto_demo(semilla=31)
        sobreviviente = contexto.snapshots.obtener(contexto.run_id).partida.sobrevivientes[0]
        app = crear_app_demo(semilla=31, seguridad=ConfiguracionSeguridad(api_key="demo-test-key"))
        respuesta = TestClient(app).post(
            "/paso",
            headers={"x-api-key": "demo-test-key"},
            json={
                "sobrevivienteId": sobreviviente.id,
                "nodoActual": sobreviviente.nodo,
                "turno": 0,
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(set(respuesta.json()), {"siguienteNodo"})

    def test_app_demo_admite_la_misma_cohorte_para_pruebas_http(self) -> None:
        contexto = crear_contexto_demo(semilla=17, cantidad_sobrevivientes=20)
        sobreviviente = contexto.snapshots.obtener(contexto.run_id).partida.sobrevivientes[-1]
        app = crear_app_demo(
            semilla=17,
            cantidad_sobrevivientes=20,
            seguridad=ConfiguracionSeguridad(api_key="demo-test-key"),
        )
        respuesta = TestClient(app).post(
            "/paso",
            headers={"x-api-key": "demo-test-key"},
            json={
                "sobrevivienteId": sobreviviente.id,
                "nodoActual": sobreviviente.nodo,
                "turno": 0,
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(set(respuesta.json()), {"siguienteNodo"})

    def test_variables_de_entorno_configuran_cohorte_del_servidor(self) -> None:
        contexto = crear_contexto_demo(semilla=19, cantidad_sobrevivientes=20)
        sobreviviente = contexto.snapshots.obtener(contexto.run_id).partida.sobrevivientes[-1]
        configuracion = {
            "NAVIRA_DEMO": "1",
            "NAVIRA_DEMO_SEED": "19",
            "NAVIRA_DEMO_SURVIVORS": "20",
            "NAVIRA_DEMO_SCENARIO": "libre",
            "NAVIRA_API_KEY": "demo-test-key",
        }
        with patch.dict(os.environ, configuracion, clear=True):
            app = _crear_app_configurada()
            respuesta = TestClient(app).post(
                "/paso",
                headers={"x-api-key": "demo-test-key"},
                json={
                    "sobrevivienteId": sobreviviente.id,
                    "nodoActual": sobreviviente.nodo,
                    "turno": 0,
                },
            )

        self.assertEqual(respuesta.status_code, 200)

    def test_control_demo_local_se_cablea_desde_el_entorno(self) -> None:
        with patch.dict(os.environ, {"NAVIRA_DEMO": "1", "NAVIRA_LOCAL_DEMO_CONTROL": "1"}, clear=True):
            self.assertTrue(_crear_app_configurada().state.seguridad.control_demo_local)
        with patch.dict(os.environ, {"NAVIRA_DEMO": "1"}, clear=True):
            self.assertFalse(_crear_app_configurada().state.seguridad.control_demo_local)

    def test_repr_de_seguridad_no_expone_api_key(self) -> None:
        self.assertNotIn("secreto", repr(ConfiguracionSeguridad(api_key="secreto")))

    def test_juego_demo_opt_in_arranca_reloj_y_reutiliza_personaje(self) -> None:
        configuracion = {
            "NAVIRA_GAME_DEMO": "1",
            "NAVIRA_DEMO_SEED": "45",
            "NAVIRA_DEMO_SCENARIO": "libre",
            "NAVIRA_DEMO_SURVIVORS": "1",
            "NAVIRA_COOKIE_SECURE": "0",
        }
        with patch.dict(os.environ, configuracion, clear=True):
            app = _crear_app_configurada()
            with TestClient(app, base_url="https://testserver") as client:
                primera = client.post("/juego/unirse", headers={"Origin": "https://testserver"})
                self.assertEqual(primera.status_code, 200)
                run_id = primera.json()["runId"]
                limite = time.monotonic() + 3.0
                estado = client.get("/panel/estado").json()
                while estado.get("turno", 0) < 1 and time.monotonic() < limite:
                    time.sleep(0.05)
                    estado = client.get("/panel/estado").json()
                segunda = client.post("/juego/unirse", headers={"Origin": "https://testserver"})

                self.assertEqual(estado["modo"], "juego")
                self.assertGreaterEqual(estado["turno"], 1)
                self.assertEqual(segunda.status_code, 200)
                self.assertEqual(segunda.json()["jugadorId"], primera.json()["jugadorId"])
                self.assertEqual(sum(
                    personaje["control"] == "humano"
                    for personaje in estado["sobrevivientes"]
                ), 1)
                self.assertEqual(segunda.json()["runId"], run_id)

    def test_demo_se_activa_solo_con_variable_explicita(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            aplicacion = crear_app()

        self.assertEqual(
            aplicacion.state.decidir_paso.ejecutar(
                SolicitudPaso("desconocido", "D-001", 0)
            ).siguiente_nodo,
            "D-001",
        )


def _conteos_por_sector(grafo, habitantes) -> tuple[int, ...]:
    coordenadas = {nodo.id: (nodo.lat, nodo.lng) for nodo in grafo.mapa.nodos}
    conteos = [0] * len(SECTORES_SPAWN_RETO)
    for persona in habitantes:
        posicion = coordenadas[persona.nodo]
        distancias = tuple(
            _distancia_metros(posicion, (lat, lng))
            for _, lat, lng in SECTORES_SPAWN_RETO
        )
        sector = min(range(len(distancias)), key=distancias.__getitem__)
        if distancias[sector] > RADIO_ZONA_SPAWN_RETO_M:
            return tuple(-1 for _ in conteos)
        conteos[sector] += 1
    return tuple(conteos)


if __name__ == "__main__":
    unittest.main()
