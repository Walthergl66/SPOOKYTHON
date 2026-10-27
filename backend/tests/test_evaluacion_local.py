"""Integración HTTP de evaluación con resolución multi-turno en Manta."""

from __future__ import annotations

import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

from navira.demo import MAPA_MANTA_POR_DEFECTO
from navira.domain.mapa import MANTA_PLAYABLE_BOUNDS, cargar_mapa, recortar_mapa
from navira.evaluacion_local import ejecutar_evaluacion_local
from navira.domain.modelo import EstadoPartida, EstadoSobreviviente, FaseTurno, Sobreviviente


class EvaluacionLocalTests(unittest.TestCase):
    def test_consulta_paso_avanza_turnos_y_registra_evidencia(self) -> None:
        reporte = ejecutar_evaluacion_local(
            sobrevivientes=20,
            turnos=2,
            semilla=20261026,
            escenario="mixto",
            concurrencia=4,
            periodo_segundos=0.01,
        )

        self.assertEqual(reporte["medicion"], "exploratoria_local_http_loopback")
        mapa_jugable = recortar_mapa(cargar_mapa(MAPA_MANTA_POR_DEFECTO), MANTA_PLAYABLE_BOUNDS)
        self.assertEqual(reporte["mapaVersion"], mapa_jugable.version)
        self.assertEqual(reporte["turnosEjecutados"], 2)
        self.assertEqual(reporte["solicitudes"], 40)
        self.assertEqual(reporte["fallidas"], 0)
        self.assertEqual(reporte["estadosHttp"], {"200": 40})
        turnos = reporte["turnos"]
        self.assertEqual([turno["turno"] for turno in turnos], [0, 1])
        self.assertEqual([turno["solicitudes"] for turno in turnos], [20, 20])
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
            "periodo_segundos": 0.01,
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

    def test_alinea_inicio_de_turnos_a_la_cadencia_configurada(self) -> None:
        reporte = ejecutar_evaluacion_local(
            sobrevivientes=20,
            turnos=2,
            semilla=20261026,
            concurrencia=4,
            periodo_segundos=0.2,
        )

        self.assertEqual(reporte["periodoObjetivoSegundos"], 0.2)
        turnos = reporte["turnos"]
        self.assertGreaterEqual(turnos[1]["intervaloInicioAnteriorMs"], 190)
        self.assertGreaterEqual(turnos[1]["inicioDesdeInicioMs"], 190)
        self.assertIn("duracionTurnoMs", turnos[0])
        self.assertIn("periodoCumplido", turnos[0])

    def test_rechaza_periodo_no_positivo(self) -> None:
        with self.assertRaisesRegex(ValueError, "período"):
            ejecutar_evaluacion_local(sobrevivientes=20, periodo_segundos=0)

    def test_completa_duracion_con_slots_ociosos_sin_fabricar_turnos_ni_solicitudes(self) -> None:
        partida = SimpleNamespace(
            estado=EstadoPartida.FINALIZADA,
            fase=FaseTurno.RESUELTA,
            turno=11,
            sobrevivientes=(Sobreviviente("S-1", "N-1", estado=EstadoSobreviviente.EVACUADO),),
        )
        snapshot = SimpleNamespace(partida=partida, version=42)
        almacen = SimpleNamespace(obtener=lambda _run_id: snapshot)
        contexto = SimpleNamespace(
            grafo=SimpleNamespace(mapa=SimpleNamespace(version="mapa-test")),
            snapshots=almacen,
            servicio_decision=None,
            run_id="run-terminal",
            semilla=7,
        )

        with (
            patch("navira.evaluacion_local.crear_contexto_demo", return_value=contexto),
            patch("navira.evaluacion_local.crear_app"),
            patch(
                "navira.evaluacion_local._servidor_loopback",
                return_value=nullcontext("http://127.0.0.1/paso"),
            ),
        ):
            reporte = ejecutar_evaluacion_local(
                sobrevivientes=20,
                turnos=3,
                semilla=7,
                escenario="libre",
                periodo_segundos=0.01,
            )

        self.assertEqual(reporte["turnosEjecutados"], 0)
        self.assertEqual(reporte["solicitudes"], 0)
        self.assertEqual(reporte["slotsCadenciaSinActividad"], 3)
        self.assertEqual(len(reporte["slotsSinActividad"]), 3)
        self.assertTrue(reporte["duracionObjetivoCumplida"])
        self.assertGreaterEqual(
            reporte["duracionTotalSegundos"], reporte["duracionObjetivoSegundos"] - 0.001
        )


if __name__ == "__main__":
    unittest.main()
