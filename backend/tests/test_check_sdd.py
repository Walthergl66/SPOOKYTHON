"""Regression checks for invalid SDD references, using an isolated fixture."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[1] / "scripts/check_sdd.py"
loader = importlib.util.spec_from_file_location("check_sdd", MODULE)
check_sdd = importlib.util.module_from_spec(loader)
loader.loader.exec_module(check_sdd)


class SddValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.doc = self.root / "docs"
        (self.doc / "metodo" / "especificaciones").mkdir(parents=True)
        (self.doc / "producto").mkdir()
        (self.doc / "seguimiento").mkdir()
        (self.doc / "calidad").mkdir()
        self.spec = self.doc / "metodo/especificaciones/SPEC-001-ejemplo.md"
        self.write("producto/PRD.md", "### PRD-01 — Ejemplo\n")
        self.write("producto/TRD.md", "### TRD-01 — Condición\n")
        self.write("seguimiento/plan-implementacion.md", "| P0-01 | Tarea |\n")
        self.write("calidad/pruebas.md", "| T-01 | Caso |\n")
        self.write("seguimiento/cambios.md", "## CAM-001 — Cambio\n")
        self.write("metodo/trazabilidad.md", "| [SPEC-001](x) | PRD-01, TRD-01 |\n")
        self.spec.write_text(
            "# Ejemplo\nID: SPEC-001\nEstado: lista\n"
            "Requisitos: PRD-01, TRD-01\nTareas: P0-01\nPruebas: T-01\n"
            "Cambio: pendiente\nEvidencia: pendiente\n"
            "| CA-001-01 | Se verifica el resultado. | T-01 |\n",
            encoding="utf-8",
        )

    def write(self, path, content):
        (self.doc / path).write_text(content, encoding="utf-8")

    def replace(self, old, new):
        self.spec.write_text(self.spec.read_text().replace(old, new), encoding="utf-8")

    def errors(self):
        return "\n".join(check_sdd.validate(self.root)[0])

    def test_valid_spec_with_known_references(self):
        self.assertEqual(self.errors(), "")

    def test_unknown_requirement_is_rejected(self):
        self.replace("Requisitos: PRD-01", "Requisitos: PRD-99")
        self.assertIn("referencia desconocida en Requisitos: PRD-99", self.errors())

    def test_criterion_without_a_declared_test_is_rejected(self):
        self.replace("resultado. | T-01", "resultado. | T-99")
        self.assertIn("sin descripción/pruebas declaradas válidas", self.errors())

    def test_unknown_task_is_rejected(self):
        self.replace("Tareas: P0-01", "Tareas: P9-99")
        self.assertIn("referencia desconocida en Tareas: P9-99", self.errors())

    def test_verified_requires_recorded_evidence(self):
        self.replace("Estado: lista", "Estado: verificada")
        self.assertIn("verificada exige CAM y evidencia", self.errors())

    def test_verified_with_existing_change_and_report(self):
        self.replace("Estado: lista", "Estado: verificada")
        self.replace("Cambio: pendiente", "Cambio: CAM-001")
        self.replace("Evidencia: pendiente", "Evidencia: ../reporte.md")
        self.write("metodo/reporte.md", "Resultado comprobado de la fixture.\n")
        self.assertEqual(self.errors(), "")

    def test_matrix_drift_is_rejected(self):
        self.write("metodo/trazabilidad.md", "| [SPEC-001](x) | PRD-01 |\n")
        self.assertIn("matriz de trazabilidad ausente o distinta", self.errors())

    def test_requirement_without_spec_is_rejected(self):
        self.write("producto/PRD.md", "### PRD-01 — Ejemplo\n### PRD-02 — Olvidado\n")
        self.assertIn("Requisito sin especificación: PRD-02", self.errors())


if __name__ == "__main__":
    unittest.main()
