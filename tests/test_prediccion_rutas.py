"""Pruebas de frontera de información y distribución de pronósticos."""

from __future__ import annotations

import unittest

from navira.domain.modelo import TipoZombie
from navira.routing.prediccion import (
    SobrevivienteObservable,
    ZombieObservable,
    pronosticar_zombies_visibles,
)
from test_ruta_temporal import grafo_temporal


class PronosticoRutasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo = grafo_temporal()

    def test_caminante_mezcla_fases_sin_recibir_fase_privada(self) -> None:
        resultado = pronosticar_zombies_visibles(
            self.grafo,
            (ZombieObservable("Z-1", TipoZombie.CAMINANTE, "N-1"),),
            (),
            turno_actual=0,
            horizonte_turnos=1,
        )

        exposicion = resultado.turnos[0].exposicion_nodo
        self.assertAlmostEqual(exposicion["N-1"], 0.5)
        self.assertAlmostEqual(exposicion["N-2"], 0.25)
        self.assertAlmostEqual(exposicion["N-3"], 0.25)
        self.assertIn("caminante_uniforme_fase_desconocida", resultado.supuestos)

    def test_corredor_persigue_superviviente_observable_hasta_dos_tramos(self) -> None:
        resultado = pronosticar_zombies_visibles(
            self.grafo,
            (ZombieObservable("Z-C", TipoZombie.CORREDOR, "N-1"),),
            (SobrevivienteObservable("S-1", "N-4"),),
            turno_actual=0,
            horizonte_turnos=1,
        )

        self.assertEqual(dict(resultado.turnos[0].exposicion_nodo), {"N-2": 1.0, "N-4": 1.0})
        self.assertIn("corredor_objetivo_con_sobrevivientes_estaticos", resultado.supuestos)

    def test_horda_mantiene_bloqueado_su_nodo_y_vecinos_de_ambos_sentidos(self) -> None:
        resultado = pronosticar_zombies_visibles(
            self.grafo,
            (ZombieObservable("Z-H", TipoZombie.HORDA, "N-2"),),
            (),
            turno_actual=0,
            horizonte_turnos=2,
        )

        self.assertEqual(
            resultado.turnos[0].nodos_bloqueados,
            frozenset({"N-1", "N-2", "N-3", "N-4"}),
        )
        self.assertEqual(resultado.turnos[0].nodos_bloqueados, resultado.turnos[1].nodos_bloqueados)
        self.assertIn("horda_estatica_provisional", resultado.supuestos)

    def test_no_acepta_dormidos_ni_observaciones_fuera_del_grafo(self) -> None:
        with self.assertRaises(ValueError):
            ZombieObservable("Z-D", TipoZombie.DORMIDO, "N-1")
        with self.assertRaises(KeyError):
            pronosticar_zombies_visibles(
                self.grafo,
                (ZombieObservable("Z-1", TipoZombie.CAMINANTE, "N-X"),),
                (),
                turno_actual=0,
            )

    def test_valida_horizonte_turno_y_observaciones_duplicadas(self) -> None:
        with self.assertRaises(ValueError):
            pronosticar_zombies_visibles(self.grafo, (), (), turno_actual=-1)
        with self.assertRaises(ValueError):
            pronosticar_zombies_visibles(self.grafo, (), (), turno_actual=0, horizonte_turnos=13)
        with self.assertRaises(ValueError):
            pronosticar_zombies_visibles(
                self.grafo,
                (ZombieObservable("Z-1", TipoZombie.CAMINANTE, "N-1"),) * 2,
                (),
                turno_actual=0,
            )


if __name__ == "__main__":
    unittest.main()
