"""Pruebas del caso de uso de rutas contra un snapshot activo."""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from navira.adapters.mapas_memoria import CatalogoMapasMemoria
from navira.application.decidir_paso import (
    DecidirPaso,
    EntidadNoEncontrada,
    PartidaNoDisponible,
    PasoIncompatible,
    SolicitudPaso,
    _exposicion_pronosticada,
)
from navira.domain.mapa import Calle, Grafo, Mapa, Nodo, Refugio, TipoCalle, cargar_mapa
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
from navira.domain.snapshot import CompromisoRuta
from navira.domain.visibilidad import nodos_horda_visibles
from navira.routing.dijkstra import RutasHaciaRefugios
from navira.simulation.coordinador import MovimientoZombie, SnapshotMundo
from navira.routing.temporal import CondicionTurno


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

    def test_horda_inaccesibiliza_refugio_objetivo_y_recalcula_al_alternativo(self) -> None:
        grafo = Grafo(Mapa(
            version="horda-refugio-alternativo-v1",
            nodos=tuple(Nodo(nodo, 0, indice) for indice, nodo in enumerate(
                ("ORIGEN", "HORDA", "VECINO_HORDA", "DESVIO", "REFUGIO_1", "REFUGIO_2")
            )),
            calles=(
                Calle("E-OV", "S-OV", "ORIGEN", "VECINO_HORDA", 10, TipoCalle.CALLE, 20),
                Calle("E-HV", "S-HV", "HORDA", "VECINO_HORDA", 10, TipoCalle.CALLE, 20),
                Calle("E-VR1", "S-VR1", "VECINO_HORDA", "REFUGIO_1", 10, TipoCalle.CALLE, 20),
                Calle("E-OD", "S-OD", "ORIGEN", "DESVIO", 15, TipoCalle.CALLE, 20),
                Calle("E-DR2", "S-DR2", "DESVIO", "REFUGIO_2", 15, TipoCalle.CALLE, 20),
            ),
            refugios=(Refugio("R-1", "REFUGIO_1"), Refugio("R-2", "REFUGIO_2")),
        ))
        partida = Partida(
            run_id="run-horda-refugio-alternativo",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-1", "ORIGEN", refugio_objetivo="R-1"),),
            zombies=(Zombie("Z-H", TipoZombie.HORDA, "HORDA"),),
            estado=EstadoPartida.ACTIVA,
            turno=1,
            fase=FaseTurno.DECISIONES,
        )
        snapshot = SnapshotMundo(partida, version=1)
        servicio = DecidirPaso(SnapshotStub(snapshot), CatalogoMapasMemoria((grafo,)))

        ruta = servicio.prever_ruta(SolicitudPaso("S-1", "ORIGEN", 1))
        compromiso = servicio.proponer_compromiso_en_snapshot(snapshot, "S-1", grafo)

        self.assertEqual(ruta, ("ORIGEN", "DESVIO", "REFUGIO_2"))
        self.assertNotIn("VECINO_HORDA", ruta)
        self.assertEqual(servicio.ejecutar(SolicitudPaso("S-1", "ORIGEN", 1)).siguiente_nodo, "DESVIO")
        self.assertIsNotNone(compromiso)
        self.assertEqual(compromiso.refugio_id, "R-2")

    def test_grupo_replanifica_a_otro_refugio_si_el_objetivo_queda_bloqueado(self) -> None:
        grafo = Grafo(Mapa(
            version="grupo-refugio-alternativo-v1",
            nodos=tuple(Nodo(nodo, 0, indice) for indice, nodo in enumerate(
                ("ORIGEN_1", "ORIGEN_2", "HORDA", "VECINO_HORDA", "DESVIO", "REFUGIO_1", "REFUGIO_2")
            )),
            calles=(
                Calle("E-1V", "S-1V", "ORIGEN_1", "VECINO_HORDA", 10, TipoCalle.CALLE, 20),
                Calle("E-2V", "S-2V", "ORIGEN_2", "VECINO_HORDA", 10, TipoCalle.CALLE, 20),
                Calle("E-HV", "S-HV", "HORDA", "VECINO_HORDA", 10, TipoCalle.CALLE, 20),
                Calle("E-VR1", "S-VR1", "VECINO_HORDA", "REFUGIO_1", 10, TipoCalle.CALLE, 20),
                Calle("E-1D", "S-1D", "ORIGEN_1", "DESVIO", 15, TipoCalle.CALLE, 20),
                Calle("E-2D", "S-2D", "ORIGEN_2", "DESVIO", 15, TipoCalle.CALLE, 20),
                Calle("E-DR2", "S-DR2", "DESVIO", "REFUGIO_2", 15, TipoCalle.CALLE, 20),
            ),
            refugios=(Refugio("R-1", "REFUGIO_1"), Refugio("R-2", "REFUGIO_2")),
        ))
        partida = Partida(
            run_id="run-grupo-refugio-alternativo",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=grafo.mapa.version,
            sobrevivientes=(
                Sobreviviente("S-1", "ORIGEN_1", refugio_objetivo="R-1"),
                Sobreviviente("S-2", "ORIGEN_2", refugio_objetivo="R-1"),
            ),
            zombies=(Zombie("Z-H", TipoZombie.HORDA, "HORDA"),),
            estado=EstadoPartida.ACTIVA,
            turno=1,
            fase=FaseTurno.DECISIONES,
        )
        servicio = DecidirPaso(
            SnapshotStub(SnapshotMundo(partida, version=1)), CatalogoMapasMemoria((grafo,))
        )

        rutas = tuple(
            servicio.prever_ruta(SolicitudPaso(persona.id, persona.nodo, 1))
            for persona in partida.sobrevivientes
        )

        self.assertEqual(rutas, (
            ("ORIGEN_1", "DESVIO", "REFUGIO_2"),
            ("ORIGEN_2", "DESVIO", "REFUGIO_2"),
        ))

    def test_incidente_y_zombie_en_ruta_no_dejan_habitante_deteniendo_su_ruta(self) -> None:
        grafo = Grafo(Mapa(
            version="incidente-zombie-refugio-alternativo-v1",
            nodos=tuple(Nodo(nodo, 0, indice) for indice, nodo in enumerate(
                ("ORIGEN", "PASO_BLOQUEADO", "DESVIO", "PASO_ALTERNATIVO", "REFUGIO_1", "REFUGIO_2")
            )),
            calles=(
                Calle("E-OB", "S-OB", "ORIGEN", "PASO_BLOQUEADO", 10, TipoCalle.CALLE, 20),
                Calle("E-BR1", "S-BR1", "PASO_BLOQUEADO", "REFUGIO_1", 10, TipoCalle.CALLE, 20),
                Calle("E-OD", "S-OD", "ORIGEN", "DESVIO", 15, TipoCalle.CALLE, 20),
                Calle("E-DP", "S-DP", "DESVIO", "PASO_ALTERNATIVO", 15, TipoCalle.CALLE, 20),
                Calle("E-PR2", "S-PR2", "PASO_ALTERNATIVO", "REFUGIO_2", 10, TipoCalle.CALLE, 20),
            ),
            refugios=(Refugio("R-1", "REFUGIO_1"), Refugio("R-2", "REFUGIO_2")),
        ))
        partida = Partida(
            run_id="run-incidente-zombie-refugio-alternativo",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-1", "ORIGEN", refugio_objetivo="R-1"),),
            zombies=(Zombie("Z-1", TipoZombie.CAMINANTE, "PASO_BLOQUEADO"),),
            estado=EstadoPartida.ACTIVA,
            turno=1,
            fase=FaseTurno.DECISIONES,
        )
        snapshot = SnapshotMundo(partida, version=1, segmentos_cerrados=frozenset({"S-OB"}))
        servicio = DecidirPaso(SnapshotStub(snapshot), CatalogoMapasMemoria((grafo,)))

        ruta = servicio.prever_ruta(SolicitudPaso("S-1", "ORIGEN", 1))

        self.assertEqual(ruta, ("ORIGEN", "DESVIO", "PASO_ALTERNATIVO", "REFUGIO_2"))
        self.assertNotEqual(servicio.ejecutar(SolicitudPaso("S-1", "ORIGEN", 1)).siguiente_nodo, "ORIGEN")

    def test_horda_conserva_todos_sus_vecinos_aunque_sus_calles_estan_cerradas(self) -> None:
        partida = Partida(
            run_id="run-horda-cierres",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=self.grafo.mapa.version,
            sobrevivientes=self.partida.sobrevivientes,
            zombies=(Zombie("Z-H", TipoZombie.HORDA, "N-0002"),),
            estado=EstadoPartida.ACTIVA,
            turno=4,
            fase=FaseTurno.DECISIONES,
        )
        snapshot = SnapshotMundo(
            partida,
            version=1,
            segmentos_cerrados=frozenset({"S-0001", "S-0002"}),
        )

        bloqueados = nodos_horda_visibles(snapshot, self.grafo)

        self.assertEqual(bloqueados, frozenset({"N-0001", "N-0002", "N-0003"}))

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

    def test_rechaza_partida_cuyo_mapa_no_coincide_con_el_grafo(self) -> None:
        partida = Partida(
            run_id=self.partida.run_id,
            modo=self.partida.modo,
            escenario=self.partida.escenario,
            map_version="mapa-obsoleto",
            sobrevivientes=self.partida.sobrevivientes,
            estado=self.partida.estado,
            turno=self.partida.turno,
            fase=self.partida.fase,
        )
        servicio = DecidirPaso(
            SnapshotStub(SnapshotMundo(partida, version=1)),
            CatalogoMapasMemoria((self.grafo,)),
        )

        with self.assertRaises(PartidaNoDisponible):
            servicio.ejecutar(self.solicitud())

    def test_valida_nodo_y_refugio_del_actor_solicitado_sin_recorrer_la_cohorte(self) -> None:
        for nodo, refugio in (("N-404", "R-0004"), ("N-0001", "R-404")):
            with self.subTest(nodo=nodo, refugio=refugio):
                persona = Sobreviviente("S-1", nodo, refugio_objetivo=refugio)
                partida = Partida(
                    run_id=self.partida.run_id,
                    modo=self.partida.modo,
                    escenario=self.partida.escenario,
                    map_version=self.grafo.mapa.version,
                    sobrevivientes=(persona,),
                    estado=self.partida.estado,
                    turno=self.partida.turno,
                    fase=self.partida.fase,
                )
                servicio = DecidirPaso(
                    SnapshotStub(SnapshotMundo(partida, version=1)),
                    CatalogoMapasMemoria((self.grafo,)),
                )

                with self.assertRaises(PartidaNoDisponible):
                    servicio.ejecutar(self.solicitud(nodo=nodo))

    def test_ruta_temporal_prefiere_menos_exposicion_antes_que_distancia(self) -> None:
        grafo = Grafo(
            Mapa(
                version="riesgo-observable-v1",
                nodos=tuple(Nodo(f"N-{indice}", 0, indice) for indice in range(1, 7)),
                calles=(
                    Calle("E-12", "S-12", "N-1", "N-2", 1, TipoCalle.CALLE, 30),
                    Calle("E-25", "S-25", "N-2", "N-5", 1, TipoCalle.CALLE, 30),
                    Calle("E-54", "S-54", "N-5", "N-4", 1, TipoCalle.CALLE, 30),
                    Calle("E-13", "S-13", "N-1", "N-3", 10, TipoCalle.CALLE, 30),
                    Calle("E-36", "S-36", "N-3", "N-6", 10, TipoCalle.CALLE, 30),
                    Calle("E-64", "S-64", "N-6", "N-4", 10, TipoCalle.CALLE, 30),
                ),
                refugios=(Refugio("R-4", "N-4"),),
            )
        )
        partida = Partida(
            run_id="run-risk-first",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-1", "N-1", refugio_objetivo="R-4"),),
            estado=EstadoPartida.ACTIVA,
            turno=1,
            fase=FaseTurno.DECISIONES,
        )
        snapshots = SnapshotStub(SnapshotMundo(partida, version=1))
        servicio = DecidirPaso(snapshots, CatalogoMapasMemoria((grafo,)))
        escenario = SimpleNamespace(
            turnos=(CondicionTurno(exposicion_nodo={"N-5": 1.0}), CondicionTurno()),
            supuestos=("riesgo_sintetico_de_prueba",),
        )

        with patch(
            "navira.application.decidir_paso.pronosticar_zombies_visibles",
            return_value=escenario,
        ) as pronosticar:
            decision = servicio.ejecutar(SolicitudPaso("S-1", "N-1", 1))
            trayecto = servicio.prever_ruta(SolicitudPaso("S-1", "N-1", 1))

        self.assertEqual(decision.siguiente_nodo, "N-3")
        self.assertEqual(trayecto, ("N-1", "N-3", "N-6", "N-4"))
        self.assertEqual(pronosticar.call_count, 1)

    def test_no_extiende_el_ultimo_riesgo_pronosticado_mas_alla_del_horizonte(self) -> None:
        futuro = (CondicionTurno(exposicion_nodo={"C": 0.8, "D": 1.0}),)

        exposicion = _exposicion_pronosticada(("A", "B", "C", "D", "E"), futuro)

        # Solo el primer paso está modelado; riesgos de turnos C/D/E no se copian.
        self.assertEqual(exposicion, 0.0)

    def _servicio_linea(self, nodos, calles_pares, refugio, posiciones, run_id):
        calles = tuple(
            Calle(f"E-{a}-{b}", f"S-{a}-{b}", a, b, 10, TipoCalle.CALLE, 20)
            for a, b in calles_pares for a, b in ((a, b), (b, a))
        )
        grafo = Grafo(Mapa(
            version=run_id, nodos=tuple(Nodo(n, 0, i) for i, n in enumerate(nodos)),
            calles=calles, refugios=(Refugio("R-X", refugio),) if refugio else (),
        ))
        partida = Partida(
            run_id=run_id, modo=ModoPartida.SIMULADOR, escenario="fixture",
            map_version=grafo.mapa.version,
            sobrevivientes=tuple(Sobreviviente(f"S-{i}", n) for i, n in enumerate(posiciones, 1)),
            estado=EstadoPartida.ACTIVA, turno=1, fase=FaseTurno.DECISIONES,
        )
        return DecidirPaso(SnapshotStub(SnapshotMundo(partida, version=1)), CatalogoMapasMemoria((grafo,)))

    def test_no_oscila_ir_y_volver_que_solo_explota_el_recorte_del_horizonte(self) -> None:
        linea = [f"P{i}" for i in range(15)]
        pares = list(zip(linea, linea[1:])) + [("P0", "L")]

        def decidir(actual):
            servicio = self._servicio_linea(linea + ["L"], pares, "P14", [actual, actual], f"osc-{actual}")
            futuras = tuple(
                CondicionTurno(exposicion_nodo={"P12": 1.0} if i in (10, 11) else {}) for i in range(12)
            )
            escenario = SimpleNamespace(turnos=futuras, supuestos=())
            with patch("navira.application.decidir_paso.pronosticar_zombies_visibles", return_value=escenario):
                return servicio.ejecutar(SolicitudPaso("S-1", actual, 1)).siguiente_nodo

        primero = decidir("P0")
        segundo = decidir("P1")
        self.assertEqual(primero, "P1")
        self.assertNotEqual(segundo, "P0")

    def test_sin_refugio_alcanzable_y_nodos_libres_espera(self) -> None:
        servicio = self._servicio_linea(["A", "B", "Z"], [("A", "B")], "Z", ["A", "A"], "espera")
        self.assertEqual(servicio.prever_ruta(SolicitudPaso("S-1", "A", 1)), ("A",))
        solo = self._servicio_linea(["A", "B", "Z"], [("A", "B")], "Z", ["A"], "espera-1")
        self.assertEqual(solo.prever_ruta(SolicitudPaso("S-1", "A", 1)), ("A",))

    def test_indicador_y_accion_reutilizan_la_misma_ruta_del_snapshot(self) -> None:
        servicio = self.servicio()
        with patch.object(servicio, "_seleccionar_trayecto", wraps=servicio._seleccionar_trayecto) as seleccionar:
            ruta = servicio.prever_ruta(self.solicitud())
            decision = servicio.ejecutar(self.solicitud())

        self.assertEqual(decision.siguiente_nodo, ruta[1])
        self.assertEqual(seleccionar.call_count, 1)

    def test_plan_compartido_reparte_un_embudo_sin_cambiar_reglas_de_riesgo(self) -> None:
        grafo = Grafo(Mapa(
            version="coordinacion-v1",
            nodos=tuple(Nodo(n, 0, i) for i, n in enumerate(("A", "B", "C", "D"))),
            calles=(
                Calle("E-AB", "S-AB", "A", "B", 10, TipoCalle.CALLE, 20),
                Calle("E-AC", "S-AC", "A", "C", 10, TipoCalle.CALLE, 20),
                Calle("E-BD", "S-BD", "B", "D", 10, TipoCalle.CALLE, 20),
                Calle("E-CD", "S-CD", "C", "D", 10, TipoCalle.CALLE, 20),
            ),
            refugios=(Refugio("R-D", "D"),),
        ))
        partida = Partida(
            run_id="run-coordination", modo=ModoPartida.SIMULADOR, escenario="fixture",
            map_version=grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-1", "A"), Sobreviviente("S-2", "A")),
            estado=EstadoPartida.ACTIVA, turno=1, fase=FaseTurno.DECISIONES,
        )
        servicio = DecidirPaso(
            SnapshotStub(SnapshotMundo(partida, version=1)), CatalogoMapasMemoria((grafo,))
        )

        ruta_1 = servicio.prever_ruta(SolicitudPaso("S-1", "A", 1))
        ruta_2 = servicio.prever_ruta(SolicitudPaso("S-2", "A", 1))

        self.assertEqual({ruta_1[1], ruta_2[1]}, {"B", "C"})
        self.assertEqual(
            servicio.ejecutar(SolicitudPaso("S-1", "A", 1)).siguiente_nodo, ruta_1[1]
        )
        self.assertEqual(
            servicio.ejecutar(SolicitudPaso("S-2", "A", 1)).siguiente_nodo, ruta_2[1]
        )

    def test_congestion_no_envia_a_una_salida_con_mayor_exposicion(self) -> None:
        grafo = Grafo(Mapa(
            version="coordinacion-riesgo-v1",
            nodos=tuple(Nodo(n, 0, i) for i, n in enumerate(("A", "B", "C", "D"))),
            calles=(
                Calle("E-AB", "S-AB", "A", "B", 1, TipoCalle.CALLE, 20),
                Calle("E-AC", "S-AC", "A", "C", 10, TipoCalle.CALLE, 20),
                Calle("E-BD", "S-BD", "B", "D", 1, TipoCalle.CALLE, 20),
                Calle("E-CD", "S-CD", "C", "D", 10, TipoCalle.CALLE, 20),
            ),
            refugios=(Refugio("R-D", "D"),),
        ))
        partida = Partida(
            run_id="run-coordination-risk", modo=ModoPartida.SIMULADOR, escenario="fixture",
            map_version=grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-1", "A"), Sobreviviente("S-2", "A")),
            estado=EstadoPartida.ACTIVA, turno=1, fase=FaseTurno.DECISIONES,
        )
        servicio = DecidirPaso(
            SnapshotStub(SnapshotMundo(partida, version=1)), CatalogoMapasMemoria((grafo,))
        )
        pronostico = SimpleNamespace(
            turnos=(CondicionTurno(exposicion_nodo={"B": 1.0}), CondicionTurno()),
            supuestos=("riesgo_sintetico_de_prueba",),
        )
        with patch(
            "navira.application.decidir_paso.pronosticar_zombies_visibles",
            return_value=pronostico,
        ):
            ruta_1 = servicio.prever_ruta(SolicitudPaso("S-1", "A", 1))
            ruta_2 = servicio.prever_ruta(SolicitudPaso("S-2", "A", 1))

        self.assertEqual(ruta_1[1], "C")
        self.assertEqual(ruta_2[1], "C")

    def test_snapshot_nuevo_invalida_el_trayecto_cacheado(self) -> None:
        servicio = self.servicio()
        stub = servicio._snapshots
        with patch.object(
            servicio,
            "_seleccionar_trayecto",
            side_effect=(("N-0001", "N-0002"), ("N-0001", "N-0003")),
        ) as seleccionar:
            primera = servicio.prever_ruta(self.solicitud())
            stub.snapshot = SnapshotMundo(self.partida, version=2)
            segunda = servicio.prever_ruta(self.solicitud())

        self.assertEqual(primera, ("N-0001", "N-0002"))
        self.assertEqual(segunda, ("N-0001", "N-0003"))
        self.assertEqual(seleccionar.call_count, 2)

    def test_sin_ruta_completa_espera_si_la_unica_salida_esta_junto_a_zombie(self) -> None:
        grafo = Grafo(
            Mapa(
                version="escape-inmediato-v1",
                nodos=(Nodo("A", 0, 0), Nodo("B", 0, 1), Nodo("C", 0, 2)),
                calles=(
                    Calle("E-AB", "S-AB", "A", "B", 10, TipoCalle.CALLE, 20),
                    Calle("E-BC", "S-BC", "B", "C", 10, TipoCalle.CALLE, 20),
                ),
                refugios=(Refugio("R-C", "C"),),
            )
        )
        partida = Partida(
            run_id="run-escape-inmediato",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-escape", "A"),),
            zombies=(Zombie("Z-ocupando-refugio", TipoZombie.CAMINANTE, "C"),),
            estado=EstadoPartida.ACTIVA,
            turno=1,
            fase=FaseTurno.DECISIONES,
        )
        servicio = DecidirPaso(
            SnapshotStub(SnapshotMundo(partida, version=1)),
            CatalogoMapasMemoria((grafo,)),
        )

        decision = servicio.ejecutar(SolicitudPaso("S-escape", "A", 1))
        ruta = servicio.prever_ruta(SolicitudPaso("S-escape", "A", 1))

        self.assertEqual(decision.siguiente_nodo, "A")
        self.assertEqual(ruta[:2], ("A", "A"))

    def test_rodea_vecino_de_zombie_si_hay_una_alternativa(self) -> None:
        grafo = Grafo(
            Mapa(
                version="riesgo-vecinal-v1",
                nodos=tuple(Nodo(node, 0, index) for index, node in enumerate(("S", "A", "B", "C", "R", "Z"))),
                calles=(
                    Calle("E-SA", "SA", "S", "A", 10, TipoCalle.CALLE, 20),
                    Calle("E-AS", "SA", "A", "S", 10, TipoCalle.CALLE, 20),
                    Calle("E-AR", "AR", "A", "R", 10, TipoCalle.CALLE, 20),
                    Calle("E-RA", "AR", "R", "A", 10, TipoCalle.CALLE, 20),
                    Calle("E-SB", "SB", "S", "B", 10, TipoCalle.CALLE, 20),
                    Calle("E-BS", "SB", "B", "S", 10, TipoCalle.CALLE, 20),
                    Calle("E-BC", "BC", "B", "C", 10, TipoCalle.CALLE, 20),
                    Calle("E-CB", "BC", "C", "B", 10, TipoCalle.CALLE, 20),
                    Calle("E-CR", "CR", "C", "R", 10, TipoCalle.CALLE, 20),
                    Calle("E-RC", "CR", "R", "C", 10, TipoCalle.CALLE, 20),
                    Calle("E-ZA", "ZA", "Z", "A", 10, TipoCalle.CALLE, 20),
                    Calle("E-AZ", "ZA", "A", "Z", 10, TipoCalle.CALLE, 20),
                ),
                refugios=(Refugio("R-1", "R"),),
            )
        )
        partida = Partida(
            run_id="run-riesgo-vecinal",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=grafo.mapa.version,
            sobrevivientes=(Sobreviviente("S-1", "S"),),
            zombies=(Zombie("Z-1", TipoZombie.CAMINANTE, "Z"),),
            estado=EstadoPartida.ACTIVA,
            turno=1,
            fase=FaseTurno.DECISIONES,
        )
        servicio = DecidirPaso(
            SnapshotStub(SnapshotMundo(partida, version=1)),
            CatalogoMapasMemoria((grafo,)),
        )

        ruta = servicio.prever_ruta(SolicitudPaso("S-1", "S", 1))

        self.assertEqual(ruta[1], "B")

    def test_invalida_compromiso_si_un_zombie_ocupa_un_nodo_mas_adelante(self) -> None:
        nodos = tuple(Nodo(node, 0, index) for index, node in enumerate("ABCDEFG"))
        calles = tuple(
            calle
            for origen, destino in zip("ABCDEF", "BCDEFG")
            for calle in (
                Calle(f"E-{origen}{destino}", f"S-{origen}{destino}", origen, destino, 10, TipoCalle.CALLE, 20),
                Calle(f"E-{destino}{origen}", f"S-{origen}{destino}", destino, origen, 10, TipoCalle.CALLE, 20),
            )
        )
        grafo = Grafo(Mapa("compromiso-peligro-v1", nodos, calles, (Refugio("R-G", "G"),)))
        persona = Sobreviviente("S-1", "A", refugio_objetivo="R-G")
        partida = Partida(
            run_id="run-compromiso-peligro",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=grafo.mapa.version,
            sobrevivientes=(persona,),
            zombies=(Zombie("Z-lejano", TipoZombie.CAMINANTE, "E"),),
            estado=EstadoPartida.ACTIVA,
            turno=1,
            fase=FaseTurno.DECISIONES,
        )
        compromiso = CompromisoRuta("S-1", "R-G", tuple("ABCDEFG"))
        snapshot = SnapshotMundo(partida, version=1, rutas_comprometidas=(compromiso,))
        servicio = DecidirPaso(SnapshotStub(snapshot), CatalogoMapasMemoria((grafo,)))

        retenida = servicio._ruta_comprometida_vigente(snapshot, grafo, persona, compromiso)

        self.assertIsNone(retenida)

    def test_comparte_campo_estatico_entre_compromisos_invalidos_del_mismo_refugio(self) -> None:
        personas = (
            Sobreviviente("S-1", "N-0001", refugio_objetivo="R-0004"),
            Sobreviviente("S-2", "N-0002", refugio_objetivo="R-0004"),
        )
        partida = Partida(
            run_id="run-campo-compartido",
            modo=ModoPartida.SIMULADOR,
            escenario="fixture",
            map_version=self.grafo.mapa.version,
            sobrevivientes=personas,
            estado=EstadoPartida.ACTIVA,
            turno=4,
            fase=FaseTurno.DECISIONES,
        )
        compromisos = (
            CompromisoRuta("S-1", "R-0004", ("N-0002", "N-0003", "N-0004")),
            CompromisoRuta("S-2", "R-0004", ("N-0001", "N-0002", "N-0003", "N-0004")),
        )
        snapshot = SnapshotMundo(partida, version=4, rutas_comprometidas=compromisos)
        servicio = DecidirPaso(SnapshotStub(snapshot), CatalogoMapasMemoria((self.grafo,)))

        with patch(
            "navira.application.decidir_paso.RutasHaciaRefugios",
            wraps=RutasHaciaRefugios,
        ) as campos:
            rutas = servicio._planificar_conjunto(snapshot, self.grafo)

        self.assertEqual(campos.call_count, 1)
        self.assertEqual(rutas["S-1"], ("N-0001", "N-0002", "N-0003", "N-0004"))
        self.assertEqual(rutas["S-2"], ("N-0002", "N-0003", "N-0004"))


if __name__ == "__main__":
    unittest.main()
