"""Integridad del fixture geográfico y metadatos de seguridad de Manta."""

import json
import unittest
from collections import defaultdict, deque
from pathlib import Path

from navira.domain.mapa import Grafo, cargar_mapa


ROOT = Path(__file__).resolve().parents[1]
MAPA = ROOT / "data/maps/manta-hackathon-v1.json"
FUENTES = ROOT / "data/maps/manta-hackathon-v1.fuentes.json"


class MapaMantaTests(unittest.TestCase):
    def test_fixture_tiene_caja_completa_cuatro_refugios_y_rutas_dirigidas(self) -> None:
        mapa = cargar_mapa(MAPA)
        mapa.validar_mapa_evaluacion(minimo_nodos=8366)
        self.assertEqual(len(mapa.nodos), 8366)
        self.assertEqual(len(mapa.refugios), 4)
        self.assertEqual(len({refugio.nodo for refugio in mapa.refugios}), 4)

        predecesores: defaultdict[str, set[str]] = defaultdict(set)
        for calle in mapa.calles:
            predecesores[calle.destino].add(calle.origen)
        alcanzan_refugio = {refugio.nodo for refugio in mapa.refugios}
        frontera = deque(alcanzan_refugio)
        while frontera:
            nodo = frontera.popleft()
            for anterior in predecesores[nodo]:
                if anterior not in alcanzan_refugio:
                    alcanzan_refugio.add(anterior)
                    frontera.append(anterior)
        self.assertEqual(alcanzan_refugio, set(mapa.nodos_por_id))
        self.assertGreater(len(mapa.calles), 0)
        self.assertTrue(all(calle.distancia_m > 0 for calle in mapa.calles))
        self.assertIsInstance(Grafo(mapa).calles_desde(mapa.nodos[0].id), tuple)

    def test_fuentes_distinguen_evidencia_de_tsunami_y_sismo(self) -> None:
        fuentes = json.loads(FUENTES.read_text(encoding="utf-8"))
        self.assertIn("no usar", fuentes["estado"])
        self.assertEqual(fuentes["osm"]["licencia"], "Open Database License (ODbL)")
        self.assertEqual(len(fuentes["refugios"]), 4)
        self.assertTrue(all("zona segura" in ref["evidencia_tsunami"].casefold() for ref in fuentes["refugios"]))
        self.assertTrue(all("no evaluada" in ref["evidencia_sismo"] for ref in fuentes["refugios"]))
        self.assertTrue(all(0 <= ref["distancia_snap_m"] <= 350 for ref in fuentes["refugios"]))
        self.assertIn("no se afirma", fuentes["amenazas"]["sismo"])


if __name__ == "__main__":
    unittest.main()
