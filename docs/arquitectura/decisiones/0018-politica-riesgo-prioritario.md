# ADR-018 — Política temporal prioritaria por riesgo visible

Fecha: 2026-10-26  
Estado: aceptada e integrada localmente; evaluación de producto pendiente  
Origen: aclaración del usuario: el propósito de la evacuación es encontrar rutas que mantengan la cantidad de personas mordidas lo más baja posible.

## Contexto

La política activa anterior, Dijkstra, evitaba bloqueos y zombies visibles en el snapshot, pero no estimaba amenazas en los siguientes turnos. El proyecto ya tenía búsqueda temporal y un pronóstico observable, separados del servicio activo. La selección y evaluación anteriores daban más peso a evacuados; eso no representa la prioridad confirmada por el usuario.

## Decisión

Conectar la búsqueda temporal a `DecidirPaso`, compartido por `/paso`, el simulador automático y la vista previa del panel. La prioridad de una ruta es, en orden: validez topológica y bloqueos confirmados; menor suma de exposición futura estimada; menos turnos; costo ponderado de calles; secuencia determinista. El planificador vuelve a calcular desde el snapshot de cada turno. El pronóstico inmutable se comparte una vez por versión entre recomendaciones del mismo snapshot.

La proyección solo usa zombies activos visibles, sobrevivientes observables, calles y cierres confirmados. No lee dormidos ni estado RNG privado. Si no produce una ruta completa dentro del horizonte/presupuesto, conserva Dijkstra como respaldo. El contrato HTTP permanece igual.

La evaluación de resultados de partida ordena lexicográficamente `(mordidos ascendente, evacuados descendente)`. La exposición es una señal de planificación provisional, no el conteo real de mordidas ni una probabilidad calibrada. Una ruta temporal no garantiza menos mordidas en cada semilla.

## Alternativas consideradas

- Mantener Dijkstra como activa: rechazado porque no anticipa amenazas en evolución y no refleja el objetivo primario de supervivencia.
- Maximizar evacuados con una penalización ponderada de mordidas: rechazado porque mezcla magnitudes y puede tratar una mordida como compensable por más evacuaciones.
- Usar el RNG o la ubicación futura exacta de zombies: rechazado por la frontera de información, la privacidad y la falta de certeza sobre el futuro.
- Eliminar Dijkstra: rechazado; conserva una respuesta completa ante límite o pronóstico insuficiente.

## Evidencia y límites

CAM-058 ejecuta 27 pares emparejados sobre tres perfiles sintéticos, tres semillas, cohortes de 20/80/200 y seis turnos con horizonte de 12. Temporal obtuvo agregado de 32 mordidos menos y 131 evacuados más que Dijkstra, pero produjo más mordidos en seis pares y menos en trece. La peor medición p95 por recomendación temporal fue 25,194 ms dentro de la función local. Estos datos son exploratorios, no miden HTTP/concurrencia ni T-11, y no prueban mejora universal. Ver [reporte CAM-058](../../calidad/resultados/politica-riesgo-cam058.md).

Las fases uniformes de caminante, ubicaciones congeladas de sobrevivientes para corredores y horda estática siguen siendo aproximaciones (P-02/P-03/P-07/P-09). Ejecutar T-22 con semillas de validación, T-11 vía HTTP y rondas más largas antes de presentar la política como mejora estable.

## Consecuencias

- `/paso` mantiene método, esquema, autenticación y regla de determinismo para el mismo snapshot.
- Simulador automático y juego comparten el caso de uso; no se añade un resolutor alterno.
- El panel puede mostrar la ruta temporal calculada con la misma observación del servidor.
- Los resultados comparativos reportan mordidos antes que evacuados; vivos/activos siguen visibles por separado.
- La API puede exceder el presupuesto interno de búsqueda por el tiempo de pronóstico/serialización; debe medirse con transporte real.

## Documentos y módulos propietarios afectados

`src/navira/application/decidir_paso.py`, `src/navira/evaluacion_rutas.py`, pruebas de planificación y evaluación, PRD-10, TRD-14, SPEC-002 CA-002-06, [algoritmos](../algoritmos.md), [trazabilidad](../../metodo/trazabilidad.md) y [plan](../../seguimiento/plan-implementacion.md).
