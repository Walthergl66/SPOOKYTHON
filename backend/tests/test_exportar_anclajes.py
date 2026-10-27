"""Validación de anclajes manuales del exportador de mapa (sin red)."""

import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts/exportar_mapa_manta.py"
loader = importlib.util.spec_from_file_location("exportar_mapa_manta", MODULE)
exportar = importlib.util.module_from_spec(loader)
loader.loader.exec_module(exportar)

OFICIALES = {"R-01": (0.0, 0.0), "R-02": (0.0005, 0.0)}
ANCLAS = {"R-01": "1", "R-02": "2"}
COORDS = {"1": (0.0, 0.0), "2": (1.0, 1.0), "3": (0.001, 0.0), "4": (0.001, 0.0001), "5": (0.01, 0.0)}
FORMAS = {"1": {"a", "b"}, "2": {"a", "b"}, "3": {"a", "b"}, "4": {"a"}, "5": {"a", "b"}}


def aplicar(anclajes):
    return exportar.aplicar_anclajes_manuales(ANCLAS, anclajes, COORDS, FORMAS, OFICIALES)


class AnclajesTests(unittest.TestCase):
    def test_valido_sustituye_solo_el_indicado(self):
        self.assertEqual(aplicar({"R-01": "3"}), {"R-01": "3", "R-02": "2"})

    def test_refugio_desconocido(self):
        with self.assertRaisesRegex(RuntimeError, "desconocido"):
            aplicar({"R-09": "3"})

    def test_nodo_no_interseccion(self):
        with self.assertRaisesRegex(RuntimeError, "intersección"):
            aplicar({"R-01": "4"})

    def test_nodo_lejano(self):
        with self.assertRaisesRegex(RuntimeError, "350 m"):
            aplicar({"R-01": "5"})

    def test_nodo_repetido(self):
        with self.assertRaisesRegex(RuntimeError, "varios refugios"):
            aplicar({"R-01": "3", "R-02": "3"})


if __name__ == "__main__":
    unittest.main()
