"""Regresiones de exportación completa: cruces, geometría y respuestas parciales."""

import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from test_exportar_anclajes import exportar


class ExportarCoberturaTests(unittest.TestCase):
    def test_conserva_cruce_interior_de_dos_vias_y_nodos_de_curva(self):
        nodos = {str(i): (-0.95 + i * 0.0001, -80.72) for i in range(1, 7)}
        vias = {
            "10": ET.fromstring('<way><nd ref="1"/><nd ref="6"/><nd ref="3"/><nd ref="2"/><tag k="highway" v="residential"/></way>'),
            "11": ET.fromstring('<way><nd ref="4"/><nd ref="3"/><nd ref="5"/><tag k="highway" v="residential"/></way>'),
        }
        with patch.object(exportar, "_anclas_por_zona", return_value={"R-01": "1"}):
            coords, segmentos, _ = exportar.construir_grafo_completo(nodos, vias)
        self.assertEqual(set(coords), set(nodos))
        self.assertEqual({(s["desde"], s["hasta"]) for s in segmentos}, {("1", "6"), ("6", "3"), ("3", "2"), ("4", "3"), ("3", "5")})

    def test_rechaza_respuestas_parciales_o_vacias(self):
        for xml in (
            b'<osm><remark>runtime error: timeout</remark></osm>',
            b'<osm/>',
            b'<osm><node id="1" lat="0" lon="0"/><way id="1"><nd ref="1"/><nd ref="2"/><tag k="highway" v="road"/></way></osm>',
        ):
            with self.subTest(xml=xml), self.assertRaises(RuntimeError):
                exportar.leer_elementos(xml)
