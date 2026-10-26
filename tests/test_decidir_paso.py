"""Pruebas del caso de uso de rutas contra un snapshot activo."""

import unittest
from pathlib import Path

from navira.adapters.mapas_memoria import CatalogoMapasMemoria
from navira.application.decidir_paso import (
    DecidirPaso,
    EntidadNoEncontrada,
    PartidaNoDisponible,
    PasoIncompatible,
    SolicitudPaso,
)
from navira.domain.mapa import Grafo, cargar_mapa
from navira.domain.modelo import (
    EstadoPartida,
    EstadoZombie,
    FaseTurno,
    ModoPartida,
    Partida,
    Sobreviviente,
    TipoZombie,
    Zombie,
)
from navira.simulation.coordinador import MovimientoZombie, SnapshotMundo


FIXTURE = Path(__file__).parent / "fixtures" / "mapa-minimo.json"


class SnapshotStub:
    def __init__(self, snapshot: SnapshotMundo | None) -> None:
        self.snapshot = snapshot

    def obtener_activa(self) -> SnapshotMundo | None:
        return self.snapshot


class DecidirPasoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo = Grafo(cargar_mapa(FIXTURE))
        sobreviviente = Sobreviviente("S-1", "N-0001", refugio_objetivo="R-0004")
        partida = Partida(
            run_id="run-step",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=self.grafo.mapa.version,
            sobrevivientes=(sobreviviente,),
            estado=EstadoPartida.ACTIVA,
            turno=4,
            fase=FaseTurno.DECISIONES,
        )
        self.partida = partida

    def servicio(self, *, zombies=(), cierres=frozenset(), movimientos=(), fase=FaseTurno.DECISIONES):
        partida = Partida(
            run_id=self.partida.run_id,
            modo=self.partida.modo,
            escenario=self.partida.escenario,
            map_version=self.partida.map_version,
            sobrevivientes=self.partida.sobrevivientes,
            zombies=tuple(zombies),
            estado=self.partida.estado,
            turno=self.partida.turno,
            fase=fase,
        )
        snapshot = SnapshotMundo(
            partida=partida,
            version=1,
            aristas_cerradas=frozenset(cierres),
            movimientos_zombies=tuple(movimientos),
        )
        return DecidirPaso(SnapshotStub(snapshot), CatalogoMapasMemoria((self.grafo,)))

    def solicitud(self, *, turno=4, nodo="N-0001", personaje="S-1"):
        return SolicitudPaso(personaje, nodo, turno)

    def test_devuelve_siguiente_vecino_de_ruta_a_refugio_objetivo(self) -> None:
        decision = self.servicio().ejecutar(self.solicitud())
        self.assertEqual(decision.siguiente_nodo, "N-0002")

    def test_sin_ruta_por_cierre_espera_sin_fingir_seguridad(self) -> None:
        decision = self.servicio(cierres={"E-0001"}).ejecutar(self.solicitud())
        self.assertEqual(decision.siguiente_nodo, "N-0001")

    def test_peligro_activo_bloquea_ingreso_y_dormido_no_se_filtra(self) -> None:
        activo = Zombie("Z-A", TipoZombie.CAMINANTE, "N-0002")
        dormido = Zombie("Z-D", TipoZombie.DORMIDO, "N-0002", EstadoZombie.DORMIDO)
        espera = self.servicio(zombies=(activo,)).ejecutar(self.solicitud())
        avanza = self.servicio(zombies=(dormido,)).ejecutar(self.solicitud())
        self.assertEqual(espera.siguiente_nodo, "N-0001")
        self.assertEqual(avanza.siguiente_nodo, "N-0002")

    def test_horda_bloquea_vecinos_y_cruce_conocido_se_evade(self) -> None:
        horda = Zombie("Z-H", TipoZombie.HORDA, "N-0002")
        movimiento = MovimientoZombie("Z-A", "N-0002", "N-0001", (self.grafo.mapa.calles[1],))
        resultado_horda = self.servicio(zombies=(horda,)).ejecutar(self.solicitud())
        resultado_cruce = self.servicio(movimientos=(movimiento,)).ejecutar(self.solicitud())
        self.assertEqual(resultado_horda.siguiente_nodo, "N-0001")
        self.assertEqual(resultado_cruce.siguiente_nodo, "N-0001")

    def test_estado_turno_fase_posicion_y_personaje_se_validan(self) -> None:
        servicio = self.servicio()
        with self.assertRaises(PasoIncompatible):
            servicio.ejecutar(self.solicitud(turno=3))
        with self.assertRaises(PasoIncompatible):
            servicio.ejecutar(self.solicitud(nodo="N-0002"))
        with self.assertRaises(EntidadNoEncontrada):
            servicio.ejecutar(self.solicitud(personaje="S-404"))
        with self.assertRaises(PasoIncompatible):
            self.servicio(fase=FaseTurno.RESUELTA).ejecutar(self.solicitud())

    def test_sin_partida_o_mapa_versionado_es_error_de_estado(self) -> None:
        vacio = DecidirPaso(SnapshotStub(None), CatalogoMapasMemoria())
        with self.assertRaises(PartidaNoDisponible):
            vacio.ejecutar(self.solicitud())
        sin_mapa = DecidirPaso(
            SnapshotStub(SnapshotMundo(partida=self.partida, version=1)),
            CatalogoMapasMemoria(),
        )
        with self.assertRaises(PartidaNoDisponible):
            sin_mapa.ejecutar(self.solicitud())


if __name__ == "__main__":
    unittest.main()
