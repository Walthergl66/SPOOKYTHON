# Reutilización de rutas estáticas — CAM-132

Fecha: 2026-10-28 (America/Guayaquil).

## Motivo y cambios

El perfil de `/paso` con 200 sobrevivientes atribuyó 26.75 s de 38.99 s a `_ruta_estatica`; 56 llamadas a `seleccionar_refugio` generaron 56 búsquedas completas desde distintos orígenes. Se agrupan los habitantes cuyo compromiso quedó inválido y que no tienen zombies cerca, y se reutiliza un `RutasHaciaRefugios` para cada refugio objetivo y snapshot. Cuando algún nodo de refugio está bloqueado se mantiene el selector anterior para preservar su comportamiento especial.

El perfil posterior encontró otro costo del pronóstico de corredores: una BFS dirigida repetida desde miles de posiciones posibles. Se añadió un índice inverso multi-origen acotado al alcance del corredor; su regresión compara el resultado con las BFS originales en todos los nodos del fixture, incluidos desempates y cierres. Además, `RutasHaciaRefugios` reutiliza el índice de aristas entrantes del grafo inmutable entre campos; cada snapshot sigue filtrando sus propios cierres. Ninguna de estas optimizaciones cambia contrato HTTP, filtros o prioridades de ruta.

## Verificación y medición

Benchmark local HTTP loopback con el mismo comando antes y después:

```sh
PYTHONPATH=backend/src /tmp/navira-perf-env/bin/python -m navira.evaluacion_local --turnos 3 --poblaciones 20 80 200 --concurrencia 200 --periodo-segundos 2.0
```

| Cohorte | p95 antes | p95 después de compartir rutas (primera muestra) | p95 versión actual, última muestra | p99 actual | Fallos actuales | Turnos actuales que superaron 2 s |
|---:|---:|---:|---:|---:|---:|---:|
| 20 | 87.117 ms | 49.355 ms | 94.565 ms | 102.031 ms | 0 | 2/3 |
| 80 | 52.977 ms | 73.834 ms | 71.821 ms | 76.220 ms | 0 | 1/3 |
| 200 | 158.135 ms | 147.181 ms | 230.814 ms | 264.753 ms | 0 | 1/3 |

En otra corrida de la versión actual solo con 200 habitantes, p95 total fue 198.250 ms y p99 224.296 ms; por turno, p95 222.535/110.039/159.238 ms y ciclos de 1.620/1.908/2.100 s. La medición actual muestra variabilidad y p95 por encima de 150 ms en R3; la meta aún no se cumple de forma reproducible.

Las pruebas focalizadas `test_dijkstra`, `test_decidir_paso` y `test_prediccion_rutas` pasaron 37/37; las regresiones cubren el campo compartido y la equivalencia del índice de corredores con la búsqueda directa. Después de todos los cambios, la suite completa pasó 248/248 en 383.471 s con `PYTHONPATH=backend/src /tmp/navira-perf-env/bin/python -m unittest discover -s backend/tests -p 'test_*.py'`. El perfil previo atribuyó 26.75 s a las rutas estáticas. La primera medición tras compartirlas redujo los ciclos de 200 que habían llegado a 25–27 s a alrededor de 1.5–2.3 s, aunque las rondas actuales todavía exceden a veces el período de dos segundos.

## Límites y siguiente paso

Son comparaciones exploratorias de pocas rondas, en loopback y compartiendo host entre emisor y servidor; no demuestran p95 estable, latencia pública de Lightsail ni la campaña oficial. La versión actual todavía excede la meta p95 en 200 habitantes y a veces tarda más de dos segundos por turno. Repetir la campaña completa varias veces, reducir el tiempo de planificación de R3 y medir desde un cliente externo contra la versión actualizada antes de declarar TRD-02/T-11 satisfechos.
