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
from pathlib import Path
import secrets
import socket
import statistics
import sys
import threading
import time
from typing import Callable, Iterator, TextIO

import uvicorn

from navira.api.seguridad import ConfiguracionSeguridad
from navira.carga_http import SolicitudCarga, enviar_solicitud_http
from navira.demo import ESCENARIOS_DEMO, crear_contexto_demo
from navira.domain.modelo import (
    EstadoPartida,
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
    *, turnos: int, concurrencia: int, timeout_segundos: float, periodo_segundos: float
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
    if not math.isfinite(periodo_segundos) or periodo_segundos <= 0:
        raise ValueError("El período debe ser un número finito mayor que cero.")


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
    periodo_segundos: float = 2.0,
    mapa: str | Path = MAPA_MANTA_POR_DEFECTO,
    ronda_reto: int | None = None,
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
        periodo_segundos=periodo_segundos,
    )
    if sobrevivientes not in POBLACIONES_EVALUACION:
        raise ValueError("La cohorte debe ser 20, 80 o 200 sobrevivientes.")
    if escenario not in ESCENARIOS_DEMO:
        raise ValueError(f"Escenario desconocido: {escenario}.")
    if ronda_reto is not None and (
        isinstance(ronda_reto, bool) or ronda_reto not in (1, 2, 3)
    ):
        raise ValueError("La ronda del reto debe ser 1, 2 o 3.")

    contexto = crear_contexto_demo(
        mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=sobrevivientes,
        ronda_reto=ronda_reto,
    )
    mapa_version = contexto.grafo.mapa.version
    snapshot_inicial = contexto.snapshots.obtener(contexto.run_id)
    if snapshot_inicial is None:
        raise RuntimeError("El snapshot inicial no está disponible para evaluación.")
    eventos_programados = [
        {
            "id": evento.id,
            "turnoObjetivo": evento.turno_objetivo,
            "segmentos": sorted(evento.segmentos),
            "causa": evento.causa,
        }
        for evento in snapshot_inicial.eventos_programados
    ]
    clave = secrets.token_urlsafe(32)
    aplicacion = crear_app(contexto.servicio_decision, seguridad=ConfiguracionSeguridad(api_key=clave))
    latencias: list[float] = []
    estados_http: Counter[str] = Counter()
    fallidas = 0
    turnos_reporte: list[dict[str, object]] = []
    slots_sin_actividad: list[dict[str, object]] = []
    inicio_evaluacion = 0.0
    inicios_turno: list[float] = []
    retrasos_inicio_ms: list[float] = []
    turnos_fuera_de_periodo = 0

    with _servidor_loopback(aplicacion) as url:
        inicio_evaluacion = time.perf_counter()
        for indice_turno in range(turnos):
            inicio_objetivo = inicio_evaluacion + indice_turno * periodo_segundos
            espera = inicio_objetivo - time.perf_counter()
            if espera > 0:
                time.sleep(espera)
            inicio_turno = time.perf_counter()
            retraso_inicio_ms = max(0.0, (inicio_turno - inicio_objetivo) * 1000)
            inicios_turno.append(inicio_turno)
            retrasos_inicio_ms.append(retraso_inicio_ms)
            snapshot = contexto.snapshots.obtener(contexto.run_id)
            if snapshot is None:
                raise RuntimeError("El snapshot desapareció durante la evaluación.")
            # La ventana oficial mide cinco minutos aunque la partida pueda
            # terminar antes. Conservamos esa duración sin seguir inventando
            # movimientos ni enviando solicitudes para personajes terminales.
            if snapshot.partida.estado is EstadoPartida.FINALIZADA:
                slots_sin_actividad.append(
                    {
                        "slotCadencia": indice_turno,
                        "turnoFinal": snapshot.partida.turno,
                        "motivo": "partida_finalizada",
                        "solicitudes": 0,
                    }
                )
                continue
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
                slots_sin_actividad.append(
                    {
                        "slotCadencia": indice_turno,
                        "turnoFinal": partida.turno,
                        "motivo": "sin_sobrevivientes_activos",
                        "solicitudes": 0,
                    }
                )
                continue

            solicitudes: list[SolicitudCarga] = []
            rutas_propuestas = {}
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
                compromiso = contexto.servicio_decision.proponer_compromiso_en_snapshot(
                    snapshot, persona.id, contexto.grafo
                )
                rutas_propuestas[persona.id] = compromiso

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
                rutas_propuestas=rutas_propuestas,
            )
            final = resuelto.partida
            duracion_turno_ms = (time.perf_counter() - inicio_turno) * 1000
            periodo_cumplido = duracion_turno_ms <= periodo_segundos * 1000
            turnos_reporte.append(
                {
                    "slotCadencia": indice_turno,
                    "turno": partida.turno,
                    "inicioDesdeInicioMs": round((inicio_turno - inicio_evaluacion) * 1000, 3),
                    "intervaloInicioAnteriorMs": round(
                        (inicio_turno - inicios_turno[-2]) * 1000, 3
                    ) if len(inicios_turno) > 1 else None,
                    "retrasoInicioMs": round(retraso_inicio_ms, 3),
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
                    "duracionTurnoMs": round(duracion_turno_ms, 3),
                    "periodoCumplido": periodo_cumplido,
                }
            )
            if not periodo_cumplido:
                turnos_fuera_de_periodo += 1

        # El slot final empieza en (N-1)*periodo; completar también el último
        # intervalo hace que N turnos cubran N períodos completos de reloj.
        objetivo_fin = inicio_evaluacion + turnos * periodo_segundos
        espera_final = objetivo_fin - time.perf_counter()
        if espera_final > 0:
            time.sleep(espera_final)

    snapshot_final = contexto.snapshots.obtener(contexto.run_id)
    if snapshot_final is None:
        raise RuntimeError("No se pudo leer el estado final de la evaluación.")
    personas_finales = snapshot_final.partida.sobrevivientes
    total_solicitudes = len(latencias)
    duracion_total = time.perf_counter() - inicio_evaluacion
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
        "escenario": snapshot_final.partida.escenario,
        "rondaReto": ronda_reto,
        "runId": contexto.run_id,
        "semilla": contexto.semilla,
        "eventosProgramados": eventos_programados,
        "eventosAplicados": list(snapshot_final.eventos_aplicados),
        "sobrevivientesIniciales": sobrevivientes,
        "turnosSolicitados": turnos,
        "turnosEjecutados": len(turnos_reporte),
        "slotsCadenciaSolicitados": turnos,
        "slotsCadenciaSinActividad": len(slots_sin_actividad),
        "slotsSinActividad": slots_sin_actividad,
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
        "periodoObjetivoSegundos": periodo_segundos,
        "duracionObjetivoSegundos": round(turnos * periodo_segundos, 3),
        "duracionTotalSegundos": round(duracion_total, 3),
        "duracionObjetivoCumplida": duracion_total >= turnos * periodo_segundos,
        "turnosFueraDePeriodo": turnos_fuera_de_periodo,
        "retrasoInicioMsMaximo": round(max(retrasos_inicio_ms, default=0.0), 3),
        "temporizacion": "inicio de turnos alineado a una cadencia monotónica configurable",
        "turnos": turnos_reporte,
        "limites": [
            "servidor y cliente comparten máquina; no mide latencia de AWS ni internet",
            "perfil sintético, no representa dificultad ni distribución oficial",
            "la temporización local no equivale al reloj continuo ni al entorno de evaluación desplegado",
            "no acredita cobertura cartográfica ni seguridad ante tsunami o terremoto",
            "las fallas HTTP producen espera local para permitir continuar la evaluación",
            "si la partida termina antes, se completa la ventana con slots ociosos; no se simulan turnos ni solicitudes después del fin",
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
    periodo_segundos: float = 2.0,
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
            periodo_segundos=periodo_segundos,
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
        "periodoObjetivoSegundos": periodo_segundos,
        "resultados": resultados,
        "limite": "no sustituye T-11 ni las rondas oficiales en su entorno de evaluación",
    }


