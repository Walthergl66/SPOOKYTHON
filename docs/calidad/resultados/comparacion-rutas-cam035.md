# Comparación local de políticas de ruta — CAM-035

Fecha: 2026-10-26, Ecuador continental. Evaluador: `python -m navira.evaluacion_rutas`.  
Mapa: `manta-osm-d76772f9d9e9`, fixture parcial de 300 nodos y cuatro refugios.  
Alcance: simulación local de tres turnos, por perfil, semilla y cohorte; no es evaluación oficial.

## Diseño

Se emparejaron Dijkstra y recomendación temporal en partidas nuevas con la misma combinación de escenario sintético, semilla y población. Se usaron perfiles `caminantes`, `mixto` y `horda`; semillas `101`, `202` y `303`; poblaciones `20`, `80` y `200`; 27 pares en total. Cada política se ejecutó dos veces para comprobar estabilidad de resultados. Se comparte el estado inicial reproducido y las mismas reglas del prototipo; después de divergencias de decisiones, cada mundo avanza su propio RNG privado mediante el coordinador. El planificador temporal solo recibe la proyección observable y el pronóstico CAM-034. Cuando no encuentra refugio dentro del horizonte de seis turnos o falla su límite, aplica el primer paso Dijkstra del mismo snapshot.

Comando:

```sh
PYTHONPATH=src /tmp/navira-env/bin/python -m navira.evaluacion_rutas --turnos 3
```

## Resultados por cohorte

Las cifras son sumas de nueve partidas emparejadas por cada población (tres perfiles × tres semillas):

| Población | Política | Evacuados | Mordidos | Activos | Pares con más evacuados (de 9) | p95 máximo local por recomendación (ms) |
|---:|---|---:|---:|---:|---:|---:|
| 20 | Dijkstra | 24 | 0 | 156 | — | 0,776 |
| 20 | Temporal con fallback | 27 | 0 | 153 | 3 | 1,554 |
| 80 | Dijkstra | 107 | 2 | 611 | — | 0,992 |
| 80 | Temporal con fallback | 113 | 2 | 605 | 6 | 1,648 |
| 200 | Dijkstra | 240 | 0 | 1.560 | — | 0,853 |
| 200 | Temporal con fallback | 246 | 0 | 1.554 | 6 | 1,485 |

En los 27 pares, Dijkstra obtuvo 371 evacuados, 2 mordidos y 2.327 activos; temporal obtuvo 386 evacuados, los mismos 2 mordidos y 2.312 activos. Temporal tuvo más evacuados en 15 pares, empató en 12 y fue peor en ninguno. Hubo `2.027` recomendaciones temporales que recurrieron a Dijkstra. El p95 máximo observado de preparación de un pronóstico por turno fue `1,076 ms` en esta corrida.

Las dos ejecuciones con los mismos inputs coincidieron en estados finales, evacuados, mordidos, activos, rutas de fallback y deltas. Las duraciones de CPU varían entre ejecuciones; no se usa tiempo como afirmación reproducible del servicio.

## Decisión

El resultado justifica conservar la política temporal como candidata experimental en el evaluador, pero no activarla en `/paso`: tres turnos sintéticos no validan la predicción en rondas largas; posiciones congeladas del corredor y horda estática son supuestos provisionales; y no se midió HTTP concurrente ni costo de preparar/cachear el pronóstico desde el endpoint. Dijkstra sigue como política activa hasta cubrir P3-03 end-to-end, P2-03/T-11 y reglas pendientes. No se declara T-22 completa ni se atribuye mejora de supervivencia a estos resultados.

El p95 mostrado cubre solo una invocación local de selección de ruta; la preparación del pronóstico se midió aparte. No incluye FastAPI, espera de concurrencia, reloj de dos segundos, latencia remota, 150 turnos, costos, persistencia, AWS o seguridad cartográfica. Las zonas seguras del fixture corresponden a tsunami y no acreditan seguridad sísmica.
