"""Casos deterministas para búsqueda temporal acotada y espera."""

from __future__ import annotations

import unittest

from navira.domain.mapa import Calle, Grafo, Mapa, Nodo, Refugio, TipoCalle
from navira.routing.temporal import CondicionTurno, buscar_ruta_temporal


def grafo_temporal() -> Grafo:
    return Grafo(
        Mapa(
            version="ruta-temporal-v1",
            nodos=(Nodo("N-1", 0, 0), Nodo("N-2", 0, 1), Nodo("N-3", 1, 0), Nodo("N-4", 1, 1)),
            calles=(
                Calle("E-12", "S-12", "N-1", "N-2", 10, TipoCalle.CALLE, 20),
                Calle("E-13", "S-13", "N-1", "N-3", 6, TipoCalle.AVENIDA, 30),
                Calle("E-32", "S-32", "N-3", "N-2", 6, TipoCalle.AVENIDA, 30),
                Calle("E-24", "S-24", "N-2", "N-4", 4, TipoCalle.CALLE, 20),
            ),
            refugios=(Refugio("R-2", "N-2"), Refugio("R-4", "N-4")),
        )
    )


class BusquedaTemporalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo = grafo_temporal()

    def test_busca_ruta_minima_y_estable_al_refugio(self) -> None:
        resultado = buscar_ruta_temporal(self.grafo, "N-1", frozenset({"R-2"}))

        self.assertEqual(resultado.estado, "ruta_encontrada")
        self.assertEqual(resultado.trayecto, ("N-1", "N-2"))
        self.assertEqual(resultado.turnos, 1)
        self.assertEqual(resultado.costo_ponderado_m, 10)
        self.assertGreaterEqual(resultado.expansiones, 0)
        self.assertGreater(resultado.duracion_ms, 0)

    def test_puede_esperar_para_evitar_exposicion_transitoria(self) -> None:
        resultado = buscar_ruta_temporal(
            self.grafo,
            "N-1",
            frozenset({"R-2"}),
            peligros_actuales=CondicionTurno(exposicion_nodo={"N-2": 0.9}),
            pronostico=(CondicionTurno(),),
        )

        self.assertEqual(resultado.trayecto, ("N-1", "N-1", "N-2"))
        self.assertEqual(resultado.turnos, 2)
        self.assertEqual(resultado.exposicion_acumulada, 0)

    def test_filtra_cierre_actual_y_halla_alternativa_dirigida(self) -> None:
        resultado = buscar_ruta_temporal(
            self.grafo,
            "N-1",
            frozenset({"R-2"}),
            peligros_actuales=CondicionTurno(aristas_cerradas=frozenset({"E-12"})),
        )

        self.assertEqual(resultado.trayecto, ("N-1", "N-3", "N-2"))
        self.assertEqual(resultado.turnos, 2)

    def test_bloqueo_actual_desaparece_segun_el_pronostico_observable(self) -> None:
        resultado = buscar_ruta_temporal(
            self.grafo,
            "N-1",
            frozenset({"R-2"}),
            peligros_actuales=CondicionTurno(nodos_bloqueados=frozenset({"N-2", "N-3"})),
            pronostico=(CondicionTurno(),),
        )

        self.assertEqual(resultado.trayecto, ("N-1", "N-1", "N-2"))
        self.assertEqual(resultado.turnos, 2)

    def test_presupuesto_agotado_descarta_trayecto_parcial(self) -> None:
        resultado = buscar_ruta_temporal(
            self.grafo,
            "N-1",
            frozenset({"R-4"}),
            limite_expansiones=1,
        )

        self.assertEqual(resultado.estado, "presupuesto_agotado")
        self.assertIsNone(resultado.trayecto)
        self.assertEqual(resultado.expansiones, 1)

    def test_horizonte_acotado_informa_que_no_alcanza_el_refugio(self) -> None:
        resultado = buscar_ruta_temporal(
            self.grafo,
            "N-1",
            frozenset({"R-4"}),
            horizonte_turnos=1,
        )

        self.assertEqual(resultado.estado, "sin_ruta_en_horizonte")
        self.assertIsNone(resultado.trayecto)

    def test_valida_rangos_e_identidad_de_condiciones(self) -> None:
        with self.assertRaises(ValueError):
            buscar_ruta_temporal(self.grafo, "N-1", frozenset({"R-2"}), horizonte_turnos=13)
        with self.assertRaises(ValueError):
            CondicionTurno(exposicion_nodo={"N-1": 1.1})
        with self.assertRaises(KeyError):
            buscar_ruta_temporal(
                self.grafo,
                "N-1",
                frozenset({"R-2"}),
                peligros_actuales=CondicionTurno(nodos_bloqueados=frozenset({"N-desconocido"})),
            )

    def test_devuelve_inmediatamente_si_ya_esta_en_refugio(self) -> None:
        resultado = buscar_ruta_temporal(self.grafo, "N-2", frozenset({"R-2"}))

        self.assertEqual(resultado.estado, "en_refugio")
        self.assertEqual(resultado.trayecto, ("N-2",))
        self.assertEqual(resultado.expansiones, 0)


if __name__ == "__main__":
    unittest.main()
