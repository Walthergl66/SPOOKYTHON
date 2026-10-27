# Política riesgo-primero — CAM-058

Fecha: 2026-10-26, Ecuador continental. Rama: `master`; commit individual local creado. HEAD antes del cambio `350871d`.
Objetivo: aplicar la aclaración del usuario de que la evacuación debe priorizar el menor número de personas mordidas.  
Mapa: `manta-osm-d76772f9d9e9`, fixture sintético parcial de Manta; no representa cobertura municipal validada.

## Cambios verificados

- `DecidirPaso` ahora pronostica amenazas observables y llama la búsqueda temporal con horizonte de hasta 12 turnos y presupuesto de 25 ms por invocación.
- Las rutas ordenan exposición futura estimada antes que turnos y costo de calles. Se recalcula por snapshot; no consulta dormidos ni RNG privado.
- El pronóstico se calcula una vez por versión de snapshot y se comparte entre recomendaciones concurrentes del mismo turno; la caché descarta la versión previa al observar un snapshot nuevo.
- Si el pronóstico no encuentra un refugio en el horizonte o agota el presupuesto, se conserva una ruta Dijkstra del mismo snapshot como respaldo.
- La selección se comparte con `/paso`, el simulador automático y la ruta prevista que proyecta el panel. El contrato de `/paso` no cambia.
- El comparador añade un orden de resultado real: menos mordidos gana primero; evacuados desempata cuando la cantidad de mordidos coincide.

## Evaluación emparejada exploratoria

Se compararon Dijkstra y temporal en mundos nuevos emparejados por mapa, perfil, semilla y población. Cada política evolucionó su propio mundo después de divergir. Parámetros: semillas `101`, `202`, `303`; perfiles `caminantes`, `mixto`, `horda`; cohortes `20`, `80`, `200`; seis turnos; horizonte temporal de 12; 27 pares totales.

| Perfil | Pares | Cambio agregado de mordidos | Pares con menos / igual / más mordidos | Cambio agregado de evacuados |
|---|---:|---:|---:|---:|
| Caminantes | 9 | −5 | 4 / 2 / 3 | +28 |
| Mixto | 9 | −22 | 5 / 2 / 2 | +52 |
| Horda | 9 | −5 | 4 / 4 / 1 | +51 |
| Total | 27 | −32 | 13 / 8 / 6 | +131 |

Según la prioridad `(mordidos ascendente, evacuados descendente)`, temporal fue mejor en 17 pares, igual en 3 y peor en 7. La política bajó las mordidas agregadas en esta muestra, pero no mejoró todos los pares. La peor p95 local por recomendación temporal fue 25,194 ms. No se midió la API HTTP ni la preparación/priorización bajo concurrencia; el presupuesto de búsqueda tampoco representa latencia total del endpoint.

Después de integrar y reiniciar el backend local se inició un smoke en Manta con perfil `mixto`, intensidad `alta`, 20 sobrevivientes y semilla `582026`. `/salud` respondió 200; el control inició la partida y `/panel/estado` devolvió mapa, 64 zombies visibles y 20 rutas previstas. Al segundo turno el snapshot mostraba 7 mordidos, 2 evacuados y 11 activos. Esto confirma movimiento/publicación local, no que esa corrida haya sido mejor que Dijkstra; muestra por qué la comparación debe seguir centrada en mordidas reales.

Una comparación emparejada adicional de esa semilla a 12 turnos dio Dijkstra: 8 mordidos, 5 evacuados y 7 activos; temporal: 9 mordidos, 8 evacuados y 3 activos. Por la prioridad definida, temporal queda peor en este par pese a evacuar tres personas más. En temporal hubo 41 recomendaciones con fallback Dijkstra de 157. Más tarde, la corrida viva alcanzó el turno 33 con 19 mordidos, 0 evacuados y 1 activo. Estos casos no contradicen el agregado de la matriz, pero confirman que el pronóstico vigente no reduce mordidas de forma consistente por ejecución; mejorar y calibrar ese modelo sigue siendo el siguiente trabajo de P3-03.

## Verificación y límites

Pruebas dirigidas: `tests.test_decidir_paso`, `tests.test_api_planner_integration`, `tests.test_simulacion_automatica` y `tests.test_evaluacion_rutas`; incluyen exposición sintética futura, contrato HTTP, ronda automática y preferencia lexicográfica de mordidas.

Esta matriz no es oficial: usa distribuciones sintéticas, supuestos abiertos para movimiento de caminantes/corredor/horda, solo seis turnos y tres semillas. No acredita T-22 completa, T-11, p95 de endpoint, supervivencia a cinco minutos, cobertura de Manta ni uso de emergencia. El reporte debe repetirse con más semillas y transporte real antes de llamar a la política una mejora estable.
