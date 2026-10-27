"""Pruebas del puerto CAS y el adaptador local de snapshots."""

import random
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from navira.adapters.snapshots_memoria import AlmacenSnapshotsMemoria
from navira.application.snapshots import (
    SnapshotObsoleto,
    abrir_siguiente_turno_persistido,
    preparar_turno_persistido,
    resolver_turno_persistido,
)
from navira.domain.mapa import Grafo, cargar_mapa
from navira.domain.modelo import (
    EstadoPartida,
    FaseTurno,
    IntencionMovimiento,
    ModoPartida,
    Partida,
    Sobreviviente,
)
from navira.simulation.coordinador import crear_snapshot_inicial, preparar_turno_versionado


FIXTURE = Path(__file__).parent / "fixtures" / "mapa-minimo.json"


class SnapshotPersistidoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapa = cargar_mapa(FIXTURE)
        self.grafo = Grafo(self.mapa)
        partida = Partida(
            run_id="run-persistido",
            modo=ModoPartida.JUEGO,
            escenario="fixture",
            map_version=self.mapa.version,
            sobrevivientes=(Sobreviviente("S-1", "N-0001"),),
            estado=EstadoPartida.ACTIVA,
            fase=FaseTurno.PREPARACION,
        )
        self.inicial = crear_snapshot_inicial(partida, self.grafo, rng=random.Random(2))
        self.repo = AlmacenSnapshotsMemoria()
        self.assertTrue(self.repo.insertar_inicial(self.inicial))

    def test_flujo_completo_confirma_cada_fase_por_version(self) -> None:
        decisiones = preparar_turno_persistido(
            self.repo, self.grafo, "run-persistido", version_esperada=0
        )
        self.assertEqual(decisiones.version, 1)
        self.assertEqual(decisiones.partida.fase, FaseTurno.DECISIONES)
        with self.assertRaises(SnapshotObsoleto):
            preparar_turno_persistido(
                self.repo, self.grafo, "run-persistido", version_esperada=0
            )

        resuelto, resultado = resolver_turno_persistido(
            self.repo,
            self.grafo,
            "run-persistido",
            version_esperada=1,
            intenciones=(IntencionMovimiento(
                "run-persistido", 0, FaseTurno.DECISIONES, "S-1", "N-0002"
            ),),
        )
        self.assertEqual(resuelto.version, 2)
        self.assertEqual(resuelto.partida.fase, FaseTurno.RESUELTA)
        self.assertEqual(resultado.partida.sobrevivientes[0].nodo, "N-0002")

        siguiente = abrir_siguiente_turno_persistido(
            self.repo, "run-persistido", version_esperada=2
        )
        self.assertEqual(siguiente.version, 3)
        self.assertEqual(siguiente.partida.turno, 1)
        self.assertEqual(siguiente.partida.fase, FaseTurno.PREPARACION)

    def test_dos_escritores_sobre_la_misma_version_solo_confirman_uno(self) -> None:
        barrera = Barrier(2)
        candidato_a, _ = preparar_turno_versionado(
            self.inicial, self.grafo, version_esperada=0
        )
        candidato_b, _ = preparar_turno_versionado(
            self.inicial, self.grafo, version_esperada=0
        )
        def reemplazar(candidato) -> bool:
            barrera.wait()
            return self.repo.guardar_si_version(
                "run-persistido", 0, candidato
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = tuple(executor.map(reemplazar, (candidato_a, candidato_b)))
        self.assertEqual(sorted(resultados), [False, True])
        self.assertEqual(self.repo.obtener("run-persistido").version, 1)

    def test_insertar_run_duplicado_no_sobrescribe(self) -> None:
        self.assertFalse(self.repo.insertar_inicial(self.inicial))
        self.assertEqual(self.repo.obtener("run-persistido").version, 0)


if __name__ == "__main__":
    unittest.main()
