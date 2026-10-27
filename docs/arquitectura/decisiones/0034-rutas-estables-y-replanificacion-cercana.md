# ADR-034 — Rutas estables y replanteamiento por amenaza cercana

Fecha: 2026-10-27  
Estado: adoptada localmente; comportamiento automático pendiente de verificación  
Origen: solicitud del usuario de evitar que los habitantes den vueltas sin zombies cercanos y cambiar la ruta cuando la amenaza se aproxime.  
Relacionadas: ADR-018, ADR-019 y ADR-020; las complementa en política de replanteamiento.

## Contexto

El planificador asignaba rutas por snapshot y la ocupación de una salida por otro habitante podía enviar al siguiente por un ciclo. En el turno siguiente se recalculaba la cohorte y el desvío podía alternar aunque no hubiese un zombie cerca. Una caché del proceso no sirve como memoria de ruta: no es parte del snapshot, no sobrevive una recreación del servicio y el panel podría consultar versiones pasadas.

## Decisión

1. Guardar en cada `SnapshotMundo` el sufijo dirigido de ruta automática y refugio por habitante. La consulta de panel, la vista previa y `/paso` solo leen o derivan la ruta; únicamente la transición resuelta por compare-and-swap confirma el sufijo restante, después de comprobar que el primer movimiento propuesto se ejecutó.
2. Mientras el siguiente tramo siga legal y no exista un zombie visible activo a tres saltos topológicos o menos, conservar la ruta comprometida incluso cuando haya cambiado la versión del snapshot. El radio se configura en el planificador y el valor inicial 3 es una decisión de demo, no una regla oficial ni una distancia métrica calibrada.
3. Replanificar si un zombie está dentro del radio, el siguiente nodo/tramo está ocupado o cruzado en la fase actual, un cierre confirmado invalida cualquier tramo restante, o la posición confirmada diverge de la ruta. Dormidos y estado RNG no se consultan.
4. Si no hay compromiso, sin amenaza próxima se usa el camino dirigido más corto que respeta bloqueos actuales/cierres. Con amenaza próxima se aplica el pronóstico temporal riesgo-primero. Congestión de otros habitantes no es por sí sola una razón para cambiar de camino. Candidatos con ciclos se descartan.
5. La ruta propuesta viaja junto a la intención interna hasta el resolutor y se conserva solo para sobrevivientes automáticos activos. Una espera, un camino parcial sin refugio, movimiento rechazado, mordida o evacuación no deja un compromiso obsoleto.

## Alternativas

- Conservar una caché en `DecidirPaso`: descartada, porque su ciclo de vida no coincide con el estado confirmado/versionado y un panel podría contaminar decisiones futuras.
- Recalcular el pronóstico en cada turno para todo zombie del mapa: descartada, porque causa desvíos por amenazas remotas, contradice la solicitud y puede aumentar cómputo.
- Inmovilizar la ruta incluso ante cierre o zombie que ocupa el siguiente paso: descartada, porque puede generar una acción ilegal o previsible.
- Penalizar nodos reservados por otros habitantes: no se usa como disparador de desvío; las reglas no modelan capacidad ni exclusión de paso.

## Consecuencias y límites

- El sufijo de ruta es dato privado del snapshot y queda versionado junto con el mundo; no cambia el contrato HTTP de `/paso` ni su respuesta.
- El radio topológico usa calles en ambos sentidos y no equivale a metros o tiempo de llegada. Debe ajustarse con evaluación y evidencia de mordidas antes de afirmarlo como óptimo.
- Las rutas son recomendaciones: el resolutor mantiene autoridad de movimiento, colisión y mordida.
- T-46 debe cubrir persistencia/reanudación, snapshots viejos, humano y automáticos, cierres/cruces, ruta incompleta y replay. La implementación CAM-084 no queda verificada integralmente sin esa ejecución.

## Documentos propietarios

[PRD](../../producto/PRD.md), [TRD](../../producto/TRD.md), [ODDD](../../dominio/ODDD.md), [datos](../../dominio/datos.md), [reglas](../../dominio/reglas-juego.md), [algoritmos](../algoritmos.md), [SPEC-002](../../metodo/especificaciones/SPEC-002-motor-paso.md), [pruebas](../../calidad/pruebas.md), [módulos backend](../modulos/backend.md) y CAM-084.
