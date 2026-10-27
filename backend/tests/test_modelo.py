"""Invariantes de partida e intenciones compartidas por ambos modos."""

import unittest
from pathlib import Path

from navira.domain.mapa import cargar_mapa
from navira.domain.modelo import (
    ControlSobreviviente,
    EstadoPartida,
    EstadoSobreviviente,
    EstadoZombie,
    FaseTurno,
    IntencionMovimiento,
    ModoPartida,
    Partida,
    Sobreviviente,
    TipoZombie,
    Zombie,
    validar_contexto_intencion,
)


FIXTURE = Path(__file__).parent / "fixtures" / "mapa-minimo.json"


def partida_activa(modo: ModoPartida = ModoPartida.SIMULADOR, **cambios: object) -> Partida:
    valores: dict[str, object] = {
        "run_id": "run-1",
        "modo": modo,
        "escenario": "fixture",
        "map_version": "fixture-sintetico-v1",
        "estado": EstadoPartida.ACTIVA,
        "turno": 12,
        "fase": FaseTurno.DECISIONES,
    }
    valores.update(cambios)
    return Partida(**valores)  # type: ignore[arg-type]


class ModeloTests(unittest.TestCase):
    def test_partida_valida_mapa_y_version(self) -> None:
        mapa = cargar_mapa(FIXTURE)
        partida = partida_activa(
            sobrevivientes=(Sobreviviente("S-1", "N-0001"),),
            zombies=(Zombie("Z-1", TipoZombie.CAMINANTE, "N-0002"),),
        )
        partida.validar_mapa(mapa)

        with self.assertRaisesRegex(ValueError, "versión de mapa"):
            partida.validar_mapa(type(mapa)("mapa-otra-version", mapa.nodos, mapa.calles, mapa.refugios))

    def test_partida_rechaza_nodo_desconocido_e_ids_duplicados(self) -> None:
        mapa = cargar_mapa(FIXTURE)
        partida = partida_activa(sobrevivientes=(Sobreviviente("S-1", "N-fantasma"),))
        with self.assertRaisesRegex(ValueError, "nodo inexistente"):
            partida.validar_mapa(mapa)

        with self.assertRaisesRegex(ValueError, "IDs.*únicos"):
            partida_activa(
                sobrevivientes=(Sobreviviente("X-1", "N-0001"),),
                zombies=(Zombie("X-1", TipoZombie.CAMINANTE, "N-0002"),),
            )

    def test_partida_rechaza_refugio_objetivo_desconocido(self) -> None:
        partida = partida_activa(
            sobrevivientes=(Sobreviviente("S-1", "N-0001", refugio_objetivo="R-fantasma"),)
        )
        with self.assertRaisesRegex(ValueError, "refugio inexistente"):
            partida.validar_mapa(cargar_mapa(FIXTURE))

    def test_ambos_modos_usan_el_mismo_contrato_de_intencion(self) -> None:
        sobreviviente = Sobreviviente(
            "S-1", "N-0001", control=ControlSobreviviente.HUMANO
        )
        intencion = IntencionMovimiento("run-1", 12, FaseTurno.DECISIONES, "S-1", "N-0002")

        for modo in (ModoPartida.SIMULADOR, ModoPartida.JUEGO):
            with self.subTest(modo=modo):
                validar_contexto_intencion(partida_activa(modo), sobreviviente, intencion)

    def test_intencion_rechaza_otra_partida_turno_fase_o_personaje(self) -> None:
        partida = partida_activa()
        sobreviviente = Sobreviviente("S-1", "N-0001")
        casos = (
            IntencionMovimiento("run-2", 12, FaseTurno.DECISIONES, "S-1", "N-0002"),
            IntencionMovimiento("run-1", 13, FaseTurno.DECISIONES, "S-1", "N-0002"),
            IntencionMovimiento("run-1", 12, FaseTurno.ZOMBIES_MOVIDOS, "S-1", "N-0002"),
            IntencionMovimiento("run-1", 12, FaseTurno.DECISIONES, "S-2", "N-0002"),
        )
        for intencion in casos:
            with self.subTest(intencion=intencion), self.assertRaises(ValueError):
                validar_contexto_intencion(partida, sobreviviente, intencion)

    def test_partida_y_sobreviviente_inactivos_no_aceptan_intencion(self) -> None:
        sobreviviente = Sobreviviente("S-1", "N-0001")
        intencion = IntencionMovimiento("run-1", 12, FaseTurno.DECISIONES, "S-1", "N-0002")
        with self.assertRaisesRegex(ValueError, "no está activa"):
            validar_contexto_intencion(
                partida_activa(estado=EstadoPartida.FINALIZADA), sobreviviente, intencion
            )

        mordido = Sobreviviente("S-1", "N-0001", estado=EstadoSobreviviente.MORDIDO)
        with self.assertRaisesRegex(ValueError, "inactivo"):
            validar_contexto_intencion(partida_activa(), mordido, intencion)

    def test_zombie_y_intencion_rechazan_estados_invalidos(self) -> None:
        with self.assertRaisesRegex(ValueError, "Tipo de zombie"):
            Zombie("Z-1", "fantasma", "N-0001")  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "turno de activación"):
            Zombie("Z-1", TipoZombie.DORMIDO, "N-0001", EstadoZombie.DORMIDO, -1)
        with self.assertRaisesRegex(ValueError, "tipo dormido"):
            Zombie("Z-2", TipoZombie.CAMINANTE, "N-0001", EstadoZombie.DORMIDO)


if __name__ == "__main__":
    unittest.main()
