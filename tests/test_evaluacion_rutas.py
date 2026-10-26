"""Pruebas de reproducibilidad del comparador temporal contra Dijkstra."""

from __future__ import annotations

import unittest

from navira.evaluacion_rutas import comparar_politicas
from navira.demo import MAPA_DEMO_POR_DEFECTO


class EvaluacionRutasTests(unittest.TestCase):
    def test_compara_politicas_en_igual_semilla_y_reporta_resultados(self) -> None:
        reporte = comparar_politicas(
            ruta_mapa=MAPA_DEMO_POR_DEFECTO,
            semillas=(17,),
            escenarios=("caminantes",),
            poblaciones=(2,),
            turnos=1,
            horizonte=3,
        )

        self.assertEqual(reporte["resumen"]["pares"], 1)
        par = reporte["comparaciones"][0]
        self.assertEqual(par["semilla"], 17)
        self.assertEqual(par["dijkstra"]["evacuados"] + par["dijkstra"]["mordidos"] + par["dijkstra"]["activos"], 2)
        self.assertEqual(par["temporal"]["evacuados"] + par["temporal"]["mordidos"] + par["temporal"]["activos"], 2)
        self.assertIsNotNone(par["dijkstra"]["p95TiempoPorRecomendacionMs"])
        self.assertIsNotNone(par["temporal"]["p95TiempoPorRecomendacionMs"])

    def test_rechaza_configuracion_vacia_o_fuera_de_rango(self) -> None:
        with self.assertRaises(ValueError):
            comparar_politicas(semillas=(), turnos=1)
        with self.assertRaises(ValueError):
            comparar_politicas(semillas=(1,), escenarios=("oficial",), turnos=1)
        with self.assertRaises(ValueError):
            comparar_politicas(semillas=(1,), poblaciones=(201,), turnos=1)


if __name__ == "__main__":
    unittest.main()
