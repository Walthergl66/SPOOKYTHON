"""Pruebas de rutas dirigidas, ponderadas y con peligros visibles."""

import unittest

from navira.domain.mapa import Calle, Grafo, Mapa, Nodo, Refugio, TipoCalle
from navira.routing.dijkstra import PerfilCostos, encontrar_ruta, seleccionar_refugio


def grafo_rutas(distancia_directa: float = 10.0) -> Grafo:
    mapa = Mapa(
        version="rutas-test-v1",
        nodos=(
            Nodo("N-1", 0.0, 0.0),
            Nodo("N-2", 0.0, 0.1),
            Nodo("N-3", 0.1, 0.0),
            Nodo("N-4", 0.1, 0.1),
        ),
        calles=(
            Calle("E-01", "S-D", "N-1", "N-2", distancia_directa, TipoCalle.CALLEJON, 20),
            Calle("E-02", "S-A", "N-1", "N-3", 6.0, TipoCalle.AVENIDA, 50),
            Calle("E-03", "S-B", "N-3", "N-2", 6.0, TipoCalle.AVENIDA, 50),
            Calle("E-04", "S-C", "N-2", "N-4", 4.0, TipoCalle.CALLE, 30),
        ),
        refugios=(Refugio("R-Z", "N-2"), Refugio("R-A", "N-2")),
    )
    return Grafo(mapa)


class DijkstraTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo = grafo_rutas()

    def test_selecciona_costo_menor_y_devuelve_primer_vecino(self) -> None:
        ruta = encontrar_ruta(self.grafo, "N-1", "N-2")
        self.assertIsNotNone(ruta)
        self.assertEqual(tuple(calle.id for calle in ruta.calles), ("E-01",))
        self.assertEqual(ruta.siguiente_nodo, "N-2")
        self.assertEqual(ruta.costo_ponderado_m, 10.0)

    def test_factor_por_tipo_puede_cambiar_ruta_sin_cambiar_unidades(self) -> None:
        perfil = PerfilCostos({TipoCalle.CALLEJON: 3.0})
        ruta = encontrar_ruta(self.grafo, "N-1", "N-2", perfil=perfil)
        self.assertEqual(tuple(calle.id for calle in ruta.calles), ("E-02", "E-03"))
        self.assertEqual(ruta.costo_ponderado_m, 12.0)

    def test_cierres_y_nodos_bloqueados_filtran_rutas(self) -> None:
        cerrada = encontrar_ruta(
            self.grafo, "N-1", "N-2", aristas_cerradas=frozenset({"E-01"})
        )
        bloqueada = encontrar_ruta(
            self.grafo, "N-1", "N-2", nodos_bloqueados=frozenset({"N-3"})
        )
        sin_ruta = encontrar_ruta(
            self.grafo,
            "N-1",
            "N-2",
            segmentos_cerrados=frozenset({"S-D", "S-A"}),
        )
        self.assertEqual(tuple(calle.id for calle in cerrada.calles), ("E-02", "E-03"))
        self.assertEqual(tuple(calle.id for calle in bloqueada.calles), ("E-01",))
        self.assertIsNone(sin_ruta)

    def test_desempate_es_determinista_por_secuencia_de_calles(self) -> None:
        empate = encontrar_ruta(grafo_rutas(12.0), "N-1", "N-2")
        self.assertEqual(tuple(calle.id for calle in empate.calles), ("E-01",))

    def test_seleccion_refugio_desempata_por_id(self) -> None:
        ruta = seleccionar_refugio(self.grafo, "N-1")
        self.assertEqual(ruta.refugio_id, "R-A")

    def test_origen_igual_destino_y_refugio_objetivo(self) -> None:
        ruta = encontrar_ruta(self.grafo, "N-2", "N-2")
        elegida = seleccionar_refugio(self.grafo, "N-1", refugio_objetivo="R-Z")
        self.assertEqual(ruta.calles, ())
        self.assertIsNone(ruta.siguiente_nodo)
        self.assertEqual(elegida.refugio_id, "R-Z")

    def test_rechaza_factor_no_positivo_y_nodo_desconocido(self) -> None:
        with self.assertRaises(ValueError):
            PerfilCostos({TipoCalle.CALLE: 0.0})
        with self.assertRaises(KeyError):
            encontrar_ruta(self.grafo, "N-x", "N-2")


if __name__ == "__main__":
    unittest.main()
