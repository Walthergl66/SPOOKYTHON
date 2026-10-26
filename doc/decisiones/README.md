# Registro de decisiones de arquitectura y producto

Un ADR documenta una elección duradera y su motivo. «Aceptada para diseño» no significa implementada o verificada. Las instrucciones actuales del usuario prevalecen sobre una decisión anterior; registrar su sustitución en vez de esconderla.

| ID | Decisión | Estado | Evidencia de implementación |
|---|---|---|---|
| [ADR-001](0001-arquitectura-base.md) | Núcleo modular Python, API FastAPI y stack AWS inicial | Aceptada para diseño | Pendiente. |
| [ADR-002](0002-dos-modos.md) | Simulador y juego comparten mundo y reglas | Alcance solicitado; diseño inicial adoptado | Pendiente. |
| [ADR-003](0003-estado-y-turnos.md) | Versiones por partida/turno/fase y coordinador único | Aceptada para diseño | Pendiente. |
| [ADR-004](0004-documentacion-y-continuidad.md) | `doc/` canónico y protocolo de incorporación | Adoptada en documentación | Archivos presentes y comprobador documental. |
| [ADR-005](0005-prd-trd-oddd-sdd.md) | PRD/TRD, modelo OO + DDD y SDD trazable | Adoptada para el método | SPEC-006 y su evidencia; app pendiente. |
| [ADR-006](0006-nombre-navira.md) | Nombre oficial Navira | Decisión explícita del usuario | Documentación vigente actualizada; paquete `navira` previsto. |
| [ADR-007](0007-mapa-manta-y-evidencia-de-amenazas.md) | Fuentes de mapa y límites de seguridad por amenaza | Aceptada para dataset de simulación | Exportación OSM con metadatos del GAD Manta; validación de sismo pendiente. |
| [ADR-008](0008-simulacion-estocastica-reproducible.md) | Mundo estocástico con reproducción por semilla y estado privado | Aceptada como requisito y diseño | Parcial: RNG walker/snapshot existe; inicialización completa y rondas no están implementadas. |
| [ADR-009](0009-panel-ws-snapshots-completos.md) | WebSocket de panel con snapshots completos | Implementada localmente | CAM-032: snapshot al conectar, cambios de versión, heartbeat, origen same-host y reconexión ASGI probados; memoria local solamente. |

Usar [plantilla](../plantillas/decision.md). Numeración correlativa, fecha, contexto, decisión, alternativas, consecuencias, pendientes y enlaces. No renumerar IDs ya citados. Para cambiar una decisión relevante, añadir ADR nuevo y marcar el anterior sustituido con enlace recíproco. Correcciones menores pueden aclararse sin fingir que la decisión original ya decía otra cosa.
