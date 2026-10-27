# Consistencia de ruta y escape inmediato — CAM-059

Fecha: 2026-10-26, Ecuador continental. Mapa: `manta-osm-d76772f9d9e9`, fixture parcial sintético de Manta.

## Problema reproducido

El estado local consultado tras el reporte del usuario era `runId=navira-demo-aa0bd0cdb27f41b791e44f07c42983b4`, turno 12, fase `resuelta`: 20 mordidos, 0 evacuados, 0 activos y 67 zombies visibles. La partida había terminado.

El pronóstico temporal solo sumaba exposición por nodos, aunque el resolutor también muerde por cruce opuesto de una arista. Una inspección de la semilla local 101 halló sobrevivientes cuyo plan era la ruta vacía de un solo nodo: un corredor había ocupado su nodo y no había ruta completa a refugio, por lo que el respaldo los dejaba esperando en el peligro. Además, `ControlSimuladorDemoLocal` creaba una instancia de `DecidirPaso` para la partida automática distinta de la instancia usada por el panel; por ello, cada una podía agotar el presupuesto de búsqueda de manera distinta.

## Cambios

- El control local inyecta al runner automático la misma instancia `DecidirPaso` que consume el panel.
- Se cachea el trayecto por run, versión de snapshot/mapa y sobreviviente, para alinear vista previa y primera acción; la caché se reemplaza al cambiar snapshot. Cálculos de sobrevivientes distintos conservan locks separados.
- El pronóstico estima la masa de caminantes/corredores que recorrería una arista opuesta del mismo segmento. Índice de calles inversas se construye una vez por pronóstico.
- Cruces confirmados bloquean solo la decisión actual. Los cierres viales reales sí persisten.
- Si temporal y Dijkstra no encuentran un camino completo, se selecciona una salida inmediata legal y no ocupada por menor exposición futura de nodo, con costo estático restante al refugio como desempate. Solo se espera si no hay salida despejada.
- El evaluador comparativo ahora configura intensidad y eventos y reutiliza el caso de uso de producción, evitando mantener una segunda implementación temporal divergente. El p95 reportado por recomendación incluye cálculo/cache observado; ya no se separa falsamente un tiempo de pronóstico medido por una ruta duplicada. La métrica específica de preparación y el conteo de fallbacks se informan como no disponibles en esta versión.

## Evaluación emparejada de la configuración del usuario

Comando:

```bash
PYTHONPATH=src /tmp/navira-env/bin/python -m navira.evaluacion_rutas \
  --semillas 101 202 303 --escenarios mixto --poblaciones 20 \
  --turnos 12 --horizonte 12 --intensidad alta --eventos-ciudad
```

Los pares usan mapa/configuración idénticos por semilla; cada política evoluciona su mundo después de divergir.

| Semilla | Dijkstra: mordidos / evacuados / activos | Temporal: mordidos / evacuados / activos | Delta mordidos temporal − Dijkstra |
|---:|---:|---:|---:|
| 101 | 17 / 1 / 2 | 13 / 3 / 4 | −4 |
| 202 | 13 / 3 / 4 | 13 / 5 / 2 | 0 |
| 303 | 18 / 1 / 1 | 16 / 0 / 4 | −2 |
| **Total** | **48 / 5 / 7** | **42 / 8 / 10** | **−6** |

Temporal fue mejor o igual por la prioridad `(mordidos asc, evacuados desc)` en los tres pares; agregado: seis mordidos menos y tres evacuados más. Tres semillas no prueban una mejora general ni garantizan que el run del usuario tenga sobrevivientes. Cada partida sigue aleatoria.

En esta corrida, p95 de `p95TiempoPorRecomendacionMs` temporal fue 90,986/90,105/106,752 ms por semilla; contiene el trabajo del planificador compartido y no es medición del endpoint HTTP ni del ciclo de reloj. Tras construir el índice inverso de aristas, la preparación de pronóstico dejó de tardar ~1,0–1,3 s y se integró dentro de la medición de recomendación. No se declara T-11 ni cumplimiento de dos segundos.

## Verificación funcional CAM-059

- `test_decidir_paso`: ruta preview/acción comparte cálculo y no se queda inmóvil cuando todas las rutas completas están bloqueadas pero hay vecino despejado.
- `test_ruta_temporal`: cruce actual temporal, exposición futura de arista y prioridad de alternativa con menor cruce.
- `test_prediccion_rutas`: caminante visible pronostica cruce opuesto en una calle bidireccional.
- `test_control_simulador_demo`: panel y runner comparten la misma instancia del planificador.
- `test_evaluacion_rutas`: el comparador reproduce intensidad alta con eventos.

## Verificación de cierre

- Pruebas enfocadas de ruta, predicción, decisión, runner automático, control y evaluación: 43 OK.
- Suite backend completa: 173 pruebas OK. La salida de `argparse` sobre `--turnos 0` es el caso negativo esperado por una prueba.
- `cd frontend && npm run build`: correcto; queda el aviso conocido de chunk MapLibre mayor a 500 kB.
- `python3 scripts/check_docs.py`: 86 Markdown en `doc/`, 88 archivos comprobados; `python3 scripts/check_sdd.py`: ocho SPEC estructuralmente trazables; regresiones `test_check_sdd.py`: ocho OK.
- `compileall` y `git diff --check`: correctos.
- Smoke inicial desde tablero con backend reiniciado: el mapa y las rutas aparecieron en fase de decisiones y la partida avanzó. En el turno 24 se observó 15 mordidos, 3 evacuados y 2 activos; luego el contador cambió a 19 mordidos y 0 evacuados mientras un personaje permanecía activo. Esa regresión reveló el defecto independiente de resolución corregido en CAM-060 (evacuados volvían a recibir mordidas).
- Smoke actualizado con CAM-060, semilla 202: el mapa 3D cargó, el snapshot inicial incluyó 20 rutas previstas y el run terminó en turno 18 con 15 mordidos, 5 evacuados y 0 activos. Los evacuados no volvieron a recibir mordidas durante la observación. Un solo run local no garantiza supervivencia ni mejora universal.
- CAM-060: 12 pruebas focalizadas de resolutor; suite backend completa de 174 pruebas OK. `python3 scripts/check_docs.py` (86 Markdown/88 archivos), `python3 scripts/check_sdd.py` (ocho SPEC), ocho regresiones, `compileall`, `git diff --check` y build frontend correctos. Las pruebas automáticas y esta observación no son T-22 ampliada ni medición HTTP/carga.

Esta evidencia es una comparación local de demo sintética. No valida cartografía completa, parámetros oficiales, terremoto/tsunami, performance HTTP o supervivencia universal; T-22 permanece parcial.
