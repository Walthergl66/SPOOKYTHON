"""Rondas automáticas completas y reanudables desde snapshots versionados."""

from __future__ import annotations

import random
import unittest

from navira.adapters.mapas_memoria import CatalogoMapasMemoria
from navira.adapters.snapshots_memoria import AlmacenSnapshotsMemoria
from navira.application.simulacion_automatica import (
    EjecutarRondaAutomatica,
    SimulacionIncompatible,
)
from navira.application.snapshots import SnapshotObsoleto
from navira.demo import MAPA_DEMO_POR_DEFECTO
from navira.domain.mapa import Grafo, cargar_mapa
from navira.domain.modelo import (
    ControlSobreviviente,
    EstadoPartida,
    FaseTurno,
    ModoPartida,
    Partida,
    Sobreviviente,
    TipoZombie,
    Zombie,
)
from navira.application.snapshots import preparar_turno_persistido
from navira.simulation.coordinador import crear_snapshot_inicial


class SimulacionAutomaticaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo = Grafo(cargar_mapa(MAPA_DEMO_POR_DEFECTO))
        self.snapshots = AlmacenSnapshotsMemoria()
        self.mapas = CatalogoMapasMemoria((self.grafo,))
        partida = Partida(
            run_id="run-simulacion-local",
            modo=ModoPartida.SIMULADOR,
            escenario="demo-sintetico",
            map_version=self.grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-AUTO", "D-001"),),
            estado=EstadoPartida.ACTIVA,
            turno=0,
            fase=FaseTurno.PREPARACION,
        )
        inicial = crear_snapshot_inicial(partida, self.grafo, rng=random.Random(17))
        self.assertTrue(self.snapshots.insertar_inicial(inicial))
        self.ejecutor = EjecutarRondaAutomatica(self.snapshots, self.mapas)

    def test_completa_y_persiste_un_turno_con_decision_dijkstra(self) -> None:
        resultado = self.ejecutor.ejecutar("run-simulacion-local", version_esperada=0)
        vigente = self.snapshots.obtener("run-simulacion-local")

        self.assertEqual(resultado.movimientos_sobrevivientes[0].destino, "D-002")
        self.assertEqual(vigente.partida.fase, FaseTurno.RESUELTA)
        self.assertEqual(vigente.version, 2)

    def test_reanuda_decisiones_persistidas_sin_repetir_preparacion(self) -> None:
        decisiones = preparar_turno_persistido(
            self.snapshots,
            self.grafo,
            "run-simulacion-local",
            version_esperada=0,
        )

        resultado = self.ejecutor.ejecutar(
            "run-simulacion-local", version_esperada=decisiones.version
        )
        vigente = self.snapshots.obtener("run-simulacion-local")

        self.assertEqual(resultado.partida.turno, 0)
        self.assertEqual(resultado.movimientos_sobrevivientes[0].destino, "D-002")
        self.assertEqual(vigente.partida.fase, FaseTurno.RESUELTA)
        self.assertEqual(vigente.version, 2)

    def test_abre_y_completa_el_turno_siguiente(self) -> None:
        self.ejecutor.ejecutar("run-simulacion-local", version_esperada=0)
        version_resuelta = self.snapshots.obtener("run-simulacion-local").version

        siguiente = self.ejecutor.ejecutar(
            "run-simulacion-local", version_esperada=version_resuelta
        )
        vigente = self.snapshots.obtener("run-simulacion-local")

        self.assertEqual(siguiente.partida.turno, 1)
        self.assertEqual(siguiente.movimientos_sobrevivientes[0].destino, "D-003")
        self.assertEqual(vigente.partida.fase, FaseTurno.RESUELTA)
        self.assertEqual(vigente.version, 5)

    def test_mueve_zombie_antes_de_planificar_y_registra_su_trayecto(self) -> None:
        self.snapshots = AlmacenSnapshotsMemoria()
        partida = Partida(
            run_id="run-con-zombie",
            modo=ModoPartida.SIMULADOR,
            escenario="demo-sintetico",
            map_version=self.grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-AUTO", "D-001"),),
            zombies=(Zombie("Z-001", TipoZombie.CAMINANTE, "D-005"),),
            estado=EstadoPartida.ACTIVA,
            turno=0,
            fase=FaseTurno.PREPARACION,
        )
        inicial = crear_snapshot_inicial(partida, self.grafo, rng=random.Random(17))
        self.snapshots.insertar_inicial(inicial)
        ejecutor = EjecutarRondaAutomatica(self.snapshots, self.mapas)

        resultado = ejecutor.ejecutar(partida.run_id, version_esperada=0)

        self.assertEqual(resultado.movimientos_zombies[0].destino, "D-004")
        # The route forecast can keep moving when the post-zombie snapshot
        # exposes no occupied node or dangerous opposite crossing ahead.
        self.assertEqual(resultado.movimientos_sobrevivientes[0].destino, "D-002")

    def test_rechaza_version_antigua_y_modo_juego(self) -> None:
        with self.assertRaises(SnapshotObsoleto):
            self.ejecutor.ejecutar("run-simulacion-local", version_esperada=1)

        snapshot = self.snapshots.obtener("run-simulacion-local")
        juego = Partida(
            run_id=snapshot.partida.run_id,
            modo=ModoPartida.JUEGO,
            escenario=snapshot.partida.escenario,
            map_version=snapshot.partida.map_version,
            sobrevivientes=snapshot.partida.sobrevivientes,
            estado=EstadoPartida.ACTIVA,
            turno=0,
            fase=FaseTurno.PREPARACION,
        )
        otro = AlmacenSnapshotsMemoria()
        otro.insertar_inicial(crear_snapshot_inicial(juego, self.grafo, rng=random.Random(17)))
        ejecutor = EjecutarRondaAutomatica(otro, self.mapas)
        with self.assertRaises(SimulacionIncompatible):
            ejecutor.ejecutar(juego.run_id, version_esperada=0)

    def test_rechaza_control_humano_sin_avanzar_el_mundo(self) -> None:
        partida = Partida(
            run_id="run-con-humano",
            modo=ModoPartida.SIMULADOR,
            escenario="demo-sintetico",
            map_version=self.grafo.mapa.version,
            sobrevivientes=(
                Sobreviviente(
                    "S-HUMANO",
                    "D-001",
                    control=ControlSobreviviente.HUMANO,
                ),
            ),
            estado=EstadoPartida.ACTIVA,
            turno=0,
            fase=FaseTurno.PREPARACION,
        )
        self.snapshots.insertar_inicial(
            crear_snapshot_inicial(partida, self.grafo, rng=random.Random(17))
        )
        ejecutor = EjecutarRondaAutomatica(self.snapshots, self.mapas)

        with self.assertRaises(SimulacionIncompatible):
            ejecutor.ejecutar(partida.run_id, version_esperada=0)

        vigente = self.snapshots.obtener(partida.run_id)
        self.assertEqual(vigente.version, 0)
        self.assertEqual(vigente.partida.fase, FaseTurno.PREPARACION)


if __name__ == "__main__":
    unittest.main()
