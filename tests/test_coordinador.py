"""Pruebas de versionado, eventos y avance completo de un turno."""

import random
import unittest
from dataclasses import replace
from pathlib import Path

from navira.domain.mapa import Grafo, cargar_mapa
from navira.domain.modelo import (
    ControlSobreviviente,
    EstadoPartida,
    FaseTurno,
    IntencionMovimiento,
    ModoPartida,
    Partida,
    Sobreviviente,
    Zombie,
    TipoZombie,
)
from navira.simulation.coordinador import (
    EventoCierre,
    avanzar_turno,
    abrir_siguiente_turno,
    crear_snapshot_inicial,
    preparar_turno_versionado,
    resolver_turno_versionado,
)
from navira.simulation.reloj import VentanaTurno


FIXTURE = Path(__file__).parent / "fixtures" / "mapa-minimo.json"


class CoordinadorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapa = cargar_mapa(FIXTURE)
        self.grafo = Grafo(self.mapa)
        self.partida = Partida(
            run_id="run-coordinador",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=self.mapa.version,
            zombies=(Zombie("Z-1", TipoZombie.CAMINANTE, "N-0001"),),
            estado=EstadoPartida.ACTIVA,
            fase=FaseTurno.PREPARACION,
        )

    def test_avance_devuelve_snapshots_completos_y_versiones_distintas(self) -> None:
        inicial = crear_snapshot_inicial(self.partida, self.grafo, rng=random.Random(7))
        turno = avanzar_turno(inicial, self.grafo, version_esperada=0)
        self.assertEqual(turno.decisiones.partida.fase, FaseTurno.DECISIONES)
        self.assertEqual(turno.resuelto.partida.fase, FaseTurno.RESUELTA)
        self.assertEqual(turno.decisiones.version, 1)
        self.assertEqual(turno.resuelto.version, 2)
        self.assertEqual(turno.decisiones.identidad[0:2], ("run-coordinador", 0))
        self.assertEqual(inicial.partida.fase, FaseTurno.PREPARACION)

    def test_evento_de_cierre_se_aplica_una_vez_y_se_conserva(self) -> None:
        evento = EventoCierre("EV-1", 0, aristas=frozenset({"E-0001"}), causa="puente")
        inicial = crear_snapshot_inicial(
            self.partida, self.grafo, rng=random.Random(7), eventos=(evento,)
        )
        primer_turno = avanzar_turno(inicial, self.grafo, version_esperada=0)
        self.assertEqual(primer_turno.eventos_aplicados_ahora, ("EV-1",))
        self.assertEqual(primer_turno.resuelto.aristas_cerradas, frozenset({"E-0001"}))
        self.assertEqual(primer_turno.resuelto.partida.zombies[0].nodo, "N-0001")

        siguiente = abrir_siguiente_turno(primer_turno.resuelto, version_esperada=2)
        segundo_turno = avanzar_turno(siguiente, self.grafo, version_esperada=3)
        self.assertEqual(segundo_turno.eventos_aplicados_ahora, ())
        self.assertEqual(segundo_turno.resuelto.eventos_aplicados, ("EV-1",))

    def test_version_obsoleta_no_avanza_y_solo_resuelto_abre_turno(self) -> None:
        inicial = crear_snapshot_inicial(self.partida, self.grafo, rng=random.Random(1))
        with self.assertRaisesRegex(ValueError, "versión esperada"):
            avanzar_turno(inicial, self.grafo, version_esperada=4)
        with self.assertRaisesRegex(ValueError, "solo se abre"):
            abrir_siguiente_turno(inicial, version_esperada=0)

        resuelto = avanzar_turno(inicial, self.grafo, version_esperada=0).resuelto
        siguiente = abrir_siguiente_turno(resuelto, version_esperada=2)
        self.assertEqual(siguiente.partida.turno, 1)
        self.assertEqual(siguiente.partida.fase, FaseTurno.PREPARACION)
        self.assertEqual(siguiente.version, 3)

    def test_evento_rechaza_referencias_desconocidas(self) -> None:
        evento = EventoCierre("EV-1", 0, segmentos=frozenset({"segmento-inexistente"}))
        with self.assertRaisesRegex(ValueError, "segmento desconocido"):
            crear_snapshot_inicial(self.partida, self.grafo, rng=random.Random(1), eventos=(evento,))

    def test_flujo_humano_separa_decision_del_movimiento_zombie(self) -> None:
        con_personaje = replace(
            self.partida,
            modo=ModoPartida.JUEGO,
            sobrevivientes=(Sobreviviente("S-1", "N-0003", control=ControlSobreviviente.HUMANO),),
        )
        inicial = crear_snapshot_inicial(con_personaje, self.grafo, rng=random.Random(4))
        decisiones, _ = preparar_turno_versionado(
            inicial, self.grafo, version_esperada=0
        )
        self.assertEqual(decisiones.partida.fase, FaseTurno.DECISIONES)
        zombies_tras_preparar = decisiones.partida.zombies
        resultado, aplicado = resolver_turno_versionado(
            decisiones,
            self.grafo,
            version_esperada=decisiones.version,
            intenciones=(IntencionMovimiento(
                "run-coordinador", 0, FaseTurno.DECISIONES, "S-1", "N-0004"
            ),),
        )
        self.assertEqual(decisiones.partida.zombies, zombies_tras_preparar)
        self.assertEqual(resultado.partida.fase, FaseTurno.RESUELTA)
        self.assertEqual(aplicado.partida.sobrevivientes[0].nodo, "N-0004")

    def test_partida_finalizada_no_avanza(self) -> None:
        finalizada = replace(self.partida, estado=EstadoPartida.FINALIZADA)
        snapshot = crear_snapshot_inicial(finalizada, self.grafo, rng=random.Random(1))
        with self.assertRaisesRegex(ValueError, "partida activa"):
            avanzar_turno(snapshot, self.grafo, version_esperada=0)


class RelojTests(unittest.TestCase):
    def test_plazo_absoluto_y_retraso(self) -> None:
        ventana = VentanaTurno(inicio_monotonic_s=10.0)
        self.assertEqual(ventana.deadline_monotonic_s, 12.0)
        self.assertEqual(ventana.restante_s(11.25), 0.75)
        self.assertEqual(ventana.restante_s(12.1), 0.0)
        self.assertAlmostEqual(ventana.retraso_s(12.1), 0.1)


if __name__ == "__main__":
    unittest.main()
