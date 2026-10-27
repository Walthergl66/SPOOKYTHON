"""Cliente de carga local para medir ráfagas contra `POST /paso`."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Callable, TextIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from navira.application.decidir_paso import SolicitudPaso
from navira.demo import ESCENARIOS_DEMO, MAPA_DEMO_POR_DEFECTO, crear_contexto_demo
from navira.domain.modelo import EstadoSobreviviente


@dataclass(frozen=True, slots=True)
class SolicitudCarga:
    cuerpo: bytes
    destino_esperado: str


@dataclass(frozen=True, slots=True)
class ResultadoSolicitud:
    latencia_ms: float
    estado_http: int | None
    correcta: bool
    destino_recibido: str | None = None


def _preparar_solicitudes(
    *,
    escenario: str,
    semilla: int,
    sobrevivientes: int,
    mapa: str | Path,
) -> tuple[SolicitudCarga, ...]:
    contexto = crear_contexto_demo(
        mapa,
        semilla=semilla,
        escenario=escenario,
        cantidad_sobrevivientes=sobrevivientes,
    )
    snapshot = contexto.snapshots.obtener(contexto.run_id)
    if snapshot is None:
        raise RuntimeError("El snapshot inicial no está disponible para preparar la carga.")
    solicitudes: list[SolicitudCarga] = []
    for sobreviviente in snapshot.partida.sobrevivientes:
        if sobreviviente.estado is not EstadoSobreviviente.ACTIVO:
            continue
        decision = contexto.servicio_decision.ejecutar(
            # El turno y la posición se toman del mismo fixture que debe
            # haberse ensamblado en el proceso HTTP del servidor.
            SolicitudPaso(
                sobreviviente.id,
                sobreviviente.nodo,
                snapshot.partida.turno,
            )
        )
        cuerpo = {
            "sobrevivienteId": sobreviviente.id,
            "nodoActual": sobreviviente.nodo,
            "turno": snapshot.partida.turno,
        }
        solicitudes.append(
            SolicitudCarga(
                cuerpo=json.dumps(cuerpo, separators=(",", ":")).encode("utf-8"),
                destino_esperado=decision.siguiente_nodo,
            )
        )
    return tuple(solicitudes)


def enviar_solicitud_http(
    url: str, api_key: str, solicitud: SolicitudCarga, timeout: float
) -> ResultadoSolicitud:
    """Envía un paso autenticado y devuelve latencia, estado y destino recibido."""

    request = Request(
        url,
        data=solicitud.cuerpo,
        headers={"content-type": "application/json", "x-api-key": api_key},
        method="POST",
    )
    inicio = time.perf_counter()
    estado: int | None = None
    correcta = False
    destino_recibido: str | None = None
    try:
        with urlopen(request, timeout=timeout) as response:
            estado = response.status
            cuerpo = json.loads(response.read())
        if isinstance(cuerpo, dict):
            destino_recibido = cuerpo.get("siguienteNodo")
        correcta = (
            estado == 200
            and isinstance(cuerpo, dict)
            and set(cuerpo) == {"siguienteNodo"}
            and cuerpo["siguienteNodo"] == solicitud.destino_esperado
        )
    except HTTPError as error:
        estado = error.code
        error.read()
    except (URLError, TimeoutError, ValueError, OSError):
        pass
    return ResultadoSolicitud(
        (time.perf_counter() - inicio) * 1000,
        estado,
        correcta,
        destino_recibido,
    )


def ejecutar_carga(
    *,
    url: str,
    api_key: str,
    escenario: str = "libre",
    sobrevivientes: int = 20,
    semilla: int = 31,
    rondas: int = 1,
    concurrencia: int = 200,
    periodo_segundos: float = 2.0,
    timeout_segundos: float = 1.0,
    mapa: str | Path = MAPA_DEMO_POR_DEFECTO,
    enviar: Callable[[str, str, SolicitudCarga, float], ResultadoSolicitud] = enviar_solicitud_http,
) -> dict[str, object]:
    """Ejecuta ráfagas periódicas de decisiones repetidas sobre un snapshot.

    Cada réplica de una solicitud observa el mismo turno; esto mide el camino
    HTTP de decisión y no avanza el reloj ni resuelve una ronda.
    """

    if not api_key.strip():
        raise ValueError("Configura NAVIRA_API_KEY antes de iniciar el cliente de carga.")
    if not url.rstrip("/").endswith("/paso"):
        raise ValueError("La URL debe apuntar a la ruta /paso.")
    if isinstance(rondas, bool) or not isinstance(rondas, int) or rondas < 1:
        raise ValueError("El número de rondas debe ser un entero positivo.")
    if isinstance(concurrencia, bool) or not isinstance(concurrencia, int) or not 1 <= concurrencia <= 200:
        raise ValueError("La concurrencia debe ser un entero entre 1 y 200.")
    if (
        not math.isfinite(periodo_segundos)
        or not math.isfinite(timeout_segundos)
        or periodo_segundos <= 0
        or timeout_segundos <= 0
    ):
        raise ValueError("El período y el timeout deben ser mayores que cero.")

    solicitudes = _preparar_solicitudes(
        escenario=escenario,
        semilla=semilla,
        sobrevivientes=sobrevivientes,
        mapa=mapa,
    )
    if not solicitudes:
        raise ValueError("El escenario no dejó sobrevivientes activos para generar solicitudes.")
    if concurrencia > len(solicitudes):
        concurrencia = len(solicitudes)
    latencias: list[float] = []
    estados_http: dict[str, int] = {}
    fallidas = 0
    inicio = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrencia) as pool:
        for indice_ronda in range(rondas):
            inicio_objetivo = inicio + indice_ronda * periodo_segundos
            restante = inicio_objetivo - time.perf_counter()
            if restante > 0:
                time.sleep(restante)
            resultados = pool.map(
                lambda solicitud: enviar(url, api_key, solicitud, timeout_segundos),
                solicitudes,
            )
            for resultado in resultados:
                latencias.append(resultado.latencia_ms)
                clave_estado = str(resultado.estado_http) if resultado.estado_http is not None else "sin_respuesta"
                estados_http[clave_estado] = estados_http.get(clave_estado, 0) + 1
                if not resultado.correcta:
                    fallidas += 1

    latencias_ordenadas = sorted(latencias)
    total = len(latencias_ordenadas)

    def percentil(cuantil: float) -> float:
        indice = max(0, math.ceil(cuantil * total) - 1)
        return round(latencias_ordenadas[indice], 3)

    duracion = time.perf_counter() - inicio
    return {
        "url": url,
        "escenario": escenario,
        "semilla": semilla,
        "sobrevivientes": sobrevivientes,
        "sobrevivientesActivosEnSnapshot": len(solicitudes),
        "rondas": rondas,
        "solicitudes": total,
        "concurrenciaMaxima": concurrencia,
        "periodoSegundos": periodo_segundos,
        "timeoutSegundos": timeout_segundos,
        "estadosHttp": estados_http,
        "fallidas": fallidas,
        "latenciaMs": {
            "p50": round(statistics.median(latencias_ordenadas), 3),
            "p95": percentil(0.95),
            "p99": percentil(0.99),
            "max": round(latencias_ordenadas[-1], 3),
        },
        "menorA500ms": all(latencia < 500 for latencia in latencias_ordenadas),
        "duracionTotalSegundos": round(duracion, 3),
        "nota": "Ráfagas sobre snapshot fijo; no avanza el turno ni mide supervivencia.",
    }


def _entero_positivo(valor: str) -> int:
    try:
        numero = int(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser un entero") from exc
    if numero < 1:
        raise argparse.ArgumentTypeError("debe ser mayor que cero")
    return numero


def _real_positivo(valor: str) -> float:
    try:
        numero = float(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser numérico") from exc
    if numero <= 0:
        raise argparse.ArgumentTypeError("debe ser mayor que cero")
    return numero


def main(argv: list[str] | None = None, *, salida: TextIO | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mide ráfagas locales de POST /paso.")
    parser.add_argument("--url", default="http://127.0.0.1:8000/paso")
    parser.add_argument("--escenario", choices=sorted(ESCENARIOS_DEMO), default="libre")
    parser.add_argument("--sobrevivientes", type=_entero_positivo, choices=(20, 80, 200), default=20)
    parser.add_argument("--semilla", type=int, default=31)
    parser.add_argument("--rondas", type=_entero_positivo, default=1)
    parser.add_argument("--concurrencia", type=_entero_positivo, default=200)
    parser.add_argument("--periodo-segundos", type=_real_positivo, default=2.0)
    parser.add_argument("--timeout-segundos", type=_real_positivo, default=1.0)
    parser.add_argument("--mapa", type=Path, default=MAPA_DEMO_POR_DEFECTO)
    args = parser.parse_args(argv)
    api_key = os.environ.get("NAVIRA_API_KEY", "")
    destino = salida if salida is not None else sys.stdout
    try:
        reporte = ejecutar_carga(
            url=args.url,
            api_key=api_key,
            escenario=args.escenario,
            sobrevivientes=args.sobrevivientes,
            semilla=args.semilla,
            rondas=args.rondas,
            concurrencia=args.concurrencia,
            periodo_segundos=args.periodo_segundos,
            timeout_segundos=args.timeout_segundos,
            mapa=args.mapa,
        )
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(reporte, ensure_ascii=False, sort_keys=True), file=destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
