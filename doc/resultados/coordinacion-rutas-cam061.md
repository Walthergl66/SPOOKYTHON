# Evaluación exploratoria de coordinación de rutas — CAM-061

Fecha: 2026-10-26, Ecuador continental.

## Configuración

`python -m navira.evaluacion_rutas --mapa data/maps/manta-hackathon-v1.json --semillas 101 202 303 --escenarios mixto --poblaciones 20 --turnos 6 --intensidad alta --eventos-ciudad`

El comparador empareja los mismos mapas/configuraciones/semillas entre Dijkstra y la política de decisión temporal de Navira, ahora con asignación coordinada del primer paso de cada cohorte. La prueba es local, usa el fixture cartográfico de 300 nodos, intensidad sintética alta y seis turnos.

## Resultado observado

| Semilla | Política coordinada: mordidos / evacuados / activos | Dijkstra: mordidos / evacuados / activos | Diferencia de mordidos | Orden lexicográfico |
|---:|---:|---:|---:|---|
| 101 | 8 / 1 / 11 | 16 / 2 / 2 | -8 | mejor |
| 202 | 8 / 2 / 10 | 10 / 3 / 7 | -2 | mejor |
| 303 | 10 / 1 / 9 | 13 / 1 / 6 | -3 | mejor |

Agregado: 26 mordidos, 4 evacuados y 30 activos con coordinación; Dijkstra registró 39 mordidos, 6 evacuados y 15 activos. La prioridad del usuario ordena primero menos mordidos y usa evacuados solo como desempate, por eso el evaluador clasifica los tres pares como mejores aun cuando la evacuación todavía sea menor al turno seis. Los p95 internos por recomendación informados fueron ~12–21 ms para la política coordinada y <1 ms para Dijkstra; no son tiempos HTTP, ni medición de reloj/cadencia.

## Límites y siguiente verificación

Solo se compararon tres semillas, una población, escenario y duración. La evaluación no separa el efecto causal de la coordinación del predictor temporal que ya estaba activo, y no demuestra resultado general, capacidad, seguridad ni cumplimiento del contrato HTTP bajo ráfaga. Extender a más semillas, 20/80/200, mayor duración y métricas HTTP/ciclo de turno antes de decidir que la política mejora globalmente el simulador.
