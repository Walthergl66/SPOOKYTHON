# Evaluación HTTP con cadencia de dos segundos — CAM-029

Fecha: 2026-10-26, Ecuador continental. Entorno: local, `/tmp/navira-env`. Base de código: `4f943d8` más el cambio CAM-029. Uvicorn y el cliente corrieron en el mismo host mediante loopback.

## Configuración

- Mapa: `data/maps/manta-hackathon-v1.json`, versión `manta-osm-d76772f9d9e9`.
- Escenario sintético: `mixto`; semilla fija: `20261026`.
- Cohortes: 20, 80 y 200 sobrevivientes, cada una en una partida aislada.
- Tres turnos por cohorte, período objetivo de 2 s, máximo 200 workers y timeout HTTP de 1 s.
- Comando: `PYTHONPATH=src /tmp/navira-env/bin/python -m navira.evaluacion_local --turnos 3 --poblaciones 20 80 200 --concurrencia 200 --semilla 20261026 --periodo-segundos 2`.
- Los inicios se programan desde un reloj monotónico común por partida. Se registran retraso de inicio, tiempo total de cada ciclo y solicitudes a `/paso`; después se resuelven las intenciones devueltas.

## Resultados observados

| Cohorte | Turnos | Solicitudes | Fallos | p50 (ms) | p95 (ms) | p99 (ms) | Máx. (ms) | Ciclo máximo (ms) | Retraso máximo de inicio (ms) | Evacuados | Mordidos | Activos finales | Duración (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 3 | 59 | 0 | 13,496 | 18,017 | 19,838 | 19,838 | 59,078 | 0,176 | 2 | 0 | 18 | 4,208 |
| 80 | 3 | 236 | 0 | 34,543 | 54,593 | 58,284 | 60,994 | 207,267 | 0,072 | 8 | 0 | 72 | 4,326 |
| 200 | 3 | 582 | 0 | 74,265 | 103,734 | 107,077 | 113,576 | 479,105 | 0,074 | 28 | 0 | 172 | 4,547 |

Los tres inicios de turno de cada partida quedaron separados por aproximadamente 2.000 ms; ningún ciclo superó el período objetivo. Hubo 877 solicitudes, todas HTTP 200 y ninguna fallida. El p95 observado fue inferior a 150 ms en esta ejecución local concreta.

## Alcance y límites

Esto verifica el programador de cadencia y el avance del mundo durante tres turnos, no el reloj de producción. Son cohortes y composición zombie sintéticas; solo hay una ejecución por tamaño y semilla. Tres turnos no equivalen a los 150 turnos ni a los cinco minutos de las rondas oficiales. No se midió desde AWS, internet o la ubicación del evaluador, no se resolvieron reglas pendientes de densidad zombie y no se verificó persistencia durable. El p95 local no demuestra que la meta se mantenga bajo una ronda completa. P-07, P-09 y T-11 siguen abiertos; P2-03 y P5-01 permanecen en curso.

El fixture usa referencias de zona segura ante tsunami del GAD Manta y no acredita seguridad sísmica. El resultado de supervivencia de esta muestra no es pronóstico ni certificación para emergencias reales.
