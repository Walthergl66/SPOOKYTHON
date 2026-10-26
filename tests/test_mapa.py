"""Regresiones de validación del mapa y cierres dirigidos/físicos."""

import json
import tempfile
import unittest
from pathlib import Path

from navira.domain.mapa import Calle, Grafo, Mapa, Nodo, Refugio, TipoCalle, cargar_mapa


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "mapa-minimo.json"


class MapaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapa = cargar_mapa(FIXTURE)
        self.grafo = Grafo(self.mapa)

    def test_carga_fixture_y_valida_cuatro_refugios(self) -> None:
        self.mapa.validar_mapa_evaluacion(minimo_nodos=4)
        self.assertEqual(len(self.mapa.nodos_por_id), 4)
        self.assertEqual(self.grafo.vecinos_desde("N-0001"), ("N-0002",))

    def test_cierre_de_arista_preserva_el_sentido_opuesto(self) -> None:
        salientes = self.grafo.calles_desde("N-0001", aristas_cerradas=frozenset({"E-0001"}))
        self.assertEqual(salientes, ())
        self.assertEqual(
            tuple(calle.id for calle in self.grafo.calles_desde("N-0002", aristas_cerradas=frozenset({"E-0001"}))),
            ("E-0002", "E-0003"),
        )

    def test_cierre_de_segmento_bloquea_sus_dos_sentidos(self) -> None:
        cerradas = frozenset({"S-0001"})
        self.assertEqual(self.grafo.calles_desde("N-0001", segmentos_cerrados=cerradas), ())
        self.assertEqual(self.grafo.calles_desde("N-0002", segmentos_cerrados=cerradas)[0].id, "E-0003")

    def test_calle_paralela_no_se_cierra_con_otro_segmento(self) -> None:
        paralela = Calle(
            id="E-0099",
            segmento_id="S-0099",
            origen="N-0001",
            destino="N-0002",
            distancia_m=125,
            tipo=TipoCalle.CALLE,
            velocidad_kmh=20,
        )
        mapa = Mapa(
            version=self.mapa.version,
            nodos=self.mapa.nodos,
            calles=self.mapa.calles + (paralela,),
            refugios=self.mapa.refugios,
        )
        grafo = Grafo(mapa)
        habilitadas = grafo.calles_desde("N-0001", segmentos_cerrados=frozenset({"S-0001"}))
        self.assertEqual(tuple(calle.id for calle in habilitadas), ("E-0099",))

    def test_rechaza_nodo_duplicado_y_referencia_rota(self) -> None:
        with self.assertRaisesRegex(ValueError, "Id de nodo duplicado"):
            Mapa("invalido", self.mapa.nodos + (self.mapa.nodos[0],), self.mapa.calles, self.mapa.refugios)

        calle_rota = Calle("E-x", "S-x", "N-0001", "N-no-existe", 10, TipoCalle.CALLE, 20)
        with self.assertRaisesRegex(ValueError, "referencia un nodo inexistente"):
            Mapa("v2", self.mapa.nodos, (calle_rota,), self.mapa.refugios)

    def test_rechaza_distancia_no_positiva(self) -> None:
        with self.assertRaisesRegex(ValueError, "distancia.*positiva"):
            Calle("E-x", "S-x", "N-0001", "N-0002", 0, TipoCalle.CALLE, 20)

    def test_rechaza_tipo_no_normalizado_y_congela_colecciones(self) -> None:
        with self.assertRaisesRegex(ValueError, "categoría.*no está reconocida"):
            Calle("E-x", "S-x", "N-0001", "N-0002", 20, "calle", 20)  # type: ignore[arg-type]

        nodos = list(self.mapa.nodos)
        mapa = Mapa("v2", nodos, list(self.mapa.calles), list(self.mapa.refugios))  # type: ignore[arg-type]
        nodos.clear()
        self.assertEqual(len(mapa.nodos), 4)
        self.assertIsInstance(mapa.calles, tuple)

    def test_evaluacion_exige_cuatro_refugios_en_nodos_distintos(self) -> None:
        mapa_incompleto = Mapa("v2", self.mapa.nodos, self.mapa.calles, self.mapa.refugios[:3])
        with self.assertRaisesRegex(ValueError, "requiere 4 refugios"):
            mapa_incompleto.validar_mapa_evaluacion(minimo_nodos=4)

    def test_loader_rechaza_categoria_desconocida(self) -> None:
        datos = json.loads(FIXTURE.read_text(encoding="utf-8"))
        datos["calles"][0]["tipo"] = "pasaje-desconocido"
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "mapa.json"
            ruta.write_text(json.dumps(datos), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Mapa inválido"):
                cargar_mapa(ruta)

    def test_nodo_desconocido_falla_en_consulta_de_grafo(self) -> None:
        with self.assertRaisesRegex(KeyError, "Nodo desconocido"):
            self.grafo.calles_desde("N-9999")


if __name__ == "__main__":
    unittest.main()
