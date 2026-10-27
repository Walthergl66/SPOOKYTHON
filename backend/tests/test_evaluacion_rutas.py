"""Pruebas de reproducibilidad del comparador temporal contra Dijkstra."""

from __future__ import annotations

import unittest

from navira.evaluacion_rutas import comparar_politicas
from navira.evaluacion_rutas import _comparar_prioridad
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

    def test_permite_reproducir_la_intensidad_y_eventos_del_panel(self) -> None:
        reporte = comparar_politicas(
            ruta_mapa=MAPA_DEMO_POR_DEFECTO,
            semillas=(31,),
            escenarios=("mixto",),
            poblaciones=(2,),
            turnos=1,
            horizonte=3,
            intensidad="alta",
            eventos_ciudad=True,
        )

        self.assertEqual(reporte["intensidad"], "alta")
        self.assertTrue(reporte["eventosCiudad"])
        self.assertEqual(reporte["comparaciones"][0]["dijkstra"]["evacuados"] + reporte["comparaciones"][0]["dijkstra"]["mordidos"] + reporte["comparaciones"][0]["dijkstra"]["activos"], 2)

    def test_prioriza_menos_mordidos_aunque_haya_menos_evacuados(self) -> None:
        self.assertEqual(
            _comparar_prioridad(
                {"mordidos": 1, "evacuados": 4},
                {"mordidos": 2, "evacuados": 9},
            ),
            "mejor",
        )

    def test_compara_evacuados_solo_si_empata_el_numero_de_mordidos(self) -> None:
        self.assertEqual(
            _comparar_prioridad(
                {"mordidos": 2, "evacuados": 5},
                {"mordidos": 2, "evacuados": 4},
            ),
            "mejor",
        )
        self.assertEqual(
            _comparar_prioridad(
                {"mordidos": 2, "evacuados": 4},
                {"mordidos": 2, "evacuados": 4},
            ),
            "igual",
        )


if __name__ == "__main__":
    unittest.main()
