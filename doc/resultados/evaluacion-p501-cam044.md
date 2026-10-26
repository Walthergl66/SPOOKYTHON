# P5-01: evaluación extendida HTTP loopback — CAM-044

Fecha: 2026-10-26, Ecuador continental.

Se solicitó la duración máxima de 150 turnos por cohorte con período de 2 s y se ejecutó una sola matriz sobre el fixture Manta. El evaluador termina una partida cuando sus sobrevivientes ya no están activos, por lo que la corrida no llegó a 150 turnos ni a cinco minutos.

## Configuración

- Comando: `PYTHONPATH=src /tmp/navira-env/bin/python -m navira.evaluacion_local --turnos 150 --poblaciones 20 80 200 --concurrencia 200 --semilla 20261026 --escenario mixto --periodo-segundos 2`
- Medición: servidor Uvicorn y cliente HTTP en loopback del mismo host.
- Mapa: `manta-osm-d76772f9d9e9` (fixture, no navegación real).
- Semilla: `20261026`.
- Escenario: `mixto` sintético; concurrencia máxima configurada: 200.

## Resultado observado

| Sobrevivientes iniciales | Turnos solicitados/ejecutados | Solicitudes HTTP | Errores | p95 por solicitud | Ciclo máximo | Retraso máximo de inicio | Duración | Resultado final |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 20 | 150 / 12 | 129 | 0 | 18,860 ms | 62,461 ms | 0,113 ms | 24,151 s | 13 evacuados, 7 mordidos |
| 80 | 150 / 15 | 621 | 0 | 58,097 ms | 218,492 ms | 0,175 ms | 30,196 s | 80 evacuados |
| 200 | 150 / 13 | 1.322 | 0 | 92,060 ms | 480,701 ms | 0,087 ms | 26,127 s | 200 evacuados |

Total de la matriz: 2.072 solicitudes y 80,474 s de tiempo reportado, sin fallos HTTP ni ciclos fuera del período en los turnos ejecutados. Los p95 observados quedaron bajo la meta local de 150 ms y los ciclos bajo 2 s para esta única corrida.

## Alcance de la evidencia

Es una medición exploratoria, reproducible solo en condiciones parecidas del mismo host. La terminación temprana explica el número de turnos; no se prolongó artificialmente un mundo terminado. No acredita 150 turnos, cinco minutos sostenidos por cohorte, repeticiones, la distribución oficial de evaluación, latencia de red, AWS ni T-11. Por tanto P2-03 y P5-01 continúan en curso.
