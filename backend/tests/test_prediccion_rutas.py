"""Pruebas de frontera de información y distribución de pronósticos."""

from __future__ import annotations

import unittest

from navira.domain.modelo import TipoZombie
from navira.domain.mapa import Calle, Grafo, Mapa, Nodo, Refugio, TipoCalle
from navira.routing.prediccion import (
    SobrevivienteObservable,
    ZombieObservable,
    _indice_objetivos_visibles,
    _objetivo_visible,
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

    def test_indice_inverso_de_objetivos_coincide_con_busqueda_directa(self) -> None:
        sobrevivientes_por_nodo = {"N-3": ["S-2", "S-1"], "N-4": ["S-3"]}
        aristas_cerradas = frozenset({"E-34"})
        segmentos_cerrados = frozenset()

        indice = _indice_objetivos_visibles(
            self.grafo,
            sobrevivientes_por_nodo,
            3,
            aristas_cerradas,
            segmentos_cerrados,
        )

        for nodo in self.grafo.mapa.nodos_por_id:
            self.assertEqual(
                indice.get(nodo),
                _objetivo_visible(
                    self.grafo,
                    nodo,
                    sobrevivientes_por_nodo,
                    3,
                    aristas_cerradas,
                    segmentos_cerrados,
                ),
                nodo,
            )

    def test_pronostica_cruce_opuesto_del_caminante_sobre_calle_bidireccional(self) -> None:
        grafo = Grafo(
            Mapa(
                version="cruce-pronosticado-v1",
                nodos=(Nodo("A", 0, 0), Nodo("B", 0, 1)),
                calles=(
                    Calle("A-B", "S-AB", "A", "B", 10, TipoCalle.CALLE, 20),
                    Calle("B-A", "S-AB", "B", "A", 10, TipoCalle.CALLE, 20),
                ),
                refugios=(Refugio("R-A", "A"),),
            )
        )
        resultado = pronosticar_zombies_visibles(
            grafo,
            (ZombieObservable("Z-1", TipoZombie.CAMINANTE, "A"),),
            (),
            turno_actual=0,
            horizonte_turnos=1,
        )

        self.assertEqual(resultado.turnos[0].exposicion_arista["B-A"], 0.5)
        self.assertNotIn("A-B", resultado.turnos[0].exposicion_arista)

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

    def test_agrupar_zombies_lineales_conserva_exposicion_de_nodos_y_cruces(self) -> None:
        survivors = (
            SobrevivienteObservable("S-1", "N-3"),
            SobrevivienteObservable("S-2", "N-4"),
        )
        for tipo, nodos in (
            (TipoZombie.CAMINANTE, ("N-1", "N-2")),
            (TipoZombie.CORREDOR, ("N-1", "N-2")),
        ):
            with self.subTest(tipo=tipo):
                zombies = tuple(
                    ZombieObservable(f"Z-{index}", tipo, nodo)
                    for index, nodo in enumerate(nodos, start=1)
                )
                combinado = pronosticar_zombies_visibles(
                    self.grafo, zombies, survivors, turno_actual=2, horizonte_turnos=3
                )
                individuales = [
                    pronosticar_zombies_visibles(
                        self.grafo, (zombie,), survivors, turno_actual=2, horizonte_turnos=3
                    )
                    for zombie in zombies
                ]

                for indice, turno in enumerate(combinado.turnos):
                    esperada_nodos: dict[str, float] = {}
                    esperadas_aristas: dict[str, float] = {}
                    for individual in individuales:
                        for node, exposure in individual.turnos[indice].exposicion_nodo.items():
                            esperada_nodos[node] = min(1.0, esperada_nodos.get(node, 0.0) + exposure)
                        for edge, exposure in individual.turnos[indice].exposicion_arista.items():
                            esperadas_aristas[edge] = min(1.0, esperadas_aristas.get(edge, 0.0) + exposure)

                    self.assertEqual(dict(turno.exposicion_nodo), esperada_nodos)
                    self.assertEqual(dict(turno.exposicion_arista), esperadas_aristas)

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
