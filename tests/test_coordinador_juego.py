"""Integración del ciclo humano con el snapshot y resolutor compartidos."""

from __future__ import annotations

import random
import unittest

from navira.adapters.mapas_memoria import CatalogoMapasMemoria
from navira.adapters.ordenes_memoria import RepositorioOrdenesMemoria
from navira.adapters.snapshots_memoria import AlmacenSnapshotsMemoria
from navira.application.coordinador_juego import CoordinadorJuego, JuegoIncompatible
from navira.application.decidir_paso import DecidirPaso
from navira.application.juego import RepositorioSesionesMemoria, UnirseAJuego
from navira.application.ordenes import OrdenIncompatible, RegistrarOrdenHumana
from navira.application.puerta_decisiones import PuertaDecisiones
from navira.domain.mapa import Calle, Grafo, Mapa, Nodo, Refugio, TipoCalle
from navira.domain.modelo import EstadoPartida, FaseTurno, ModoPartida, Partida, Sobreviviente, TipoZombie, Zombie
from navira.simulation.coordinador import crear_snapshot_inicial


def crear_grafo() -> Grafo:
    nodos = tuple(Nodo(f"N-{i}", -0.95 - i * 0.001, -80.72 - i * 0.001) for i in range(1, 6))
    calles = tuple(
        Calle(f"E-{origen}{destino}", f"S-{min(origen, destino)}{max(origen, destino)}", f"N-{origen}", f"N-{destino}", 100, TipoCalle.CALLE, 30)
        for origen in range(1, 6)
        for destino in (origen - 1, origen + 1)
        if 1 <= destino <= 5
    )
    return Grafo(Mapa("juego-integracion-v1", nodos, calles, (Refugio("R-1", "N-1"), Refugio("R-5", "N-5"))))


class CoordinadorJuegoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo = crear_grafo()
        self.mapas = CatalogoMapasMemoria((self.grafo,))
        self.snapshots = AlmacenSnapshotsMemoria()
        self.sesiones = RepositorioSesionesMemoria()
        self.ordenes = RepositorioOrdenesMemoria()
        self.reloj = [100.0]
        self.puerta = PuertaDecisiones(lambda: self.reloj[0])
        self.run_id = "juego-integracion"
        partida = Partida(
            run_id=self.run_id,
            modo=ModoPartida.JUEGO,
            escenario="fixture",
            map_version=self.grafo.mapa.version,
            sobrevivientes=(Sobreviviente("NPC-1", "N-3"),),
            zombies=(Zombie("Z-1", TipoZombie.CAMINANTE, "N-5"),),
            estado=EstadoPartida.ACTIVA,
        )
        inicial = crear_snapshot_inicial(partida, self.grafo, rng=random.Random(14))
        self.assertTrue(self.snapshots.insertar_inicial(inicial))
        self.unirse = UnirseAJuego(self.snapshots, self.mapas, self.sesiones)
        self.jugador = self.unirse.ejecutar()
        self.servicio_orden = RegistrarOrdenHumana(
            self.snapshots, self.mapas, self.sesiones, self.ordenes, self.puerta
        )
        self.coordinador = CoordinadorJuego(
            self.snapshots,
            self.mapas,
            self.unirse,
            self.ordenes,
            DecidirPaso(self.snapshots, self.mapas),
            self.puerta,
        )

    def test_orden_humana_y_npc_se_resuelven_juntos_sin_repetir_zombies(self) -> None:
        decisiones = self.coordinador.preparar(self.run_id, version_esperada=1)
        humano = next(
            item for item in decisiones.partida.sobrevivientes
            if item.control.value == "humano"
        )
        grafo = self.grafo
        vecino = next(calle.destino for calle in grafo.calles_desde(humano.nodo))
        orden = self.servicio_orden.ejecutar(
            self.jugador.token,
            run_id=self.run_id,
            turno=decisiones.partida.turno,
            personaje_id=humano.id,
            siguiente_nodo=vecino,
            accion_id="accion-integrada",
        )
        zombie_antes = decisiones.partida.zombies
        with self.assertRaisesRegex(JuegoIncompatible, "todavía no venció"):
            self.coordinador.resolver(self.run_id, version_esperada=decisiones.version)
        self.reloj[0] = 101.8
        resuelto, _ = self.coordinador.resolver(
            self.run_id,
            version_esperada=decisiones.version,
        )
        humano_resuelto = next(item for item in resuelto.partida.sobrevivientes if item.id == humano.id)
        self.assertEqual(humano_resuelto.nodo, vecino)
        self.assertEqual(decisiones.partida.zombies, zombie_antes)
        self.assertEqual(
            self.servicio_orden.ejecutar(
                self.jugador.token,
                run_id=self.run_id,
                turno=decisiones.partida.turno,
                personaje_id=humano.id,
                siguiente_nodo=vecino,
                accion_id="accion-integrada",
            ),
            orden,
        )
        with self.assertRaisesRegex(OrdenIncompatible, "ventana"):
            self.servicio_orden.ejecutar(
                self.jugador.token,
                run_id=self.run_id,
                turno=decisiones.partida.turno,
                personaje_id=humano.id,
                siguiente_nodo=vecino,
                accion_id="accion-tardia",
            )
        with self.assertRaises(JuegoIncompatible):
            self.coordinador.resolver(self.run_id, version_esperada=resuelto.version)

    def test_aparicion_tardia_se_incorpora_antes_del_siguiente_movimiento_zombie(self) -> None:
        snapshots = AlmacenSnapshotsMemoria()
        run_id = "juego-aparicion-tardia"
        partida = Partida(
            run_id=run_id,
            modo=ModoPartida.JUEGO,
            escenario="fixture",
            map_version=self.grafo.mapa.version,
            sobrevivientes=(Sobreviviente("NPC-2", "N-3"),),
            zombies=(Zombie("Z-2", TipoZombie.CAMINANTE, "N-5"),),
            estado=EstadoPartida.ACTIVA,
        )
        inicial = crear_snapshot_inicial(partida, self.grafo, rng=random.Random(18))
        self.assertTrue(snapshots.insertar_inicial(inicial))
        sesiones = RepositorioSesionesMemoria()
        unirse = UnirseAJuego(snapshots, self.mapas, sesiones)
        ordenes = RepositorioOrdenesMemoria()
        reloj = [200.0]
        puerta = PuertaDecisiones(lambda: reloj[0])
        coordinador = CoordinadorJuego(
            snapshots,
            self.mapas,
            unirse,
            ordenes,
            DecidirPaso(snapshots, self.mapas),
            puerta,
        )
        decisiones = coordinador.preparar(run_id, version_esperada=inicial.version)
        sesion_jugador = unirse.ejecutar()
        self.assertIsNone(sesion_jugador.sesion.nodo)
        reloj[0] = 201.8
        resuelto, _ = coordinador.resolver(run_id, version_esperada=decisiones.version)
        siguiente = coordinador.preparar(run_id, version_esperada=resuelto.version)
        jugador = next(
            item for item in siguiente.partida.sobrevivientes
            if item.id == sesion_jugador.sesion.sobreviviente_id
        )
        self.assertEqual(jugador.control.value, "humano")
        self.assertEqual(jugador.nodo, sesiones.obtener(sesion_jugador.token).nodo)
        self.assertEqual(siguiente.partida.fase, FaseTurno.DECISIONES)


if __name__ == "__main__":
    unittest.main()
