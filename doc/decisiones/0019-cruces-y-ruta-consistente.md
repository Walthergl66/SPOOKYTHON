# ADR-019 — Riesgo de cruce y ruta consistente por snapshot

Fecha: 2026-10-26
Estado: implementada localmente; evaluación de supervivencia preliminar
Origen: reporte del usuario de 20/20 sobrevivientes mordidos y fallo del indicador de ruta.

## Contexto

El resolutor puede morder por contacto en el nodo final o por cruzar en sentidos opuestos el mismo segmento durante ese turno. El pronóstico CAM-058 solo estimaba ocupación futura por nodo. Además, la vista del panel y el simulador volvían a ejecutar una búsqueda acotada por reloj: ante distinta carga, una llamada podía agotar el presupuesto y otra completar, aunque ambas leyeran el mismo snapshot.

## Decisión

1. El pronóstico por turno añade exposición en la arista dirigida del sobreviviente cuando un zombie observable tiene probabilidad de recorrer el sentido opuesto del mismo segmento. Nodos y cruces se consideran mecanismos de mordida distintos y se acota su puntuación combinada por paso.
2. Un cruce zombie confirmado en la fase actual bloquea esa arista solo para la acción actual; no se convierte por error en cierre vial permanente ni se propaga a turnos futuros. Los cierres viales confirmados sí persisten.
3. `DecidirPaso` conserva la ruta completa por `(runId, versión de snapshot, versión de mapa, sobreviviente)`. El panel y el movimiento automático reutilizan la misma primera acción. Al cambiar snapshot, reemplaza la caché anterior; los cálculos de sobrevivientes diferentes no se serializan entre sí.
4. Si el pronóstico temporal y Dijkstra no encuentran un camino completo, el sistema elige una calle vecina legal y despejada por menor exposición observable del próximo turno, luego por costo estático restante al refugio. Espera solo cuando no hay salida segura conocida.

El pronóstico sigue siendo una aproximación con caminantes aleatorios, sobrevivientes de corredor congelados y hordas estáticas. No lee dormidos ni RNG privado, y no promete supervivencia.

## Alternativas

- Mantener solo ocupación de nodos: descartada porque ignora R-10, una mordida del resolutor.
- Tratar un cruce ya ocurrido como cierre permanente: descartada porque un peligro temporal no es un incidente vial.
- Volver a calcular la ruta en cada consumidor: descartada porque el límite de tiempo puede cambiar el resultado y desalinear indicador y acción.
- Cachear rutas de toda la vida de la partida: descartada porque un snapshot nuevo invalida peligros y posiciones; la caché queda limitada a una versión.

## Consecuencias y límites

- T-31 comprueba que vista previa y acción compartan exactamente el trayecto en el snapshot.
- T-32 comprueba riesgo estimado de cruce opuesto y vigencia temporal de cruces conocidos.
- T-33 comprueba la salida inmediata cuando no existe una ruta completa.
- El run observado por el usuario terminó con 20 mordidos, 0 evacuados y 0 activos en el turno 12, con 67 zombies visibles. En tres pares exploratorios (20, mixto, intensidad alta, cierres activos, 12 turnos), CAM-059 produjo seis mordidos menos agregados que Dijkstra, y no tuvo más mordidos en ningún par. La corrección no se puede presentar como mejora universal; hacen falta más semillas.
- El límite temporal por recomendación sigue vigente. La asignación conjunta posterior se registra en [ADR-020](0020-planificacion-coordinada-por-snapshot.md); esta decisión conserva su alcance de cruces y coherencia de ruta.

## Documentos y módulos afectados

`src/navira/routing/temporal.py`, `src/navira/routing/prediccion.py`, `src/navira/application/decidir_paso.py`, pruebas de ruta/planificación, [SPEC-002](../especificaciones/SPEC-002-motor-paso.md), [algoritmos](../algoritmos.md), [pruebas](../pruebas.md), [trazabilidad](../trazabilidad.md) e historial CAM-059.
