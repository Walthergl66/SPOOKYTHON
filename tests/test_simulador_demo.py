"""Pruebas del ejecutor CLI local de rondas automáticas."""

from __future__ import annotations

import io
import json
import unittest

from navira.demo import MAPA_MANTA_POR_DEFECTO
from navira.simulador_demo import ejecutar_demo, main


class EjecutorDemoTests(unittest.TestCase):
    def test_ejecuta_hasta_evacuacion_y_reporta_movimientos(self) -> None:
        reportes = ejecutar_demo(turnos=10, semilla=41)

        self.assertEqual([reporte["turno"] for reporte in reportes], list(range(len(reportes))))
        self.assertLessEqual(len(reportes), 4)
        self.assertEqual(reportes[-1]["evacuados"], ["S-DEMO-001"])
        self.assertEqual(reportes[-1]["sobrevivientesActivos"], 0)
        self.assertTrue(all(reporte["semilla"] == 41 for reporte in reportes))

    def test_limita_turnos_y_json_por_linea(self) -> None:
        salida = io.StringIO()

        self.assertEqual(main(["--turnos", "2", "--semilla", "7"], salida=salida), 0)

        lineas = salida.getvalue().splitlines()
        self.assertEqual(len(lineas), 2)
        self.assertEqual([json.loads(linea)["turno"] for linea in lineas], [0, 1])

    def test_misma_escena_y_semilla_reproducen_resultado_y_cambiar_semilla_puede_variarlo(self) -> None:
        argumentos = {"turnos": 1, "escenario": "caminantes", "ruta_mapa": MAPA_MANTA_POR_DEFECTO}
        primero = ejecutar_demo(semilla=0, **argumentos)
        repetido = ejecutar_demo(semilla=0, **argumentos)
        otra_semilla = ejecutar_demo(semilla=1, **argumentos)

        self.assertEqual(primero, repetido)
        self.assertNotEqual(
            primero[0]["movimientosZombies"],
            otra_semilla[0]["movimientosZombies"],
        )

    def test_reproduce_trayectoria_de_varios_turnos_y_otra_semilla_cambia_rutas(self) -> None:
        primero = ejecutar_demo(
            turnos=5, semilla=41, escenario="caminantes", cantidad_sobrevivientes=20
        )
        repetido = ejecutar_demo(
            turnos=5, semilla=41, escenario="caminantes", cantidad_sobrevivientes=20
        )
        perturbado = ejecutar_demo(
            turnos=5, semilla=42, escenario="caminantes", cantidad_sobrevivientes=20
        )

        self.assertEqual(primero, repetido)

        def rutas(reportes):
            return tuple(
                tuple(
                    (paso["id"], paso["desde"], paso["hasta"])
                    for paso in reporte["movimientosSobrevivientes"]
                )
                for reporte in reportes
            )

        self.assertNotEqual(rutas(primero), rutas(perturbado))

    def test_semilla_omitida_genera_y_reporta_la_semilla_real(self) -> None:
        reporte = ejecutar_demo(turnos=1)

        self.assertIsInstance(reporte[0]["semilla"], int)
        self.assertGreaterEqual(reporte[0]["semilla"], 0)

    def test_no_publica_posicion_de_zombie_dormido(self) -> None:
        # Semilla 0 deja dormido al segundo zombie durante este turno; la
        # ubicación se sortea, pero no debe filtrarse mientras siga dormido.
        reportes = ejecutar_demo(turnos=1, semilla=0, escenario="horda")

        self.assertEqual(
            [zombie["id"] for zombie in reportes[0]["movimientosZombies"]],
            ["Z-HOR-001"],
        )

    def test_admite_poblaciones_de_evaluacion_sinteticas(self) -> None:
        for poblacion in (20, 80, 200):
            with self.subTest(poblacion=poblacion):
                reportes = ejecutar_demo(
                    turnos=1,
                    semilla=53,
                    escenario="libre",
                    cantidad_sobrevivientes=poblacion,
                )

                self.assertEqual(reportes[0]["sobrevivientesIniciales"], poblacion)
                self.assertEqual(len(reportes[0]["movimientosSobrevivientes"]), poblacion)

    def test_rechaza_poblacion_superior_al_maximo_de_prueba(self) -> None:
        with self.assertRaisesRegex(ValueError, "entre 1 y 200"):
            ejecutar_demo(cantidad_sobrevivientes=201)

    def test_rechaza_cantidad_de_turnos_no_positiva(self) -> None:
        with self.assertRaises(SystemExit) as error:
            main(["--turnos", "0"])
        self.assertEqual(error.exception.code, 2)

    def test_rechaza_cantidad_no_positiva_en_caso_de_uso(self) -> None:
        with self.assertRaisesRegex(ValueError, "entero positivo"):
            ejecutar_demo(turnos=0)


if __name__ == "__main__":
    unittest.main()
