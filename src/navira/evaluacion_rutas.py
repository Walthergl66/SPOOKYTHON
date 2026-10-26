"""Compara Dijkstra y política temporal con mundos sintéticos emparejados."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from time import perf_counter
from typing import Iterable, TextIO
import sys

from navira.application.decidir_paso import peligros_visibles
from navira.demo import ESCENARIOS_DEMO, crear_contexto_demo
from navira.domain.modelo import (
    EstadoSobreviviente,
    EstadoZombie,
    FaseTurno,
    IntencionMovimiento,
    TipoZombie,
)
from navira.routing.dijkstra import PerfilCostos, seleccionar_refugio
from navira.routing.prediccion import (
    SobrevivienteObservable,
    ZombieObservable,
    pronosticar_zombies_visibles,
)
from navira.routing.temporal import CondicionTurno, buscar_ruta_temporal
from navira.simulation.coordinador import (
    SnapshotMundo,
    abrir_siguiente_turno,
    preparar_turno_versionado,
    resolver_turno_versionado,
)

MAPA_MANTA_EVALUACION = Path(__file__).resolve().parents[2] / "data/maps/manta-hackathon-v1.json"


def comparar_politicas(
    *,
    ruta_mapa: str | Path = MAPA_MANTA_EVALUACION,
    semillas: Iterable[int] = (101, 202, 303),
    escenarios: Iterable[str] = ("caminantes", "mixto", "horda"),
    poblaciones: Iterable[int] = (20, 80, 200),
    turnos: int = 3,
    horizonte: int = 6,
) -> dict[str, object]:
    """Ejecuta cada política desde mundos nuevos con pares semilla/perfil iguales.

    El RNG privado solo avanza dentro del coordinador del mundo. Las funciones
    de recomendación reciben únicamente proyecciones públicas del snapshot.
    Esta es una comparación local de fixtures, no una evaluación oficial.
    """

    semillas, escenarios, poblaciones = tuple(semillas), tuple(escenarios), tuple(poblaciones)
    _validar_entrada(semillas, escenarios, poblaciones, turnos, horizonte)
    resultados: list[dict[str, object]] = []
    for escenario in escenarios:
        for semilla in semillas:
            for poblacion in poblaciones:
                base = _ejecutar_corrida(
                    "dijkstra", ruta_mapa, escenario, semilla, poblacion, turnos, horizonte
                )
                temporal = _ejecutar_corrida(
                    "temporal", ruta_mapa, escenario, semilla, poblacion, turnos, horizonte
                )
                resultados.append(
                    {
                        "escenario": escenario,
                        "semilla": semilla,
                        "poblacion": poblacion,
                        "turnosSolicitados": turnos,
                        "dijkstra": base,
                        "temporal": temporal,
                        "deltaEvacuados": temporal["evacuados"] - base["evacuados"],
                        "deltaMordidos": temporal["mordidos"] - base["mordidos"],
                        "deltaActivos": temporal["activos"] - base["activos"],
                    }
                )
    deltas_evac = [int(item["deltaEvacuados"]) for item in resultados]
    deltas_mordidos = [int(item["deltaMordidos"]) for item in resultados]
    return {
        "mapa": str(ruta_mapa),
        "semillas": semillas,
        "escenarios": escenarios,
        "poblaciones": poblaciones,
        "horizonte": horizonte,
        "turnos": turnos,
        "comparaciones": resultados,
        "resumen": {
            "pares": len(resultados),
            "paresTemporalMejorEvacuados": sum(valor > 0 for valor in deltas_evac),
            "paresTemporalIgualEvacuados": sum(valor == 0 for valor in deltas_evac),
            "paresTemporalPeorEvacuados": sum(valor < 0 for valor in deltas_evac),
            "sumaDeltaEvacuados": sum(deltas_evac),
            "sumaDeltaMordidos": sum(deltas_mordidos),
        },
    }


def _ejecutar_corrida(
    politica: str,
    ruta_mapa: str | Path,
    escenario: str,
    semilla: int,
    poblacion: int,
    turnos: int,
    horizonte: int,
) -> dict[str, object]:
    contexto = crear_contexto_demo(
        ruta_mapa, semilla=semilla, escenario=escenario, cantidad_sobrevivientes=poblacion
    )
    snapshot = contexto.snapshots.obtener(contexto.run_id)
    if snapshot is None:
        raise RuntimeError("No existe snapshot inicial para la evaluación de rutas.")
    llamadas_ms: list[float] = []
    preparacion_pronostico_ms: list[float] = []
    fallback = 0
    turnos_ejecutados = 0

    for _ in range(turnos):
        if snapshot.partida.fase is FaseTurno.RESUELTA:
            if not any(item.estado is EstadoSobreviviente.ACTIVO for item in snapshot.partida.sobrevivientes):
                break
            snapshot = abrir_siguiente_turno(snapshot, version_esperada=snapshot.version)
            snapshot, _ = preparar_turno_versionado(
                snapshot, contexto.grafo, version_esperada=snapshot.version
            )
        if snapshot.partida.fase is not FaseTurno.DECISIONES:
            raise RuntimeError("La evaluación esperaba un snapshot abierto a decisiones.")

        ruta_base_por_id, tiempos_base = _rutas_dijkstra(snapshot, contexto.grafo)
        if politica == "dijkstra":
            llamadas_ms.extend(tiempos_base.values())
        pronostico = ()
        peligros_actuales = None
        if politica == "temporal":
            inicio_pronostico = perf_counter()
            pronostico, peligros_actuales = _crear_pronostico(snapshot, contexto.grafo, horizonte)
            preparacion_pronostico_ms.append((perf_counter() - inicio_pronostico) * 1000)

        intenciones: list[IntencionMovimiento] = []
        for sobreviviente in snapshot.partida.sobrevivientes:
            if sobreviviente.estado is not EstadoSobreviviente.ACTIVO:
                continue
            ruta_base = ruta_base_por_id[sobreviviente.id]
            destino = ruta_base.siguiente_nodo if ruta_base is not None else sobreviviente.nodo
            if politica == "temporal":
                inicio_busqueda = perf_counter()
                refugios = (
                    frozenset({sobreviviente.refugio_objetivo})
                    if sobreviviente.refugio_objetivo is not None
                    else frozenset(refugio.id for refugio in contexto.grafo.mapa.refugios)
                )
                temporal = buscar_ruta_temporal(
                    contexto.grafo,
                    sobreviviente.nodo,
                    refugios,
                    peligros_actuales=peligros_actuales,
                    pronostico=pronostico,
                    horizonte_turnos=horizonte,
                    perfil=PerfilCostos(),
                )
                llamadas_ms.append((perf_counter() - inicio_busqueda) * 1000)
                if temporal.estado == "ruta_encontrada" and temporal.trayecto:
                    destino = temporal.trayecto[1] if len(temporal.trayecto) > 1 else sobreviviente.nodo
                else:
                    fallback += 1

            intenciones.append(
                IntencionMovimiento(
                    run_id=snapshot.partida.run_id,
                    turno=snapshot.partida.turno,
                    fase=snapshot.partida.fase,
                    sobreviviente_id=sobreviviente.id,
                    destino=destino,
                )
            )

        snapshot, _ = resolver_turno_versionado(
            snapshot,
            contexto.grafo,
            version_esperada=snapshot.version,
            intenciones=tuple(intenciones),
        )
        turnos_ejecutados += 1

    sobrevivientes = snapshot.partida.sobrevivientes
    latencia_p95 = _percentil_nearest_rank(llamadas_ms, 0.95)
    forecast_p95 = _percentil_nearest_rank(preparacion_pronostico_ms, 0.95)
    return {
        "turnosEjecutados": turnos_ejecutados,
        "evacuados": sum(item.estado is EstadoSobreviviente.EVACUADO for item in sobrevivientes),
        "mordidos": sum(item.estado is EstadoSobreviviente.MORDIDO for item in sobrevivientes),
        "activos": sum(item.estado is EstadoSobreviviente.ACTIVO for item in sobrevivientes),
        "recomendacionesEvaluadas": len(llamadas_ms),
        "fallbackDijkstra": fallback,
        "p95TiempoPorRecomendacionMs": latencia_p95,
        "p95PreparacionPronosticoMs": forecast_p95,
    }


def _rutas_dijkstra(snapshot: SnapshotMundo, grafo):
    nodos_bloqueados, aristas_cruzadas = peligros_visibles(snapshot, grafo)
    aristas_cerradas = snapshot.aristas_cerradas | aristas_cruzadas
    rutas = {}
    tiempos: dict[str, float] = {}
    for sobreviviente in snapshot.partida.sobrevivientes:
        if sobreviviente.estado is not EstadoSobreviviente.ACTIVO:
            continue
        inicio = perf_counter()
        rutas[sobreviviente.id] = seleccionar_refugio(
            grafo,
            sobreviviente.nodo,
            refugio_objetivo=sobreviviente.refugio_objetivo,
            aristas_cerradas=aristas_cerradas,
            segmentos_cerrados=snapshot.segmentos_cerrados,
            nodos_bloqueados=frozenset(nodos_bloqueados),
        )
        tiempos[sobreviviente.id] = (perf_counter() - inicio) * 1000
    return rutas, tiempos


def _crear_pronostico(snapshot: SnapshotMundo, grafo, horizonte: int):
    nodos_bloqueados, aristas_cruzadas = peligros_visibles(snapshot, grafo)
    aristas_cerradas = snapshot.aristas_cerradas | aristas_cruzadas
    actual = CondicionTurno(
        nodos_bloqueados=frozenset(nodos_bloqueados),
        aristas_cerradas=aristas_cerradas,
        segmentos_cerrados=snapshot.segmentos_cerrados,
    )
    zombies = tuple(
        ZombieObservable(zombie.id, zombie.tipo, zombie.nodo)
        for zombie in snapshot.partida.zombies
        if zombie.estado is EstadoZombie.ACTIVO and zombie.tipo is not TipoZombie.DORMIDO
    )
    sobrevivientes = tuple(
        SobrevivienteObservable(item.id, item.nodo)
        for item in snapshot.partida.sobrevivientes
        if item.estado is EstadoSobreviviente.ACTIVO
    )
    resultado = pronosticar_zombies_visibles(
        grafo,
        zombies,
        sobrevivientes,
        turno_actual=snapshot.partida.turno,
        horizonte_turnos=horizonte,
        aristas_cerradas=aristas_cerradas,
        segmentos_cerrados=snapshot.segmentos_cerrados,
    )
    return resultado.turnos, actual


def _percentil_nearest_rank(valores: list[float], fraccion: float) -> float | None:
    if not valores:
        return None
    ordenados = sorted(valores)
    posicion = max(0, math.ceil(len(ordenados) * fraccion) - 1)
    return round(ordenados[posicion], 6)


def _validar_entrada(
    semillas: tuple[int, ...],
    escenarios: tuple[str, ...],
    poblaciones: tuple[int, ...],
    turnos: int,
    horizonte: int,
) -> None:
    if not semillas or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in semillas):
        raise ValueError("Se requiere al menos una semilla entera.")
    if not escenarios or set(escenarios) - set(ESCENARIOS_DEMO):
        raise ValueError("Los escenarios deben pertenecer a los perfiles sintéticos disponibles.")
    if not poblaciones or any(isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 200 for n in poblaciones):
        raise ValueError("Cada población debe ser un entero entre 1 y 200.")
    if isinstance(turnos, bool) or not isinstance(turnos, int) or not 1 <= turnos <= 150:
        raise ValueError("Los turnos deben estar entre 1 y 150.")
    if isinstance(horizonte, bool) or not isinstance(horizonte, int) or not 1 <= horizonte <= 12:
        raise ValueError("El horizonte debe estar entre 1 y 12.")


def _entero(valor: str) -> int:
    try:
        return int(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser un entero") from exc


def _positivo(valor: str) -> int:
    parsed = _entero(valor)
    if parsed < 1:
        raise argparse.ArgumentTypeError("debe ser positivo")
    return parsed


def main(argv: list[str] | None = None, *, salida: TextIO | None = None) -> int:
    """CLI de comparación reproducible para P3-03."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapa", type=Path, default=MAPA_MANTA_EVALUACION)
    parser.add_argument("--semillas", type=_entero, nargs="+", default=(101, 202, 303))
    parser.add_argument(
        "--escenarios", choices=sorted(ESCENARIOS_DEMO), nargs="+",
        default=("caminantes", "mixto", "horda"),
    )
    parser.add_argument("--poblaciones", type=_positivo, nargs="+", default=(20, 80, 200))
    parser.add_argument("--turnos", type=_positivo, default=3)
    parser.add_argument("--horizonte", type=_positivo, default=6)
    args = parser.parse_args(argv)
    try:
        resultado = comparar_politicas(
            ruta_mapa=args.mapa,
            semillas=args.semillas,
            escenarios=args.escenarios,
            poblaciones=args.poblaciones,
            turnos=args.turnos,
            horizonte=args.horizonte,
        )
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        parser.error(str(error))
    (salida or sys.stdout).write(json.dumps(resultado, ensure_ascii=False, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
