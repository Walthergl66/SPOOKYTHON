"""Integración del generador estocástico con el fixture vial de Manta."""

from __future__ import annotations

import unittest

from navira.demo import MAPA_DEMO_POR_DEFECTO, crear_contexto_demo
from navira.domain.mapa import Grafo, cargar_mapa
from navira.simulador_demo import ejecutar_demo


MAPA_MANTA = MAPA_DEMO_POR_DEFECTO.parents[1] / "maps" / "manta-hackathon-v1.json"


class SimulacionMapaMantaTests(unittest.TestCase):
    def test_cohortes_sinteticas_recorran_grafo_manta_con_movimientos_legales(self) -> None:
        grafo = Grafo(cargar_mapa(MAPA_MANTA))
        refugios = {refugio.nodo for refugio in grafo.mapa.refugios}

        for poblacion in (20, 80, 200):
            with self.subTest(poblacion=poblacion):
                contexto = crear_contexto_demo(
                    MAPA_MANTA,
                    semilla=20261026,
                    escenario="mixto",
                    cantidad_sobrevivientes=poblacion,
                )
                iniciales = contexto.snapshots.obtener(contexto.run_id).partida.sobrevivientes
                reportes = ejecutar_demo(
                    turnos=3,
                    semilla=20261026,
                    escenario="mixto",
                    cantidad_sobrevivientes=poblacion,
                    ruta_mapa=MAPA_MANTA,
                )

                self.assertEqual(len(reportes), 3)
                self.assertEqual(reportes[0]["versionMapa"], grafo.mapa.version)
                self.assertTrue(all(reporte["semilla"] == 20261026 for reporte in reportes))
                self.assertEqual(len(iniciales), poblacion)
                self.assertTrue(all(sobreviviente.nodo not in refugios for sobreviviente in iniciales))
                movimientos = [
                    movimiento
                    for reporte in reportes
                    for movimiento in reporte["movimientosSobrevivientes"]
                ]
                self.assertEqual(len(movimientos), 3 * poblacion)
                for movimiento in movimientos:
                    origen = movimiento["desde"]
                    destino = movimiento["hasta"]
                    self.assertIn(destino, (origen, *grafo.vecinos_desde(origen)))


if __name__ == "__main__":
    unittest.main()
