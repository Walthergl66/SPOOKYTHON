"""Pruebas de métricas y validación del cliente de ráfagas HTTP."""

from __future__ import annotations

import json
import unittest

from navira.carga_http import ResultadoSolicitud, ejecutar_carga


class ClienteCargaHttpTests(unittest.TestCase):
    def test_resumen_cuenta_rondas_respuestas_y_percentiles(self) -> None:
        llamadas: list[bytes] = []

        def enviar(_url, _api_key, solicitud, _timeout):
            llamadas.append(solicitud.cuerpo)
            return ResultadoSolicitud(12.0, 200, True)

        reporte = ejecutar_carga(
            url="http://localhost/paso",
            api_key="clave-de-prueba",
            sobrevivientes=20,
            rondas=2,
            concurrencia=5,
            periodo_segundos=0.001,
            enviar=enviar,
        )

        self.assertEqual(len(llamadas), 40)
        self.assertEqual(reporte["solicitudes"], 40)
        self.assertEqual(reporte["estadosHttp"], {"200": 40})
        self.assertEqual(reporte["fallidas"], 0)
        self.assertEqual(reporte["latenciaMs"]["p95"], 12.0)
        self.assertTrue(reporte["menorA500ms"])
        self.assertIn("sobrevivienteId", json.loads(llamadas[0]))

    def test_falla_si_falta_api_key_o_url_no_es_paso(self) -> None:
        with self.assertRaisesRegex(ValueError, "NAVIRA_API_KEY"):
            ejecutar_carga(url="http://localhost/paso", api_key="")
        with self.assertRaisesRegex(ValueError, "ruta /paso"):
            ejecutar_carga(url="http://localhost", api_key="test")
        with self.assertRaisesRegex(ValueError, "mayores que cero"):
            ejecutar_carga(
                url="http://localhost/paso",
                api_key="test",
                periodo_segundos=float("nan"),
            )


if __name__ == "__main__":
    unittest.main()
