# Smoke local de concurrencia HTTP — CAM-020

Fecha: 2026-10-26. Estado: evidencia local parcial; no es una medición oficial ni cierra T-11.

## Configuración

- Código: implementación CAM-020 en `feat/navira-http-load-runner`, sobre `7e7ac5f`.
- Servidor: Uvicorn de un proceso, escuchando en `127.0.0.1`; cliente y servidor corrieron en el mismo host.
- Entorno: Linux x86_64, Python 3.14.8, 12 CPUs lógicas.
- Escenario: `libre`, semilla `31`, fixture sintético de cinco nodos, cuatro nodos no refugio.
- Snapshot: fijo en turno `0`. El endpoint no muta la partida ni avanza el reloj entre llamadas.
- Procedimiento: una ráfaga por tamaño, concurrencia máxima igual al tamaño; API key local efímera por variable de entorno; sin warm-up de `/paso` ni repetición estadística.

## Resultados observados

| Solicitudes concurrentes | HTTP 200 | Fallidas | p50 (ms) | p95 (ms) | p99 (ms) | Máxima (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 20 | 20 | 0 | 4.780 | 7.872 | 7.958 | 7.958 |
| 80 | 80 | 0 | 7.912 | 11.972 | 12.347 | 12.347 |
| 200 | 200 | 0 | 17.319 | 26.066 | 29.529 | 31.485 |

Las tres ráfagas respondieron con el esquema esperado y todas las solicitudes quedaron por debajo de 500 ms en esta ejecución local. El reporte no demuestra disponibilidad, p95 sostenido ni rendimiento en AWS o desde la ubicación del evaluador.

## Límites y continuación

Fue una sola ráfaga por cohorte, sin intervalo de dos segundos ni repetición de 150 turnos; tampoco hubo actualización del mundo, mapa de Manta, zombies o supervivencia. Es una comprobación del transporte y ensamblaje local del endpoint, no T-11 completo ni una garantía de capacidad. Para completarlo se requiere repetir rondas cronometradas en el entorno previsto y conservar errores/timeouts en percentiles y denominadores.
