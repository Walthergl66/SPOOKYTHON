# ADR-012 — Mantener Dijkstra como política activa

Fecha: 2026-10-26  
Estado: decidido con evidencia exploratoria local  
Origen: selección P3-03, comparación CAM-035

## Contexto

La ruta temporal y el pronóstico observable superaron al baseline en una comparación de tres turnos sobre 27 pares sintéticos emparejados, con resultados repetidos estables. Sin embargo, corredor con sobrevivientes inmóviles y horda estacionaria son supuestos provisionales; solo hubo tres semillas y no se midió el endpoint concurrente ni una ronda oficial.

## Decisión

Conservar Dijkstra como política usada por `/paso`. Mantener pronóstico y búsqueda temporal en el evaluador para nuevas pruebas. No publicar rutas temporales en el panel ni consumirlas desde el servicio HTTP hasta medir el costo de extremo a extremo, incluir cacheado versionado de pronóstico de forma segura y ampliar semillas/turnos con reglas aceptadas.

El fallback Dijkstra permanece obligatorio ante ruta sin horizonte, presupuesto agotado u observación incompleta. No se afirma mejora de supervivencia a partir del conteo de evacuaciones de tres turnos.

## Evidencia

CAM-035: en 27 pares hubo 15 con más evacuados, 12 iguales y ninguno peor; suma delta +15 evacuados y cero delta en mordidos. Dos pasadas produjeron los mismos resultados de mundo. El p95 local máximo por recomendación temporal fue 1,648 ms, más preparación de pronóstico hasta p95 1,076 ms; ambos son mediciones de función local, no HTTP. El comparador tuvo 2.027 fallbacks a Dijkstra.

## Revisión

Revisar cuando P-02/P-03/P-07/P-09 tengan reglas suficientemente confirmadas para modelar; ejecutar T-22 ampliada y T-11 en el contrato HTTP. Si la mejora deja de ser reproducible o afecta el presupuesto, mantener Dijkstra.
