"""Regresiones de propiedad, validación e idempotencia de órdenes humanas."""

from __future__ import annotations

import random
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from fastapi.testclient import TestClient

from navira.adapters.mapas_memoria import CatalogoMapasMemoria
from navira.adapters.ordenes_memoria import RepositorioOrdenesMemoria
from navira.adapters.snapshots_memoria import AlmacenSnapshotsMemoria
from navira.adapters.sesiones_memoria import RepositorioSesionesMemoria
from navira.application.juego import UnirseAJuego
from navira.application.ordenes import (
    OrdenIdempotenciaConflict,
    OrdenIncompatible,
    RegistrarOrdenHumana,
    SesionNoAutorizada,
)
from navira.application.juego import ConsultarSesionJuego
from navira.domain.mapa import Calle, Grafo, Mapa, Nodo, Refugio, TipoCalle
from navira.domain.modelo import (
    EstadoPartida,
    EstadoZombie,
    FaseTurno,
    ModoPartida,
    Partida,
    Sobreviviente,
    TipoZombie,
    Zombie,
)
from navira.main import crear_app
from navira.simulation.coordinador import crear_snapshot_inicial


def crear_grafo() -> Grafo:
    nodos = tuple(Nodo(f"N-{i}", -0.95 - i * 0.001, -80.72 - i * 0.001) for i in range(1, 6))
    calles: list[Calle] = []
    for i in range(1, 5):
        calles.extend((
            Calle(f"E-{i}{i+1}", f"S-{i}{i+1}", f"N-{i}", f"N-{i+1}", 100, TipoCalle.CALLE, 30),
            Calle(f"E-{i+1}{i}", f"S-{i}{i+1}", f"N-{i+1}", f"N-{i}", 100, TipoCalle.CALLE, 30),
        ))
    return Grafo(Mapa(
        "orden-fixture-v1",
        nodos,
        tuple(calles),
        (Refugio("R-1", "N-1"), Refugio("R-5", "N-5")),
    ))


class OrdenesJuegoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo = crear_grafo()
        self.snapshots = AlmacenSnapshotsMemoria()
        self.sesiones = RepositorioSesionesMemoria()
        self.ordenes = RepositorioOrdenesMemoria()
        partida = Partida(
            run_id="run-ordenes",
            modo=ModoPartida.JUEGO,
            escenario="fixture",
            map_version=self.grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-NPC", "N-2"),),
            zombies=(Zombie("Z-1", TipoZombie.CAMINANTE, "N-3", EstadoZombie.ACTIVO),),
            estado=EstadoPartida.ACTIVA,
            turno=0,
            fase=FaseTurno.PREPARACION,
        )
        inicial = crear_snapshot_inicial(partida, self.grafo, rng=random.Random(23))
        self.assertTrue(self.snapshots.insertar_inicial(inicial))
        self.unirse = UnirseAJuego(self.snapshots, CatalogoMapasMemoria((self.grafo,)), self.sesiones)
        self.session = self.unirse.ejecutar()
        self.personaje = self.session.sesion.sobreviviente_id
        snapshot = self.snapshots.obtener(partida.run_id)
        decisions = replace(
            snapshot,
            partida=replace(snapshot.partida, fase=FaseTurno.DECISIONES),
            version=snapshot.version + 1,
        )
        self.assertTrue(self.snapshots.guardar_si_version(partida.run_id, snapshot.version, decisions))
        self.servicio = RegistrarOrdenHumana(
            self.snapshots, CatalogoMapasMemoria((self.grafo,)), self.sesiones, self.ordenes
        )

    def enviar(self, *, token: str | None = None, action: str = "a-1", destino: str = "N-3"):
        return self.servicio.ejecutar(
            self.session.token if token is None else token,
            run_id="run-ordenes",
            turno=0,
            personaje_id=self.personaje,
            siguiente_nodo=destino,
            accion_id=action,
        )

    def test_orden_aceptada_solo_registra_direccion_sin_mover_mundo(self) -> None:
        snapshot_antes = self.snapshots.obtener("run-ordenes")
        orden = self.enviar(destino="N-3")
        self.assertEqual(orden.secuencia, 1)
        self.assertEqual(orden.version_snapshot, snapshot_antes.version)
        self.assertEqual(self.snapshots.obtener("run-ordenes"), snapshot_antes)
        self.assertEqual(self.ordenes.obtener_turno("run-ordenes", 0), (orden,))

    def test_posicion_confirmada_del_snapshot_prevalece_a_posicion_inicial_de_sesion(self) -> None:
        snapshot = self.snapshots.obtener("run-ordenes")
        sobrevivientes = tuple(
            replace(personaje, nodo="N-2") if personaje.id == self.personaje else personaje
            for personaje in snapshot.partida.sobrevivientes
        )
        movido = replace(
            snapshot,
            partida=replace(snapshot.partida, sobrevivientes=sobrevivientes),
            version=snapshot.version + 1,
        )
        self.assertTrue(self.snapshots.guardar_si_version("run-ordenes", snapshot.version, movido))
        orden = self.enviar(action="desde-posicion-confirmada", destino="N-3")
        self.assertEqual(orden.version_snapshot, movido.version)

    def test_idempotencia_repite_acuse_y_conflicta_si_cambia_el_cuerpo(self) -> None:
        primera = self.enviar(destino="N-3")
        self.assertEqual(self.enviar(destino="N-3"), primera)
        with self.assertRaises(OrdenIdempotenciaConflict):
            self.enviar(destino="N-4")
        self.assertEqual(self.ordenes.obtener_turno("run-ordenes", 0), (primera,))

    def test_ultima_orden_valida_reemplaza_anterior_y_secuencia_es_servidor(self) -> None:
        primera = self.enviar(action="a-1", destino="N-3")
        segunda = self.enviar(action="a-2", destino="N-4")
        self.assertGreater(segunda.secuencia, primera.secuencia)
        self.assertEqual(self.ordenes.obtener_turno("run-ordenes", 0), (segunda,))

    def test_orden_duplicada_concurrente_conserva_un_solo_acuse(self) -> None:
        with ThreadPoolExecutor(max_workers=8) as pool:
            resultados = tuple(pool.map(lambda _: self.enviar(), range(20)))
        self.assertTrue(all(resultado == resultados[0] for resultado in resultados))
        self.assertEqual(resultados[0].secuencia, 1)
        self.assertEqual(self.ordenes.obtener_turno("run-ordenes", 0), (resultados[0],))

    def test_exige_cookie_propietaria_personaje_y_partida(self) -> None:
        with self.assertRaises(SesionNoAutorizada):
            self.servicio.ejecutar(
                None,
                run_id="run-ordenes",
                turno=0,
                personaje_id=self.personaje,
                siguiente_nodo="N-3",
                accion_id="sin-cookie",
            )
        with self.assertRaises(SesionNoAutorizada):
            self.enviar(token="token-invalido")
        with self.assertRaises(SesionNoAutorizada):
            self.servicio.ejecutar(
                self.session.token,
                run_id="otra-partida",
                turno=0,
                personaje_id=self.personaje,
                siguiente_nodo="N-3",
                accion_id="otra",
            )

    def test_rechaza_turno_fase_arista_cerrada_y_destino_ilegal(self) -> None:
        with self.assertRaises(OrdenIncompatible):
            self.servicio.ejecutar(
                self.session.token, run_id="run-ordenes", turno=1,
                personaje_id=self.personaje, siguiente_nodo="N-3", accion_id="turno",
            )
        snapshot = self.snapshots.obtener("run-ordenes")
        cerrado = replace(snapshot, aristas_cerradas=frozenset({"E-43"}), version=snapshot.version + 1)
        self.assertTrue(self.snapshots.guardar_si_version("run-ordenes", snapshot.version, cerrado))
        with self.assertRaises(OrdenIncompatible):
            self.enviar(action="cerrada", destino="N-3")
        with self.assertRaises(OrdenIncompatible):
            self.enviar(action="no-vecino", destino="N-1")

    def test_permite_riesgo_de_zombie_activo_pero_rechaza_bloqueo_de_horda(self) -> None:
        riesgo_permitido = self.enviar(destino="N-3")
        self.assertEqual(riesgo_permitido.siguiente_nodo, "N-3")

        snapshot = self.snapshots.obtener("run-ordenes")
        partida_horda = replace(
            snapshot.partida,
            zombies=(Zombie("Z-HORDA", TipoZombie.HORDA, "N-2", EstadoZombie.ACTIVO),),
        )
        horda_abierta = replace(snapshot, partida=partida_horda, version=snapshot.version + 1)
        self.assertTrue(self.snapshots.guardar_si_version("run-ordenes", snapshot.version, horda_abierta))
        with self.assertRaises(OrdenIncompatible):
            self.enviar(action="horda", destino="N-3")

    def test_fase_cerrada_rechaza_orden_nueva_pero_reintento_idempotente_sigue_disponible(self) -> None:
        aceptada = self.enviar()
        snapshot = self.snapshots.obtener("run-ordenes")
        cerrada = replace(
            snapshot,
            partida=replace(snapshot.partida, fase=FaseTurno.RESUELTA),
            version=snapshot.version + 1,
        )
        self.assertTrue(self.snapshots.guardar_si_version("run-ordenes", snapshot.version, cerrada))
        self.assertEqual(self.enviar(), aceptada)
        with self.assertRaises(OrdenIncompatible):
            self.enviar(action="late")

    def test_endpoint_acusa_sin_exponer_cookie_en_json_y_valida_origen(self) -> None:
        app = crear_app(
            unirse_juego=self.unirse,
            registrar_orden_juego=self.servicio,
        )
        client = TestClient(app, base_url="https://testserver")
        client.cookies.set("navira_player_session", self.session.token, path="/juego")
        body = {
            "runId": "run-ordenes",
            "turno": 0,
            "personajeId": self.personaje,
            "siguienteNodo": "N-3",
            "accionId": "http-1",
        }
        accepted = client.post("/juego/accion", json=body, headers={"Origin": "https://testserver"})
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.json(), {"accionId": "http-1", "secuencia": 1, "estado": "recibida", "turno": 0})
        self.assertNotIn("token", accepted.text)
        self.assertEqual(client.post("/juego/accion", json=body, headers={"Origin": "https://evil.example"}).status_code, 403)

    def test_endpoint_recupera_solo_sesion_existente_y_posicion_actual(self) -> None:
        consulta = ConsultarSesionJuego(self.snapshots, self.sesiones, self.ordenes)
        client = TestClient(crear_app(
            unirse_juego=self.unirse,
            registrar_orden_juego=self.servicio,
            consultar_sesion_juego=consulta,
        ), base_url="https://testserver")
        client.cookies.set("navira_player_session", self.session.token, path="/juego")
        self.enviar(action="restaurable", destino="N-3")

        snapshot = self.snapshots.obtener("run-ordenes")
        actualizados = tuple(
            replace(personaje, nodo="N-2") if personaje.id == self.personaje else personaje
            for personaje in snapshot.partida.sobrevivientes
        )
        movido = replace(snapshot, partida=replace(snapshot.partida, sobrevivientes=actualizados), version=snapshot.version + 1)
        self.assertTrue(self.snapshots.guardar_si_version("run-ordenes", snapshot.version, movido))

        response = client.get("/juego/mi-personaje")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.json(), {
            "runId": "run-ordenes",
            "jugadorId": self.personaje,
            "estado": "activo",
            "nodo": "N-2",
            "estadoPersonaje": "activo",
            "ultimaOrden": {
                "accionId": "restaurable",
                "turno": 0,
                "siguienteNodo": "N-3",
                "secuencia": 1,
            },
        })

    def test_endpoint_recuperacion_no_crea_sesion_si_falta_cookie(self) -> None:
        consulta = ConsultarSesionJuego(self.snapshots, self.sesiones, self.ordenes)
        response = TestClient(crear_app(consultar_sesion_juego=consulta)).get("/juego/mi-personaje")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(self.snapshots.obtener("run-ordenes").partida.sobrevivientes), 2)


if __name__ == "__main__":
    unittest.main()
