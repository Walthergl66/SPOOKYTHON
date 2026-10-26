"""Pruebas de sesión propietaria y aparición segura del modo humano."""

from __future__ import annotations

import random
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from fastapi.testclient import TestClient

from navira.adapters.mapas_memoria import CatalogoMapasMemoria
from navira.adapters.ordenes_memoria import RepositorioOrdenesMemoria
from navira.adapters.snapshots_memoria import AlmacenSnapshotsMemoria
from navira.application.juego import (
    AparicionNoDisponible,
    ConsultarSesionJuego,
    EstadoSesion,
    JuegoNoDisponible,
    PropietarioOcupado,
    RepositorioSesionesMemoria,
    SesionExpirada,
    UnirseAJuego,
)
from navira.application.ordenes import RegistrarOrdenHumana
from navira.application.puerta_decisiones import PuertaDecisiones
from navira.domain.mapa import Calle, Grafo, Mapa, Nodo, Refugio, TipoCalle
from navira.domain.modelo import (
    ControlSobreviviente,
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
from navira.simulation.coordinador import (
    SnapshotMundo,
    abrir_siguiente_turno,
    crear_snapshot_inicial,
    preparar_turno_versionado,
    resolver_turno_versionado,
)


def crear_grafo_juego() -> Grafo:
    nodos = tuple(Nodo(f"N-{i}", -0.95 - i * 0.001, -80.72 - i * 0.001) for i in range(1, 6))
    calles = []
    for i in range(1, 5):
        calles.extend((
            Calle(f"E-{i}{i+1}", f"S-{i}{i+1}", f"N-{i}", f"N-{i+1}", 100, TipoCalle.CALLE, 30),
            Calle(f"E-{i+1}{i}", f"S-{i}{i+1}", f"N-{i+1}", f"N-{i}", 100, TipoCalle.CALLE, 30),
        ))
    return Grafo(
        Mapa(
            "juego-fixture-v1",
            nodos,
            tuple(calles),
            (Refugio("R-1", "N-1"), Refugio("R-5", "N-5")),
        )
    )


class JuegoSesionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo = crear_grafo_juego()
        self.snapshots = AlmacenSnapshotsMemoria()
        self.sesiones = RepositorioSesionesMemoria()
        self.partida = Partida(
            run_id="run-juego",
            modo=ModoPartida.JUEGO,
            escenario="fixture",
            map_version=self.grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-NPC", "N-2"),),
            zombies=(Zombie("Z-1", TipoZombie.CAMINANTE, "N-3", EstadoZombie.ACTIVO),),
            estado=EstadoPartida.ACTIVA,
            turno=0,
            fase=FaseTurno.PREPARACION,
        )
        self.inicial = crear_snapshot_inicial(self.partida, self.grafo, rng=random.Random(23))
        self.assertTrue(self.snapshots.insertar_inicial(self.inicial))
        self.servicio = UnirseAJuego(
            self.snapshots, CatalogoMapasMemoria((self.grafo,)), self.sesiones
        )

    def test_aparece_en_nodo_eligible_y_repetir_cookie_recupera_la_misma_sesion(self) -> None:
        primera = self.servicio.ejecutar()
        guardada = self.snapshots.obtener(self.partida.run_id)
        personaje = next(
            item for item in guardada.partida.sobrevivientes
            if item.id == primera.sesion.sobreviviente_id
        )

        self.assertEqual(primera.sesion.estado, EstadoSesion.ACTIVO)
        self.assertEqual(personaje.control, ControlSobreviviente.HUMANO)
        self.assertEqual(personaje.nodo, "N-4")
        self.assertNotIn(
            personaje.nodo,
            {zombie.nodo for zombie in guardada.partida.zombies if zombie.estado is EstadoZombie.ACTIVO},
        )
        self.assertEqual(primera.sesion.nodo, "N-4")
        repetida = self.servicio.ejecutar(primera.token)
        self.assertEqual(repetida.sesion, primera.sesion)
        self.assertEqual(self.snapshots.obtener(self.partida.run_id).version, 1)

    def test_segundo_visitante_no_roba_personaje(self) -> None:
        self.servicio.ejecutar()

        with self.assertRaises(PropietarioOcupado):
            self.servicio.ejecutar()

    def test_sesion_expirada_no_transfiere_el_personaje_a_otra_cookie(self) -> None:
        ahora = [100.0]
        sesiones = RepositorioSesionesMemoria(
            inactividad_segundos=30.0,
            reloj_monotonico=lambda: ahora[0],
        )
        servicio = UnirseAJuego(self.snapshots, CatalogoMapasMemoria((self.grafo,)), sesiones)
        primera = servicio.ejecutar()
        ahora[0] += 30.0

        with self.assertRaises(SesionExpirada):
            servicio.ejecutar(primera.token)
        with self.assertRaises(PropietarioOcupado):
            servicio.ejecutar()
        self.assertTrue(sesiones.expirada(primera.token))

    def test_actividad_valida_renueva_el_plazo_de_inactividad(self) -> None:
        ahora = [100.0]
        sesiones = RepositorioSesionesMemoria(
            inactividad_segundos=30.0,
            reloj_monotonico=lambda: ahora[0],
        )
        self.assertTrue(sesiones.reservar("token", self.partida.run_id, "S-HUMANO"))
        ahora[0] += 20.0
        self.assertIsNotNone(sesiones.obtener("token"))
        ahora[0] += 20.0

        self.assertIsNotNone(sesiones.obtener("token"))
        self.assertFalse(sesiones.expirada("token"))

    def test_http_indica_sesion_vencida_y_no_crea_personaje_nuevo(self) -> None:
        ahora = [100.0]
        sesiones = RepositorioSesionesMemoria(
            inactividad_segundos=30.0,
            reloj_monotonico=lambda: ahora[0],
        )
        servicio = UnirseAJuego(self.snapshots, CatalogoMapasMemoria((self.grafo,)), sesiones)
        cliente = TestClient(crear_app(unirse_juego=servicio), base_url="https://testserver")
        primera = cliente.post("/juego/unirse", headers={"Origin": "https://testserver"})
        self.assertEqual(primera.status_code, 200)
        ahora[0] += 30.0

        vencida = cliente.post("/juego/unirse", headers={"Origin": "https://testserver"})
        self.assertEqual(vencida.status_code, 410)
        self.assertIn("max-age=0", vencida.headers["set-cookie"].lower())
        sin_cookie = TestClient(crear_app(unirse_juego=servicio), base_url="https://testserver")
        otra_cookie = sin_cookie.post("/juego/unirse", headers={"Origin": "https://testserver"})
        self.assertEqual(otra_cookie.status_code, 409)

    def test_http_recuperacion_expirada_borra_cookie_y_responde_410(self) -> None:
        ahora = [100.0]
        sesiones = RepositorioSesionesMemoria(30.0, lambda: ahora[0])
        servicio = UnirseAJuego(self.snapshots, CatalogoMapasMemoria((self.grafo,)), sesiones)
        consulta = ConsultarSesionJuego(self.snapshots, sesiones, RepositorioOrdenesMemoria())
        cliente = TestClient(
            crear_app(unirse_juego=servicio, consultar_sesion_juego=consulta),
            base_url="https://testserver",
        )
        unido = cliente.post("/juego/unirse", headers={"Origin": "https://testserver"})
        self.assertEqual(unido.status_code, 200)
        ahora[0] += 30.0

        respuesta = cliente.get("/juego/mi-personaje")
        self.assertEqual(respuesta.status_code, 410)
        self.assertIn("max-age=0", respuesta.headers["set-cookie"].lower())

    def test_http_accion_expirada_borra_cookie_y_responde_410(self) -> None:
        ahora = [100.0]
        sesiones = RepositorioSesionesMemoria(30.0, lambda: ahora[0])
        servicio = UnirseAJuego(self.snapshots, CatalogoMapasMemoria((self.grafo,)), sesiones)
        registrar = RegistrarOrdenHumana(
            self.snapshots,
            CatalogoMapasMemoria((self.grafo,)),
            sesiones,
            RepositorioOrdenesMemoria(),
            PuertaDecisiones(),
        )
        cliente = TestClient(
            crear_app(unirse_juego=servicio, registrar_orden_juego=registrar),
            base_url="https://testserver",
        )
        unido = cliente.post("/juego/unirse", headers={"Origin": "https://testserver"})
        self.assertEqual(unido.status_code, 200)
        ahora[0] += 30.0

        respuesta = cliente.post(
            "/juego/accion",
            headers={"Origin": "https://testserver"},
            json={
                "runId": self.partida.run_id,
                "turno": 0,
                "personajeId": unido.json()["jugadorId"],
                "siguienteNodo": "N-4",
                "accionId": "expired-action",
            },
        )
        self.assertEqual(respuesta.status_code, 410)
        self.assertIn("max-age=0", respuesta.headers["set-cookie"].lower())

    def test_dos_solicitudes_concurrentes_reservan_un_solo_propietario(self) -> None:
        def intentar_unirse() -> str:
            try:
                return self.servicio.ejecutar().sesion.sobreviviente_id
            except PropietarioOcupado:
                return "ocupado"

        with ThreadPoolExecutor(max_workers=2) as workers:
            resultado = tuple(workers.map(lambda _: intentar_unirse(), range(2)))

        self.assertEqual(sum(valor != "ocupado" for valor in resultado), 1)
        snapshot = self.snapshots.obtener(self.partida.run_id)
        self.assertEqual(sum(item.control is ControlSobreviviente.HUMANO for item in snapshot.partida.sobrevivientes), 1)

    def test_si_ya_paso_preparacion_se_reserva_y_aparece_antes_del_turno_siguiente(self) -> None:
        decisiones, _ = preparar_turno_versionado(self.inicial, self.grafo, version_esperada=0)
        self.assertTrue(self.snapshots.guardar_si_version(self.partida.run_id, 0, decisiones))
        pendiente = self.servicio.ejecutar()
        self.assertEqual(pendiente.sesion.estado, EstadoSesion.ESPERANDO_APARICION)
        self.assertEqual(len(self.snapshots.obtener(self.partida.run_id).partida.sobrevivientes), 1)

        resuelto, _ = resolver_turno_versionado(decisiones, self.grafo, version_esperada=1)
        self.assertTrue(self.snapshots.guardar_si_version(self.partida.run_id, 1, resuelto))
        siguiente = abrir_siguiente_turno(resuelto, version_esperada=2)
        self.assertTrue(self.snapshots.guardar_si_version(self.partida.run_id, 2, siguiente))
        incorporado = self.servicio.incorporar_aparicion_pendiente(self.partida.run_id, 3)
        personaje = next(
            item for item in incorporado.partida.sobrevivientes
            if item.id == pendiente.sesion.sobreviviente_id
        )

        self.assertEqual(personaje.control, ControlSobreviviente.HUMANO)
        self.assertNotIn(personaje.nodo, {"N-1", "N-2", "N-5"})
        self.assertNotIn(
            personaje.nodo,
            {zombie.nodo for zombie in incorporado.partida.zombies if zombie.estado is EstadoZombie.ACTIVO},
        )
        self.assertEqual(self.servicio.ejecutar(pendiente.token).sesion.estado, EstadoSesion.ACTIVO)

    def test_falla_si_no_hay_nodo_elegible_sin_reservar_sesion(self) -> None:
        partida = replace_partida(self.partida, sobrevivientes=(Sobreviviente("S-1", "N-2"), Sobreviviente("S-2", "N-4")))
        snapshot = crear_snapshot_inicial(partida, self.grafo, rng=random.Random(3))
        snapshots = AlmacenSnapshotsMemoria()
        snapshots.insertar_inicial(snapshot)
        servicio = UnirseAJuego(snapshots, CatalogoMapasMemoria((self.grafo,)), self.sesiones)

        with self.assertRaises(AparicionNoDisponible):
            servicio.ejecutar()
        self.assertIsNone(self.sesiones.pendiente(partida.run_id))

    def test_rechaza_simulador_y_partida_ausente(self) -> None:
        partida_simulador = replace_partida(self.partida, modo=ModoPartida.SIMULADOR)
        snapshot_simulador = crear_snapshot_inicial(partida_simulador, self.grafo, rng=random.Random(4))
        snapshots = AlmacenSnapshotsMemoria()
        snapshots.insertar_inicial(snapshot_simulador)
        servicio = UnirseAJuego(snapshots, CatalogoMapasMemoria((self.grafo,)), self.sesiones)
        with self.assertRaises(JuegoNoDisponible):
            servicio.ejecutar()
        with self.assertRaises(JuegoNoDisponible):
            UnirseAJuego(AlmacenSnapshotsMemoria(), CatalogoMapasMemoria((self.grafo,)), self.sesiones).ejecutar()

    def test_endpoint_setea_cookie_segura_y_rechaza_origen_cruzado(self) -> None:
        app = crear_app(unirse_juego=self.servicio)
        cliente = TestClient(app, base_url="https://testserver")
        respuesta = cliente.post("/juego/unirse", headers={"Origin": "https://testserver"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["estado"], "activo")
        cookie = respuesta.headers["set-cookie"].lower()
        self.assertIn("httponly", cookie)
        self.assertIn("secure", cookie)
        self.assertIn("samesite=strict", cookie)
        self.assertIn("navira_player_session", cookie)

        cliente_sin_sesion = TestClient(crear_app(unirse_juego=UnirseAJuego(
            AlmacenSnapshotsMemoria(), CatalogoMapasMemoria((self.grafo,)), RepositorioSesionesMemoria()
        )), base_url="https://testserver")
        cross_origin = cliente_sin_sesion.post("/juego/unirse", headers={"Origin": "https://evil.example"})
        self.assertEqual(cross_origin.status_code, 403)


def replace_partida(partida: Partida, **cambios) -> Partida:
    """Helper de test para no mutar la entidad congelada."""
    return replace(partida, **cambios)


if __name__ == "__main__":
    unittest.main()
