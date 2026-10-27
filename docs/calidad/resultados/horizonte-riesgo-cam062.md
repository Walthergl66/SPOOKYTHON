# CAM-062 — Exposición limitada al horizonte del pronóstico

Fecha: 2026-10-26. Revisión local en `master`.

## Cambio y evidencia funcional

La asignación conjunta sumaba el último campo de riesgo pronosticado para cada paso restante de una ruta, aun cuando esos pasos excedían el horizonte. El pronóstico es un escenario acotado; tratar su último turno como persistente podía inflar artificialmente el riesgo de rutas largas. Ahora solo se suma exposición de pasos con una condición futura explícita; el costo de ruta desempata la cola sin pronóstico. Esto no afirma que el futuro no modelado sea seguro.

T-36 valida el límite con un pronóstico de un paso y una ruta de cinco nodos. La suite focalizada `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_decidir_paso -v` pasó 13 pruebas.

## Comparación exploratoria actual

Comando: `PYTHONPATH=src /tmp/navira-env/bin/python -m navira.evaluacion_rutas --semillas 101 202 303 --escenarios mixto horda --poblaciones 20 --turnos 30 --horizonte 12 --intensidad alta --eventos-ciudad`.

Se compararon mundos sintéticos emparejados por semilla, mapa, escenario, población e intensidad; en cada par Dijkstra se contrastó con la política temporal coordinada. El evaluador aplica el resolutor común. Agregado de seis pares (120 personas por política): temporal 24 evacuados, 74 mordidos y 22 activos; Dijkstra 20 evacuados, 77 mordidos y 23 activos. Temporal redujo mordidas en cuatro pares y las aumentó en dos; evacuó más en dos, empató en tres y menos en uno. El orden global por criterio de producto fue mejor en cuatro pares y peor en dos.

La comparación no aísla el efecto causal de este cambio porque el evaluador aplica la política completa, no hay corrida antes/después idéntica capturada por T-36, y seis pares no representan una muestra suficiente. La ejecución fue local y sintética; sus tiempos internos no son HTTP/p95 ni ciclo de reloj. No se declara menor mortalidad universal ni seguridad real.
