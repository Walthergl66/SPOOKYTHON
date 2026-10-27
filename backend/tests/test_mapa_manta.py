"""Integridad del fixture geográfico y metadatos de seguridad de Manta."""

import json
import unittest
from collections import defaultdict, deque
from pathlib import Path

from navira.domain.mapa import MANTA_PLAYABLE_BOUNDS, Grafo, cargar_mapa, recortar_mapa


ROOT = Path(__file__).resolve().parents[1]
MAPA = ROOT / "data/maps/manta-hackathon-v1.json"
FUENTES = ROOT / "data/maps/manta-hackathon-v1.fuentes.json"


class MapaMantaTests(unittest.TestCase):
    def test_recorte_urbano_es_limite_topologico_del_mapa_jugable(self) -> None:
        original = cargar_mapa(MAPA)
        mapa = recortar_mapa(original, MANTA_PLAYABLE_BOUNDS)
        (oeste, sur), (este, norte) = MANTA_PLAYABLE_BOUNDS
        ids = set(mapa.nodos_por_id)

        self.assertLess(len(mapa.nodos), len(original.nodos))
        self.assertTrue(all(oeste <= nodo.lng <= este and sur <= nodo.lat <= norte for nodo in mapa.nodos))
        self.assertTrue(all(calle.origen in ids and calle.destino in ids for calle in mapa.calles))
        self.assertEqual({refugio.id for refugio in mapa.refugios}, {"R-01", "R-02", "R-03", "R-04"})
        self.assertTrue(all(refugio.nodo in ids for refugio in mapa.refugios))

    def test_fixture_tiene_caja_completa_cuatro_refugios_y_rutas_dirigidas(self) -> None:
        mapa = cargar_mapa(MAPA)
        mapa.validar_mapa_evaluacion(minimo_nodos=40000)
        fuentes = json.loads(FUENTES.read_text(encoding="utf-8"))
        self.assertEqual(len(mapa.nodos), fuentes["osm"]["conteos"]["nodos"])
        self.assertEqual(len(mapa.calles), fuentes["osm"]["conteos"]["sentidos"])
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

    def test_red_alcanza_sectores_urbanos_y_rurales_ampliados(self) -> None:
        mapa = cargar_mapa(MAPA)
        # Referencias aproximadas de cobertura, no ubicaciones de refugios.
        for nombre, lat, lng in (
            ("San Mateo", -0.963, -80.810),
            ("Santa Marianita", -0.985, -80.854),
            ("San Lorenzo", -1.064, -80.904),
            ("Eloy Alfaro", -0.980, -80.690),
            ("Aeropuerto", -0.950, -80.680),
        ):
            with self.subTest(sector=nombre):
                distancia = min(((n.lat-lat)**2+(n.lng-lng)**2)**0.5 * 111000 for n in mapa.nodos)
                self.assertLess(distancia, 1000)

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
