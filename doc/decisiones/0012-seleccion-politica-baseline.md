# ADR-012 — Mantener Dijkstra como política activa

Fecha: 2026-10-26  
Estado: sustituido por [ADR-018](0018-politica-riesgo-prioritario.md)
Origen: selección P3-03, comparación CAM-035

## Contexto

La ruta temporal y el pronóstico observable superaron al baseline en una comparación de tres turnos sobre 27 pares sintéticos emparejados, con resultados repetidos estables. Sin embargo, corredor con sobrevivientes inmóviles y horda estacionaria son supuestos provisionales; solo hubo tres semillas y no se midió el endpoint concurrente ni una ronda oficial.

## Decisión original (histórica)

Conservar Dijkstra como política usada por `/paso`. Esta decisión fue reemplazada en CAM-058 por la instrucción posterior del usuario de priorizar la menor cantidad de mordidos, registrada en [ADR-018](0018-politica-riesgo-prioritario.md).

El fallback Dijkstra permanece obligatorio ante ruta sin horizonte, presupuesto agotado u observación incompleta. No se afirma mejora de supervivencia a partir del conteo de evacuaciones de tres turnos.

## Evidencia

CAM-035: en 27 pares hubo 15 con más evacuados, 12 iguales y ninguno peor; suma delta +15 evacuados y cero delta en mordidos. Dos pasadas produjeron los mismos resultados de mundo. El p95 local máximo por recomendación temporal fue 1,648 ms, más preparación de pronóstico hasta p95 1,076 ms; ambos son mediciones de función local, no HTTP. El comparador tuvo 2.027 fallbacks a Dijkstra.

## Revisión

La evidencia y el razonamiento originales se conservan arriba. Los riesgos de reglas pendientes y evaluación siguen vigentes para ADR-018.
