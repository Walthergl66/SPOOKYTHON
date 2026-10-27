"""Velocidad del reloj de simulación: validación y cambio en caliente (sin esperas reales)."""

from __future__ import annotations

import unittest

from navira.application.control_simulador_demo import ControlSimuladorDemoLocal
from navira.application.reloj_simulador import RelojSimuladorLocal, validar_velocidad


class ValidarVelocidadTests(unittest.TestCase):
    def test_acepta_factores_positivos_y_finitos(self) -> None:
        self.assertEqual(validar_velocidad(4.0), 4.0)

    def test_rechaza_cero_negativos_e_infinitos(self) -> None:
        for valor in (0.0, -2.0, float("inf"), float("nan")):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                validar_velocidad(valor)


class RelojVelocidadTests(unittest.TestCase):
    def test_cambia_en_caliente_y_rechaza_valores_invalidos(self) -> None:
        # Sin iniciar el hilo: solo se prueba el estado del factor.
        reloj = RelojSimuladorLocal("run", None, None, velocidad=2.0)  # type: ignore[arg-type]
        self.assertEqual(reloj.velocidad, 2.0)
        reloj.fijar_velocidad(4)
        self.assertEqual(reloj.velocidad, 4.0)
        with self.assertRaises(ValueError):
            reloj.fijar_velocidad(0)
        self.assertEqual(reloj.velocidad, 4.0)


class ControlVelocidadTests(unittest.TestCase):
    def test_estado_informa_velocidad_sin_partida(self) -> None:
        control = ControlSimuladorDemoLocal(lambda **_: None)  # type: ignore[arg-type]
        self.assertEqual(control.estado()["velocidad"], 1.0)
        self.assertEqual(control.fijar_velocidad(4)["velocidad"], 4.0)

    def test_velocidad_invalida_no_cambia_el_estado(self) -> None:
        control = ControlSimuladorDemoLocal(lambda **_: None)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            control.fijar_velocidad(0)
        self.assertEqual(control.estado()["velocidad"], 1.0)


if __name__ == "__main__":
    unittest.main()
