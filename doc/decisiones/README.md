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
| [ADR-010](0010-busqueda-temporal-acotada.md) | Búsqueda temporal acotada para rutas | Integrada por CAM-058; núcleo original experimental | CAM-033 construyó el buscador; ADR-018 define su política activa y respaldo. |
| [ADR-011](0011-pronostico-visible-por-escenarios.md) | Pronóstico observable por escenarios | Implementado localmente, exploratorio | CAM-034: fases privadas excluidas, supuestos explícitos; no integrado a `/paso`. |
| [ADR-012](0012-seleccion-politica-baseline.md) | Mantener Dijkstra como política activa | Sustituido por ADR-018 | Decisión histórica basada en CAM-035. |
| [ADR-013](0013-sesion-y-aparicion-humana-local.md) | Sesión propietaria y aparición humana local | Implementada parcialmente, local | CAM-036: cookie segura y aparición CAS; el ciclo local se completa en CAM-039/040. Expiración definida en ADR-014; durable y despliegue pendientes. |
| [ADR-014](0014-expiracion-local-de-sesion-humana.md) | Expiración local por inactividad sin transferir personaje | Adoptada para demo local | CAM-046: TTL deslizante de 30 minutos y reserva tombstone; producción durable pendiente. |
| [ADR-015](0015-control-local-de-demo.md) | Operar simulador desde tablero solo en loopback con opt-in | Aceptada e implementada localmente | CAM-050/T-26; superficie productiva no incluida. |
| [ADR-016](0016-mapa-maplibre-openfreemap.md) | Renderer MapLibre y tiles vectoriales OpenFreeMap/OSM para mapa 3D | Aceptada para primera integración local | CAM-051; cobertura 3D de Manta por comprobar y servicio público sin SLA. |
| [ADR-017](0017-perfiles-sinteticos-de-amenazas.md) | Intensidad sintética, distribución espacial de zombies e incidentes viales de demo | Aceptada para demo local; no define ronda oficial | CAM-057/T-28/T-29. |
| [ADR-018](0018-politica-riesgo-prioritario.md) | Política activa que prioriza exposición observable y comparación mordidos/evacuados | Aceptada para simulador local con evaluación pendiente | CAM-058; reemplaza la selección Dijkstra activa de ADR-012, conserva Dijkstra como fallback. |
| [ADR-019](0019-cruces-y-ruta-consistente.md) | Exposición de cruces opuestos, escape inmediato y coincidencia de ruta preview/acción por snapshot | Implementada localmente; evidencia de tres pares exploratoria | CAM-059; amplía ADR-018 sin cambiar el contrato ni consultar estado privado. |
| [ADR-020](0020-planificacion-coordinada-por-snapshot.md) | Asignación conjunta y penalización suave de congestión | Implementada localmente; impacto en mordidas pendiente | CAM-061/T-35; replanifica por snapshot sin inventar capacidad vial/refugio. |

Usar [plantilla](../plantillas/decision.md). Numeración correlativa, fecha, contexto, decisión, alternativas, consecuencias, pendientes y enlaces. No renumerar IDs ya citados. Para cambiar una decisión relevante, añadir ADR nuevo y marcar el anterior sustituido con enlace recíproco. Correcciones menores pueden aclararse sin fingir que la decisión original ya decía otra cosa.
