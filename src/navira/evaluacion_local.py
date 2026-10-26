"""Evaluación exploratoria de `/paso` con turnos que avanzan en Manta.

El servidor Uvicorn y el cliente HTTP corren en la misma máquina. Esta medición
incluye red loopback y el camino ASGI, pero no latencia remota, reloj real ni
condiciones oficiales de evaluación.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import secrets
import socket
import statistics
import sys
import threading
import time
from typing import Iterator, TextIO

import uvicorn

from navira.carga_http import SolicitudCarga, enviar_solicitud_http
from navira.demo import ESCENARIOS_DEMO, crear_contexto_demo
from navira.domain.modelo import (
    EstadoSobreviviente,
    FaseTurno,
    IntencionMovimiento,
)
from navira.application.decidir_paso import SolicitudPaso
from navira.application.snapshots import (
    abrir_siguiente_turno_persistido,
    preparar_turno_persistido,
    resolver_turno_persistido,
)
from navira.main import crear_app


MAPA_MANTA_POR_DEFECTO = (
    Path(__file__).resolve().parents[2] / "data/maps/manta-hackathon-v1.json"
)
POBLACIONES_EVALUACION = (20, 80, 200)
_CLAVE_LOCAL = "NAVIRA_API_KEY"


@contextmanager
def _clave_temporal(clave: str) -> Iterator[None]:
    """Configura una credencial efímera para el servidor de esta evaluación."""

    anterior = os.environ.get(_CLAVE_LOCAL)
    os.environ[_CLAVE_LOCAL] = clave
    try:
        yield
    finally:
        if anterior is None:
            os.environ.pop(_CLAVE_LOCAL, None)
        else:
            os.environ[_CLAVE_LOCAL] = anterior


@contextmanager
def _servidor_loopback(aplicacion, *, timeout_inicio: float = 10.0) -> Iterator[str]:
    """Sirve una app en un puerto efímero accesible solo desde la máquina local."""

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(socket.SOMAXCONN)
    puerto = listener.getsockname()[1]
    servidor = uvicorn.Server(
        uvicorn.Config(
            aplicacion,
            host="127.0.0.1",
            port=puerto,
            log_level="critical",
            access_log=False,
            lifespan="off",
        )
    )
    hilo = threading.Thread(
        target=servidor.run,
        kwargs={"sockets": [listener]},
        name="navira-evaluacion-http",
        daemon=True,
    )
    hilo.start()
    limite = time.monotonic() + timeout_inicio
    try:
        while not servidor.started and hilo.is_alive() and time.monotonic() < limite:
            time.sleep(0.01)
        if not servidor.started:
            raise RuntimeError("Uvicorn no inició el servidor de evaluación local.")
        yield f"http://127.0.0.1:{puerto}/paso"
    finally:
        servidor.should_exit = True
        hilo.join(timeout=timeout_inicio)
        if hilo.is_alive():
            servidor.force_exit = True
            hilo.join(timeout=1.0)
        listener.close()


def _validar_parametros(
    *, turnos: int, concurrencia: int, timeout_segundos: float
) -> None:
    if isinstance(turnos, bool) or not isinstance(turnos, int) or not 1 <= turnos <= 150:
        raise ValueError("Los turnos deben ser un entero entre 1 y 150.")
    if (
        isinstance(concurrencia, bool)
        or not isinstance(concurrencia, int)
        or not 1 <= concurrencia <= 200
    ):
        raise ValueError("La concurrencia debe ser un entero entre 1 y 200.")
    if not math.isfinite(timeout_segundos) or timeout_segundos <= 0:
        raise ValueError("El timeout debe ser un número finito mayor que cero.")


def _resumir_latencias(latencias: list[float]) -> dict[str, float | None]:
    if not latencias:
        return {"p50": None, "p95": None, "p99": None, "max": None}
    ordenadas = sorted(latencias)

    def percentil(cuantil: float) -> float:
        indice = max(0, math.ceil(cuantil * len(ordenadas)) - 1)
        return round(ordenadas[indice], 3)

    return {
        "p50": round(statistics.median(ordenadas), 3),
        "p95": percentil(0.95),
        "p99": percentil(0.99),
        "max": round(ordenadas[-1], 3),
    }


def ejecutar_evaluacion_local(
    *,
    sobrevivientes: int,
    turnos: int = 5,
    semilla: int | None = 20261026,
    escenario: str = "mixto",
    concurrencia: int = 200,
    timeout_segundos: float = 1.0,
    mapa: str | Path = MAPA_MANTA_POR_DEFECTO,
) -> dict[str, object]:
    """Consulta `/paso` por sobreviviente en cada turno y resuelve esas órdenes.

    Las peticiones de un turno comparten el snapshot inmutable. Solo después de
    completar la ráfaga se confirman las intenciones en una transición CAS; una
    respuesta fallida se convierte en espera local para poder medir y avanzar
    el resto de la ronda sin inventar un movimiento.
    """

    _validar_parametros(
        turnos=turnos,
        concurrencia=concurrencia,
        timeout_segundos=timeout_segundos,
    )
    if sobrevivientes not in POBLACIONES_EVALUACION:
        raise ValueError("La cohorte debe ser 20, 80 o 200 sobrevivientes.")
    if escenario not in ESCENARIOS_DEMO:
        raise ValueError(f"Escenario desconocido: {escenario}.")

    contexto = crear_contexto_demo(
        mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=sobrevivientes,
    )
    mapa_version = contexto.grafo.mapa.version
    aplicacion = crear_app(contexto.servicio_decision)
    clave = secrets.token_urlsafe(32)
    latencias: list[float] = []
    estados_http: Counter[str] = Counter()
    fallidas = 0
    turnos_reporte: list[dict[str, object]] = []
    inicio_evaluacion = time.perf_counter()

    with _clave_temporal(clave), _servidor_loopback(aplicacion) as url:
        for _ in range(turnos):
            snapshot = contexto.snapshots.obtener(contexto.run_id)
            if snapshot is None:
                raise RuntimeError("El snapshot desapareció durante la evaluación.")
            if snapshot.partida.fase is FaseTurno.RESUELTA:
                snapshot = abrir_siguiente_turno_persistido(
                    contexto.snapshots,
                    contexto.run_id,
                    version_esperada=snapshot.version,
                )
            if snapshot.partida.fase is FaseTurno.PREPARACION:
                snapshot = preparar_turno_persistido(
                    contexto.snapshots,
                    contexto.grafo,
                    contexto.run_id,
                    version_esperada=snapshot.version,
                )
            if snapshot.partida.fase is not FaseTurno.DECISIONES:
                raise RuntimeError("La evaluación requiere una fase de decisiones abierta.")

            partida = snapshot.partida
            activos = tuple(
                persona
                for persona in partida.sobrevivientes
                if persona.estado is EstadoSobreviviente.ACTIVO
            )
            if not activos:
                break

            solicitudes: list[SolicitudCarga] = []
            for persona in activos:
                decision = contexto.servicio_decision.ejecutar(
                    SolicitudPaso(persona.id, persona.nodo, partida.turno)
                )
                cuerpo = {
                    "sobrevivienteId": persona.id,
                    "nodoActual": persona.nodo,
                    "turno": partida.turno,
                }
                solicitudes.append(
                    SolicitudCarga(
                        json.dumps(cuerpo, separators=(",", ":")).encode("utf-8"),
                        decision.siguiente_nodo,
                    )
                )

            concurrencia_turno = min(concurrencia, len(solicitudes))
            with ThreadPoolExecutor(max_workers=concurrencia_turno) as pool:
                resultados = tuple(
                    pool.map(
                        lambda solicitud: enviar_solicitud_http(
                            url, clave, solicitud, timeout_segundos
                        ),
                        solicitudes,
                    )
                )

            intenciones: list[IntencionMovimiento] = []
            estados_turno: Counter[str] = Counter()
            latencias_turno: list[float] = []
            fallidas_turno = 0
            for persona, resultado in zip(activos, resultados, strict=True):
                latencias_turno.append(resultado.latencia_ms)
                latencias.append(resultado.latencia_ms)
                estado = (
                    str(resultado.estado_http)
                    if resultado.estado_http is not None
                    else "sin_respuesta"
                )
                estados_turno[estado] += 1
                estados_http[estado] += 1
                if resultado.correcta and resultado.destino_recibido is not None:
                    destino = resultado.destino_recibido
                else:
                    fallidas_turno += 1
                    destino = persona.nodo
                intenciones.append(
                    IntencionMovimiento(
                        run_id=partida.run_id,
                        turno=partida.turno,
                        fase=FaseTurno.DECISIONES,
                        sobreviviente_id=persona.id,
                        destino=destino,
                    )
                )
            fallidas += fallidas_turno

            resuelto, resultado_turno = resolver_turno_persistido(
                contexto.snapshots,
                contexto.grafo,
                contexto.run_id,
                version_esperada=snapshot.version,
                intenciones=tuple(intenciones),
            )
            final = resuelto.partida
            turnos_reporte.append(
                {
                    "turno": partida.turno,
                    "versionInicial": snapshot.version,
                    "versionResuelta": resuelto.version,
                    "sobrevivientesConsultados": len(activos),
                    "solicitudes": len(resultados),
                    "fallidas": fallidas_turno,
                    "estadosHttp": dict(sorted(estados_turno.items())),
                    "latenciaMs": _resumir_latencias(latencias_turno),
                    "movimientosSobrevivientes": len(
                        resultado_turno.movimientos_sobrevivientes
                    ),
                    "movimientosZombies": len(resultado_turno.movimientos_zombies),
                    "evacuadosEnTurno": len(resultado_turno.evacuados),
                    "mordidosEnTurno": len(resultado_turno.mordidos),
                    "activosAlCerrarTurno": sum(
                        persona.estado is EstadoSobreviviente.ACTIVO
                        for persona in final.sobrevivientes
                    ),
                    "estadoPartida": final.estado.value,
                }
            )
            if final.estado.value == "finalizada":
                break

    snapshot_final = contexto.snapshots.obtener(contexto.run_id)
    if snapshot_final is None:
        raise RuntimeError("No se pudo leer el estado final de la evaluación.")
    personas_finales = snapshot_final.partida.sobrevivientes
    total_solicitudes = len(latencias)
    activos_finales = sum(
        persona.estado is EstadoSobreviviente.ACTIVO for persona in personas_finales
    )
    evacuados = sum(
        persona.estado is EstadoSobreviviente.EVACUADO for persona in personas_finales
    )
    mordidos = sum(
        persona.estado is EstadoSobreviviente.MORDIDO for persona in personas_finales
    )
    latencia_resumen = _resumir_latencias(latencias)
    return {
        "medicion": "exploratoria_local_http_loopback",
        "mapaVersion": mapa_version,
        "escenario": escenario,
        "semilla": contexto.semilla,
        "sobrevivientesIniciales": sobrevivientes,
        "turnosSolicitados": turnos,
        "turnosEjecutados": len(turnos_reporte),
        "concurrenciaMaxima": concurrencia,
        "timeoutSegundos": timeout_segundos,
        "solicitudes": total_solicitudes,
        "fallidas": fallidas,
        "tasaFallo": round(fallidas / total_solicitudes, 6)
        if total_solicitudes
        else 0.0,
        "estadosHttp": dict(sorted(estados_http.items())),
        "latenciaMs": latencia_resumen,
        "menorA500ms": all(latencia < 500 for latencia in latencias),
        "sobrevivientesActivosFinales": activos_finales,
        "evacuadosTotales": evacuados,
        "mordidosTotales": mordidos,
        "duracionTotalSegundos": round(time.perf_counter() - inicio_evaluacion, 3),
        "temporizacion": "avance inmediato entre turnos; no simula el reloj de 2 segundos",
        "turnos": turnos_reporte,
        "limites": [
            "servidor y cliente comparten máquina; no mide latencia de AWS ni internet",
            "perfil sintético, no representa dificultad ni distribución oficial",
            "no acredita cobertura cartográfica ni seguridad ante tsunami o terremoto",
            "las fallas HTTP producen espera local para permitir continuar la evaluación",
        ],
    }


def ejecutar_matriz_local(
    *,
    poblaciones: tuple[int, ...] = POBLACIONES_EVALUACION,
    turnos: int = 5,
    semilla: int | None = 20261026,
    escenario: str = "mixto",
    concurrencia: int = 200,
    timeout_segundos: float = 1.0,
    mapa: str | Path = MAPA_MANTA_POR_DEFECTO,
) -> dict[str, object]:
    """Ejecuta cada población solicitada como una partida aislada reproducible."""

    if not poblaciones or len(set(poblaciones)) != len(poblaciones):
        raise ValueError("Indica una o más poblaciones sin duplicados.")
    resultados = tuple(
        ejecutar_evaluacion_local(
            sobrevivientes=poblacion,
            turnos=turnos,
            semilla=semilla,
            escenario=escenario,
            concurrencia=concurrencia,
            timeout_segundos=timeout_segundos,
            mapa=mapa,
        )
        for poblacion in poblaciones
    )
    return {
        "schemaVersion": 1,
        "medicion": "exploratoria_local_http_loopback",
        "poblaciones": list(poblaciones),
        "turnosPorPartida": turnos,
        "semillaSolicitada": semilla,
        "escenario": escenario,
        "concurrenciaMaxima": concurrencia,
        "resultados": resultados,
        "limite": "no sustituye T-11 ni las rondas oficiales en su entorno de evaluación",
    }


def _positivo(valor: str) -> int:
    try:
        numero = int(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser un entero") from exc
    if numero < 1:
        raise argparse.ArgumentTypeError("debe ser mayor que cero")
    return numero


def _poblacion(valor: str) -> int:
    numero = _positivo(valor)
    if numero not in POBLACIONES_EVALUACION:
        raise argparse.ArgumentTypeError("debe ser 20, 80 o 200")
    return numero


def _timeout(valor: str) -> float:
    try:
        numero = float(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser numérico") from exc
    if not math.isfinite(numero) or numero <= 0:
        raise argparse.ArgumentTypeError("debe ser finito y mayor que cero")
    return numero


def main(argv: list[str] | None = None, *, salida: TextIO | None = None) -> int:
    """Punto de entrada: `python -m navira.evaluacion_local`."""

    parser = argparse.ArgumentParser(
        description="Mide /paso por HTTP loopback mientras avanza el simulador local."
    )
    parser.add_argument("--turnos", type=_positivo, default=5)
    parser.add_argument("--semilla", type=int, default=20261026)
    parser.add_argument("--escenario", choices=sorted(ESCENARIOS_DEMO), default="mixto")
    parser.add_argument(
        "--poblaciones",
        type=_poblacion,
        nargs="+",
        default=POBLACIONES_EVALUACION,
        help="cohortes aisladas; por defecto ejecuta 20, 80 y 200",
    )
    parser.add_argument("--concurrencia", type=_positivo, default=200)
    parser.add_argument("--timeout-segundos", type=_timeout, default=1.0)
    parser.add_argument("--mapa", type=Path, default=MAPA_MANTA_POR_DEFECTO)
    args = parser.parse_args(argv)
    destino = salida if salida is not None else sys.stdout
    try:
        reporte = ejecutar_matriz_local(
            poblaciones=tuple(args.poblaciones),
            turnos=args.turnos,
            semilla=args.semilla,
            escenario=args.escenario,
            concurrencia=args.concurrencia,
            timeout_segundos=args.timeout_segundos,
            mapa=args.mapa,
        )
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(reporte, ensure_ascii=False, sort_keys=True), file=destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
