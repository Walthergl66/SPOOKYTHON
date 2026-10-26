"""Pruebas del ejecutor CLI local de rondas automáticas."""

from __future__ import annotations

import io
import json
import unittest

from navira.simulador_demo import ejecutar_demo, main


class EjecutorDemoTests(unittest.TestCase):
    def test_ejecuta_hasta_evacuacion_y_reporta_movimientos(self) -> None:
        reportes = ejecutar_demo(turnos=10, semilla=41)

        self.assertEqual([reporte["turno"] for reporte in reportes], [0, 1, 2, 3])
        self.assertEqual(
            [reporte["movimientosSobrevivientes"][0]["hasta"] for reporte in reportes],
            ["D-002", "D-003", "D-004", "D-005"],
        )
        self.assertEqual(reportes[-1]["evacuados"], ["S-DEMO-001"])
        self.assertEqual(reportes[-1]["sobrevivientesActivos"], 0)
        self.assertTrue(all(reporte["semilla"] == 41 for reporte in reportes))

    def test_limita_turnos_y_json_por_linea(self) -> None:
        salida = io.StringIO()

        self.assertEqual(main(["--turnos", "2", "--semilla", "7"], salida=salida), 0)

        lineas = salida.getvalue().splitlines()
        self.assertEqual(len(lineas), 2)
        self.assertEqual([json.loads(linea)["turno"] for linea in lineas], [0, 1])

    def test_rechaza_cantidad_de_turnos_no_positiva(self) -> None:
        with self.assertRaises(SystemExit) as error:
            main(["--turnos", "0"])
        self.assertEqual(error.exception.code, 2)

    def test_rechaza_cantidad_no_positiva_en_caso_de_uso(self) -> None:
        with self.assertRaisesRegex(ValueError, "entero positivo"):
            ejecutar_demo(turnos=0)


if __name__ == "__main__":
    unittest.main()
