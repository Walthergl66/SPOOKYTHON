"""Regresiones de movimiento zombie y resolución conjunta del turno."""

import random
import unittest
from dataclasses import replace
from pathlib import Path

from navira.domain.mapa import Grafo, cargar_mapa
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
)
from navira.simulation.resolver import ConfiguracionReglas, resolver_turno


FIXTURE = Path(__file__).parent / "fixtures" / "mapa-minimo.json"


def iniciar(
    turno: int = 0,
    sobrevivientes: tuple[Sobreviviente, ...] = (),
    zombies: tuple[Zombie, ...] = (),
    modo: ModoPartida = ModoPartida.SIMULADOR,
) -> Partida:
    mapa = cargar_mapa(FIXTURE)
    return Partida(
        run_id="run-resolver",
        modo=modo,
        escenario="fixture",
        map_version=mapa.version,
        sobrevivientes=sobrevivientes,
        zombies=zombies,
        estado=EstadoPartida.ACTIVA,
        turno=turno,
        fase=FaseTurno.PREPARACION,
    )


def orden(turno: int, sobreviviente: str, destino: str) -> IntencionMovimiento:
    return IntencionMovimiento(
        "run-resolver", turno, FaseTurno.DECISIONES, sobreviviente, destino
    )


class ResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapa = cargar_mapa(FIXTURE)
        self.grafo = Grafo(self.mapa)

    def resolver(self, partida: Partida, intenciones=(), **opciones):
        return resolver_turno(partida, self.grafo, tuple(intenciones), rng=random.Random(7), **opciones)

    def test_caminante_avanza_un_tramo_cada_dos_turnos(self) -> None:
        zombi = Zombie("Z-1", TipoZombie.CAMINANTE, "N-0001", fase_movimiento=0)
        primero = self.resolver(iniciar(zombies=(zombi,)))
        self.assertEqual(primero.partida.zombies[0].nodo, "N-0002")
        self.assertEqual(len(primero.movimientos_zombies[0].tramos), 1)

        segundo = self.resolver(replace(primero.partida, turno=1, fase=FaseTurno.PREPARACION))
        self.assertEqual(segundo.partida.zombies[0].nodo, "N-0002")
        self.assertEqual(segundo.movimientos_zombies[0].tramos, ())

    def test_corredor_avanza_dos_tramos_hacia_sobreviviente_cercano(self) -> None:
        zombi = Zombie("Z-1", TipoZombie.CORREDOR, "N-0001")
        sobreviviente = Sobreviviente("S-1", "N-0004")
        resultado = self.resolver(iniciar(sobrevivientes=(sobreviviente,), zombies=(zombi,)))
        movimiento = resultado.movimientos_zombies[0]
        self.assertEqual(movimiento.destino, "N-0003")
        self.assertEqual(tuple(calle.id for calle in movimiento.tramos), ("E-0001", "E-0003"))

    def test_horda_queda_fija_y_bloquea_nodo_vecino(self) -> None:
        horda = Zombie("Z-H", TipoZombie.HORDA, "N-0003")
        sobreviviente = Sobreviviente("S-1", "N-0001")
        resultado = self.resolver(
            iniciar(sobrevivientes=(sobreviviente,), zombies=(horda,)),
            (orden(0, "S-1", "N-0002"),),
        )
        self.assertEqual(resultado.partida.zombies[0].nodo, "N-0003")
        self.assertEqual(resultado.partida.sobrevivientes[0].nodo, "N-0001")
        self.assertEqual(resultado.intenciones_rechazadas, ("S-1",))

    def test_dormido_despierta_a_dos_saltos_y_espera_ese_turno(self) -> None:
        dormido = Zombie("Z-D", TipoZombie.DORMIDO, "N-0001", EstadoZombie.DORMIDO)
        sobreviviente = Sobreviviente("S-1", "N-0003")
        resultado = self.resolver(iniciar(sobrevivientes=(sobreviviente,), zombies=(dormido,)))
        actualizado = resultado.partida.zombies[0]
        self.assertEqual(actualizado.tipo, TipoZombie.CAMINANTE)
        self.assertEqual(actualizado.estado, EstadoZombie.ACTIVO)
        self.assertEqual(actualizado.turno_activacion, 0)
        self.assertEqual(actualizado.nodo, "N-0001")
        self.assertEqual(resultado.movimientos_zombies[0].tramos, ())

    def test_opcion_de_configuracion_permite_mover_al_despertar(self) -> None:
        dormido = Zombie("Z-D", TipoZombie.DORMIDO, "N-0001", EstadoZombie.DORMIDO)
        sobreviviente = Sobreviviente("S-1", "N-0003")
        resultado = self.resolver(
            iniciar(turno=1, sobrevivientes=(sobreviviente,), zombies=(dormido,)),
            configuracion=ConfiguracionReglas(dormido_mueve_al_despertar=True),
        )
        self.assertEqual(resultado.partida.zombies[0].nodo, "N-0002")

    def test_movimiento_no_adyacente_se_convierte_en_espera(self) -> None:
        sobreviviente = Sobreviviente("S-1", "N-0001")
        resultado = self.resolver(
            iniciar(sobrevivientes=(sobreviviente,)), (orden(0, "S-1", "N-0004"),)
        )
        self.assertEqual(resultado.partida.sobrevivientes[0].nodo, "N-0001")
        self.assertEqual(resultado.intenciones_rechazadas, ("S-1",))

    def test_captura_por_compartir_nodo_al_final(self) -> None:
        sobreviviente = Sobreviviente("S-1", "N-0002")
        zombi = Zombie("Z-1", TipoZombie.CAMINANTE, "N-0001")
        resultado = self.resolver(iniciar(sobrevivientes=(sobreviviente,), zombies=(zombi,)))
        self.assertEqual(resultado.mordidos, ("S-1",))
        self.assertEqual(resultado.partida.sobrevivientes[0].estado, EstadoSobreviviente.MORDIDO)

    def test_corredor_muerde_en_cruce_opuesto_del_segundo_tramo(self) -> None:
        sobreviviente = Sobreviviente("S-1", "N-0003")
        zombi = Zombie("Z-R", TipoZombie.CORREDOR, "N-0001")
        resultado = self.resolver(
            iniciar(sobrevivientes=(sobreviviente,), zombies=(zombi,)),
            (orden(0, "S-1", "N-0002"),),
        )
        self.assertEqual(tuple(calle.id for calle in resultado.movimientos_zombies[0].tramos), ("E-0001", "E-0003"))
        self.assertEqual(resultado.mordidos, ("S-1",))

    def test_corredor_muerde_en_cruce_opuesto_del_primer_tramo(self) -> None:
        sobreviviente = Sobreviviente("S-1", "N-0002")
        zombi = Zombie("Z-R", TipoZombie.CORREDOR, "N-0001")
        resultado = self.resolver(
            iniciar(sobrevivientes=(sobreviviente,), zombies=(zombi,)),
            (orden(0, "S-1", "N-0001"),),
        )
        self.assertEqual(tuple(calle.id for calle in resultado.movimientos_zombies[0].tramos), ("E-0001",))
        self.assertEqual(resultado.mordidos, ("S-1",))

    def test_evacuacion_ocurre_despues_de_resolver_mordida(self) -> None:
        sobreviviente_en_refugio = Sobreviviente("S-1", "N-0004")
        horda = Zombie("Z-H", TipoZombie.HORDA, "N-0004")
        mordido = self.resolver(
            iniciar(sobrevivientes=(sobreviviente_en_refugio,), zombies=(horda,)),
        )
        self.assertEqual(mordido.mordidos, ("S-1",))
        self.assertEqual(mordido.evacuados, ())

        sobreviviente = Sobreviviente("S-1", "N-0003")
        sin_zombies = self.resolver(
            iniciar(sobrevivientes=(sobreviviente,)), (orden(0, "S-1", "N-0004"),)
        )
        self.assertEqual(sin_zombies.evacuados, ("S-1",))
        self.assertEqual(sin_zombies.partida.sobrevivientes[0].estado, EstadoSobreviviente.EVACUADO)

    def test_sobreviviente_ya_evacuado_no_puede_ser_mordido_en_turnos_posteriores(self) -> None:
        evacuado = Sobreviviente(
            "S-evacuado", "N-0004", estado=EstadoSobreviviente.EVACUADO, refugio_objetivo="R-0004"
        )
        horda = Zombie("Z-H", TipoZombie.HORDA, "N-0004")

        resultado = self.resolver(iniciar(sobrevivientes=(evacuado,), zombies=(horda,)))

        self.assertEqual(resultado.mordidos, ())
        self.assertEqual(resultado.partida.sobrevivientes[0].estado, EstadoSobreviviente.EVACUADO)

    def test_resolucion_comparte_reglas_entre_modulos(self) -> None:
        intencion = orden(0, "S-1", "N-0002")
        resultados = []
        for modo, control in (
            (ModoPartida.SIMULADOR, ControlSobreviviente.AUTOMATICO),
            (ModoPartida.JUEGO, ControlSobreviviente.HUMANO),
        ):
            sobreviviente = Sobreviviente(
                "S-1", "N-0001", control=control, refugio_objetivo="R-0004"
            )
            resultados.append(
                self.resolver(iniciar(sobrevivientes=(sobreviviente,), modo=modo), (intencion,))
            )
        self.assertEqual(
            resultados[0].partida.sobrevivientes[0].nodo,
            resultados[1].partida.sobrevivientes[0].nodo,
        )
        self.assertEqual(resultados[0].mordidos, resultados[1].mordidos)


if __name__ == "__main__":
    unittest.main()
