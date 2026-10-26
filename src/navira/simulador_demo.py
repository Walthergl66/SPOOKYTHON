"""CLI local para ejecutar rondas automáticas del escenario sintético."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TextIO
import sys

from navira.application.simulacion_automatica import EjecutarRondaAutomatica
from navira.demo import ESCENARIOS_DEMO, MAPA_DEMO_POR_DEFECTO, crear_contexto_demo
from navira.domain.modelo import EstadoSobreviviente, EstadoZombie


def ejecutar_demo(
    *,
    turnos: int = 10,
    semilla: int = 31,
    escenario: str = "libre",
    cantidad_sobrevivientes: int = 1,
    ruta_mapa: str | Path = MAPA_DEMO_POR_DEFECTO,
) -> tuple[dict[str, object], ...]:
    """Ejecuta hasta N rondas, deteniéndose cuando no queden activos."""

    if isinstance(turnos, bool) or not isinstance(turnos, int) or turnos < 1:
        raise ValueError("El número de turnos debe ser un entero positivo.")
    if isinstance(semilla, bool) or not isinstance(semilla, int):
        raise ValueError("La semilla debe ser un entero.")

    contexto = crear_contexto_demo(
        ruta_mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=cantidad_sobrevivientes,
    )
    rondas = EjecutarRondaAutomatica(contexto.snapshots, contexto.mapas)
    reportes: list[dict[str, object]] = []

    for _ in range(turnos):
        snapshot = contexto.snapshots.obtener(contexto.run_id)
        if snapshot is None:
            raise RuntimeError("El snapshot de la demo desapareció durante la ejecución.")
        resultado = rondas.ejecutar(
            contexto.run_id,
            version_esperada=snapshot.version,
        )
        partida = resultado.partida
        activos = sum(
            sobreviviente.estado is EstadoSobreviviente.ACTIVO
            for sobreviviente in partida.sobrevivientes
        )
        zombies_visibles = {
            zombie.id for zombie in partida.zombies if zombie.estado is EstadoZombie.ACTIVO
        }
        reportes.append(
            {
                "turno": partida.turno,
                "versionMapa": partida.map_version,
                "escenario": partida.escenario,
                "sobrevivientesIniciales": cantidad_sobrevivientes,
                "movimientosSobrevivientes": [
                    {
                        "id": movimiento.sobreviviente_id,
                        "desde": movimiento.origen,
                        "hasta": movimiento.destino,
                    }
                    for movimiento in resultado.movimientos_sobrevivientes
                ],
                "movimientosZombies": [
                    {
                        "id": movimiento.zombie_id,
                        "desde": movimiento.origen,
                        "hasta": movimiento.destino,
                    }
                    for movimiento in resultado.movimientos_zombies
                    if movimiento.zombie_id in zombies_visibles
                ],
                "mordidos": list(resultado.mordidos),
                "evacuados": list(resultado.evacuados),
                "sobrevivientesActivos": activos,
                "estadoPartida": partida.estado.value,
                "semilla": semilla,
            }
        )
        if activos == 0:
            break

    return tuple(reportes)


def _entero_positivo(valor: str) -> int:
    try:
        numero = int(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser un entero") from exc
    if numero < 1:
        raise argparse.ArgumentTypeError("debe ser mayor que cero")
    return numero


def _entero(valor: str) -> int:
    try:
        return int(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser un entero") from exc


def main(argv: list[str] | None = None, *, salida: TextIO | None = None) -> int:
    """Punto de entrada de `python -m navira.simulador_demo`."""

    parser = argparse.ArgumentParser(
        description="Ejecuta rondas automáticas en el mapa sintético de Navira."
    )
    parser.add_argument("--turnos", type=_entero_positivo, default=10)
    parser.add_argument("--semilla", type=_entero, default=31)
    parser.add_argument("--escenario", choices=sorted(ESCENARIOS_DEMO), default="libre")
    parser.add_argument("--sobrevivientes", type=_entero_positivo, default=1)
    parser.add_argument("--mapa", type=Path, default=MAPA_DEMO_POR_DEFECTO)
    args = parser.parse_args(argv)
    destino = salida if salida is not None else sys.stdout
    try:
        reportes = ejecutar_demo(
            turnos=args.turnos,
            semilla=args.semilla,
            escenario=args.escenario,
            cantidad_sobrevivientes=args.sobrevivientes,
            ruta_mapa=args.mapa,
        )
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        parser.error(str(exc))
    for reporte in reportes:
        print(json.dumps(reporte, ensure_ascii=False, sort_keys=True), file=destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
