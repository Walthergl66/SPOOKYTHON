"""Integración HTTP de evaluación con resolución multi-turno en Manta."""

from __future__ import annotations

import unittest

from navira.evaluacion_local import ejecutar_evaluacion_local


class EvaluacionLocalTests(unittest.TestCase):
    def test_consulta_paso_avanza_turnos_y_registra_evidencia(self) -> None:
        reporte = ejecutar_evaluacion_local(
            sobrevivientes=20,
            turnos=2,
            semilla=20261026,
            escenario="mixto",
            concurrencia=4,
        )

        self.assertEqual(reporte["medicion"], "exploratoria_local_http_loopback")
        self.assertEqual(reporte["mapaVersion"], "manta-osm-d76772f9d9e9")
        self.assertEqual(reporte["turnosEjecutados"], 2)
        self.assertEqual(reporte["solicitudes"], 40)
        self.assertEqual(reporte["fallidas"], 0)
        self.assertEqual(reporte["estadosHttp"], {"200": 40})
        turnos = reporte["turnos"]
        self.assertEqual([turno["turno"] for turno in turnos], [0, 1])
        self.assertEqual([turno["versionResuelta"] for turno in turnos], [2, 5])
        self.assertTrue(reporte["menorA500ms"])
        self.assertIn("AWS", " ".join(reporte["limites"]))

    def test_misma_semilla_repite_resultados_del_mundo_no_latencias(self) -> None:
        argumentos = {
            "sobrevivientes": 20,
            "turnos": 2,
            "semilla": 20261026,
            "escenario": "mixto",
            "concurrencia": 4,
        }
        primero = ejecutar_evaluacion_local(**argumentos)
        segundo = ejecutar_evaluacion_local(**argumentos)

        def estado(reporte):
            return [
                (
                    turno["turno"],
                    turno["activosAlCerrarTurno"],
                    turno["evacuadosEnTurno"],
                    turno["mordidosEnTurno"],
                    turno["movimientosZombies"],
                )
                for turno in reporte["turnos"]
            ]

        self.assertEqual(estado(primero), estado(segundo))

    def test_rechaza_cohorte_fuera_de_la_matriz_definida(self) -> None:
        with self.assertRaisesRegex(ValueError, "20, 80 o 200"):
            ejecutar_evaluacion_local(sobrevivientes=40)


if __name__ == "__main__":
    unittest.main()