def ejecutar_campana_reto_local(
    *,
    turnos: int = 150,
    semilla: int | None = 20261026,
    concurrencia: int = 200,
    timeout_segundos: float = 1.0,
    periodo_segundos: float = 2.0,
    mapa: str | Path = MAPA_MANTA_POR_DEFECTO,
    al_completar_ronda: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    """Ejecuta R1, R2 y R3 en orden, con una ventana independiente por ronda.

    Cada ronda crea un run nuevo con el preset Reto del servidor. La espera
    terminal completa el tiempo de evaluación sin inventar solicitudes ni
    movimientos. La semilla de cada ronda deriva de la semilla base para que
    una campaña se pueda reproducir sin reutilizar el mismo estado aleatorio.
    """

    inicio_campana = time.perf_counter()
    resultados: list[dict[str, object]] = []
    for ronda in (1, 2, 3):
        semilla_ronda = semilla + ronda - 1 if semilla is not None else None
        resultado = ejecutar_evaluacion_local(
            sobrevivientes={1: 20, 2: 80, 3: 200}[ronda],
            turnos=turnos,
            semilla=semilla_ronda,
            escenario="mixto",
            concurrencia=concurrencia,
            timeout_segundos=timeout_segundos,
            periodo_segundos=periodo_segundos,
            mapa=mapa,
            ronda_reto=ronda,
        )
        resultados.append(resultado)
        if al_completar_ronda is not None:
            al_completar_ronda(resultado)

    duracion_objetivo = turnos * periodo_segundos * len(resultados)
    duracion_total = time.perf_counter() - inicio_campana
    total_solicitudes = sum(int(item["solicitudes"]) for item in resultados)
    total_fallidas = sum(int(item["fallidas"]) for item in resultados)
    return {
        "schemaVersion": 1,
        "medicion": "campana_reto_local_http_loopback",
        "rondas": [item["rondaReto"] for item in resultados],
        "semillaBaseSolicitada": semilla,
        "turnosPorRonda": turnos,
        "periodoObjetivoSegundos": periodo_segundos,
        "duracionObjetivoSegundos": round(duracion_objetivo, 3),
        "duracionTotalSegundos": round(duracion_total, 3),
        "duracionObjetivoCumplida": all(
            bool(item["duracionObjetivoCumplida"]) for item in resultados
        ),
        "solicitudes": total_solicitudes,
        "fallidas": total_fallidas,
        "tasaFallo": round(total_fallidas / total_solicitudes, 6)
        if total_solicitudes
        else 0.0,
        "resultados": resultados,
        "limite": "mide HTTP loopback en esta máquina; no es una prueba AWS ni confirma criterios oficiales no especificados",
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


def _periodo(valor: str) -> float:
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
    parser.add_argument(
        "--turnos",
        type=_positivo,
        default=None,
        help="slots por ronda (5 en matriz libre; 150 en campaña Reto por defecto)",
    )
    parser.add_argument(
        "--campana-reto",
        action="store_true",
        help="ejecuta R1, R2 y R3 consecutivamente; por defecto 150 turnos de 2 s por ronda",
    )
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
    parser.add_argument(
        "--periodo-segundos",
        type=_periodo,
        default=2.0,
        help="cadencia objetivo entre inicios de turno (por defecto: 2 segundos)",
    )
    parser.add_argument("--mapa", type=Path, default=MAPA_MANTA_POR_DEFECTO)
    args = parser.parse_args(argv)
    destino = salida if salida is not None else sys.stdout
    try:
        if args.campana_reto:
            if tuple(args.poblaciones) != POBLACIONES_EVALUACION:
                parser.error("--campana-reto define por sí misma las poblaciones 20/80/200.")
            reporte = ejecutar_campana_reto_local(
                turnos=args.turnos if args.turnos is not None else 150,
                semilla=args.semilla,
                concurrencia=args.concurrencia,
                timeout_segundos=args.timeout_segundos,
                periodo_segundos=args.periodo_segundos,
                mapa=args.mapa,
                al_completar_ronda=lambda ronda: print(
                    json.dumps(
                        {
                            "progreso": "ronda_completada",
                            "rondaReto": ronda["rondaReto"],
                            "duracionSegundos": ronda["duracionTotalSegundos"],
                            "turnosEjecutados": ronda["turnosEjecutados"],
                            "slotsSinActividad": ronda["slotsCadenciaSinActividad"],
                            "solicitudes": ronda["solicitudes"],
                            "fallidas": ronda["fallidas"],
                        },
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                    flush=True,
                ),
            )
        else:
            reporte = ejecutar_matriz_local(
                poblaciones=tuple(args.poblaciones),
                turnos=args.turnos if args.turnos is not None else 5,
                semilla=args.semilla,
                escenario=args.escenario,
                concurrencia=args.concurrencia,
                timeout_segundos=args.timeout_segundos,
                periodo_segundos=args.periodo_segundos,
                mapa=args.mapa,
            )
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(reporte, ensure_ascii=False, sort_keys=True), file=destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
