"""Aísla mundos públicos por cookie y acota su consumo de memoria."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from navira.adapters.sesiones_demo_memoria import (
    LimiteSesionesDemo,
    RegistroSesionesDemoMemoria,
)
from navira.api.seguridad import ConfiguracionSeguridad
from navira.main import crear_app


class _ControlFalso:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.consultar_panel = None
        self.cerrado = False
        self.partida_iniciada = False

    def estado(self):
        return {
            "habilitado": True,
            "estado": "activa" if self.partida_iniciada else "sin_partida",
            "runId": self.run_id if self.partida_iniciada else None,
        }

    def iniciar_mundo_operador(self):
        self.partida_iniciada = True
        return {"estado": "activa", "runId": self.run_id}

    def cerrar(self):
        self.cerrado = True


class RegistroSesionesDemoTests(unittest.TestCase):
    def test_clientes_reciben_mundos_independientes_y_reutilizan_su_cookie(self) -> None:
        creados: list[_ControlFalso] = []

        def crear_control():
            control = _ControlFalso(f"run-{len(creados) + 1}")
            creados.append(control)
            return control

        registro = RegistroSesionesDemoMemoria(crear_control, max_sesiones=2)
        app = crear_app(
            sesiones_demo_publicas=registro,
            seguridad=ConfiguracionSeguridad(control_demo_publico=True, cookie_segura=False),
        )
        with TestClient(app, base_url="http://navira.test") as primero, TestClient(app, base_url="http://navira.test") as segundo:
            estado_primero = primero.get("/demo/simulador")
            estado_segundo = segundo.get("/demo/simulador")
            estado_primero_repetido = primero.get("/demo/simulador")

            self.assertEqual(estado_primero.status_code, 200)
            self.assertEqual(estado_segundo.status_code, 200)
            self.assertEqual(estado_primero.json()["runId"], "run-1")
            self.assertEqual(estado_segundo.json()["runId"], "run-2")
            self.assertEqual(estado_primero_repetido.json()["runId"], "run-1")
            self.assertNotEqual(
                primero.cookies["navira_demo_session"],
                segundo.cookies["navira_demo_session"],
            )
            self.assertIn("HttpOnly", estado_primero.headers["set-cookie"])

            origen_cruzado = primero.post(
                "/demo/operador/iniciar",
                headers={"Origin": "https://attacker.example"},
            )
            self.assertEqual(origen_cruzado.status_code, 403)

        self.assertTrue(all(control.cerrado for control in creados))

    def test_rechaza_sesiones_sobre_el_limite_configurado(self) -> None:
        registro = RegistroSesionesDemoMemoria(lambda: _ControlFalso("única"), max_sesiones=1)
        app = crear_app(
            sesiones_demo_publicas=registro,
            seguridad=ConfiguracionSeguridad(control_demo_publico=True, cookie_segura=False),
        )
        with TestClient(app, base_url="http://navira.test") as primero, TestClient(app, base_url="http://navira.test") as segundo:
            self.assertEqual(primero.get("/demo/simulador").status_code, 200)
            saturada = segundo.get("/demo/simulador")

        self.assertEqual(saturada.status_code, 429)
        self.assertEqual(saturada.headers["retry-after"], "30")

    def test_expira_y_cierra_sesiones_inactivas(self) -> None:
        ahora = [10.0]
        creados: list[_ControlFalso] = []
        registro = RegistroSesionesDemoMemoria(
            lambda: creados.append(_ControlFalso("run")) or creados[-1],
            max_sesiones=1,
            inactividad_segundos=5,
            reloj=lambda: ahora[0],
        )
        _, token = registro.obtener_o_crear(None)
        ahora[0] += 5

        self.assertIsNone(registro.obtener_existente(token))
        self.assertTrue(creados[0].cerrado)

    def test_rechaza_limite_invalido(self) -> None:
        with self.assertRaises(ValueError):
            RegistroSesionesDemoMemoria(lambda: _ControlFalso("x"), max_sesiones=0)

        registro = RegistroSesionesDemoMemoria(lambda: _ControlFalso("x"), max_sesiones=1)
        registro.obtener_o_crear(None)
        with self.assertRaises(LimiteSesionesDemo):
            registro.obtener_o_crear(None)
        registro.cerrar()


if __name__ == "__main__":
    unittest.main()
