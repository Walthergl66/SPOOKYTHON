# Registro de decisiones de arquitectura y producto

Un ADR documenta una elección duradera y su motivo. «Aceptada para diseño» no significa implementada o verificada. Las instrucciones actuales del usuario prevalecen sobre una decisión anterior; registrar su sustitución en vez de esconderla.

| ID | Decisión | Estado | Evidencia de implementación |
|---|---|---|---|
| [ADR-001](0001-arquitectura-base.md) | Núcleo modular Python, API FastAPI y stack AWS inicial | Aceptada para diseño | Pendiente. |
| [ADR-002](0002-dos-modos.md) | Simulador y juego comparten mundo y reglas | Alcance solicitado; diseño inicial adoptado | Pendiente. |
| [ADR-003](0003-estado-y-turnos.md) | Versiones por partida/turno/fase y coordinador único | Aceptada para diseño | Pendiente. |
| [ADR-004](0004-documentacion-y-continuidad.md) | `docs/` canónico y protocolo de incorporación | Adoptada en documentación | Archivos presentes y comprobador documental. |
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
| [ADR-020](0020-planificacion-coordinada-por-snapshot.md) | Asignación conjunta por snapshot; congestión no causa desvíos por sí sola | Implementada localmente; impacto en mordidas pendiente | CAM-061/T-35, parcialmente supersedida por ADR-034; replanifica por snapshot sin inventar capacidad vial/refugio. |

| [ADR-021](0021-dificultad-inicial-demo.md) | Intensidad media inicial y dificultad configurable en la demo | Aceptada e implementada localmente | CAM-063/T-37; comparación de tres semillas, exploratoria. |
| [ADR-022](0022-organizacion-documental-por-temas.md) | Organización de `docs/` por temas con índice general | Aceptada e implementada localmente | CAM-064; rutas actualizadas y comprobador documental correcto. |
| [ADR-023](0023-configuracion-de-agentes.md) | Configuración de agentes en `.claude/` y guías por área en `.agents/` | Aceptada e implementada localmente | CAM-064; carga real en una sesión nueva pendiente de comprobar. |
| [ADR-024](0024-backend-y-frontend-por-carpeta.md) | Backend en `backend/` (src, data, scripts, tests, pyproject y entorno), frontend en `frontend/` y raíz general | Aceptada e implementada localmente | CAM-065; comandos, CI y validadores ajustados; carga del tablero pendiente de comprobar en sesión nueva. |
| [ADR-025](0025-agentes-de-proyecto-y-clean-architecture.md) | Subagentes de proyecto y Clean Architecture como destino | Aceptada para diseño; código pendiente de migrar | CAM-066; guía en `docs/arquitectura/guia-clean-architecture.md`. |
| [ADR-026](0026-aplanado-backend-y-setuptools.md) | Aplanado de `backend/src` y empaquetado con setuptools | Sustituida por ADR-027 | CAM-067 (parte estructural revertida en CAM-069). |
| [ADR-027](0027-reversion-del-aplanado-de-backend.md) | Reversión del aplanado: `backend/src/navira/` y hatchling (sustituye a ADR-026) | Aceptada e implementada localmente | CAM-069; 178 pruebas; CI remota no ejecutada. |
| [ADR-028](0028-configuracion-de-seguridad-inyectada.md) | Configuración de seguridad leída una vez en `main.py` e inyectada (`ConfiguracionSeguridad`) | Aceptada e implementada localmente | CAM-071; 181 pruebas; rotar clave o flags exige reiniciar. |
| [ADR-029](0029-cobertura-y-rutas-mapa-ampliado.md) | Envolvente OSM de Manta y rutas compartidas por snapshot | Aceptada e implementada localmente; auditoría territorial pendiente | CAM-073/T-38; cobertura municipal y SLA siguen pendientes. |
| [ADR-030](0030-ventana-urbana-zona-jugable.md) | Ventana urbana aplicada como límite topológico jugable y del selector de refugios | Aceptada e implementada localmente; revisión visual pendiente | CAM-077/T-39. |
| [ADR-031](0031-perimetro-refugios-manta.md) | Búfer topológico de una cuadra para impedir la aproximación zombie a refugios Manta | Aceptada e implementada localmente; calibración geográfica pendiente | CAM-078/T-40; P-17. |
| [ADR-032](0032-incidentes-viales-siempre-activos-en-demo.md) | Incidentes viales siempre activos y sin selector en el control local | Aceptada e implementada localmente | CAM-081/T-43; el parámetro HTTP legado se ignora. |
| [ADR-033](0033-alerta-y-cierres-aleatorios.md) | Sorteo 1–10, cierre antes de decisiones, alerta/punto y rutas actualizadas | Aceptada e implementada localmente | CAM-082/T-44; solo se publica tras aplicación. |
| [ADR-034](0034-rutas-estables-y-replanificacion-cercana.md) | Conservar ruta confirmada y replantear ante amenaza visible cercana o invalidez | Aceptada para implementación local | CAM-084; T-46 y comportamiento aún no verificados automáticamente. |
| [ADR-035](0035-flujo-evaluacion-reto.md) | Flujo de evaluación separado de demo libre, sobre el modo automático compartido | Aceptada para diseño | CAM-088; presets locales probados, campaña completa y despliegue pendientes. |

Usar [plantilla](../../metodo/plantillas/decision.md). Numeración correlativa, fecha, contexto, decisión, alternativas, consecuencias, pendientes y enlaces. No renumerar IDs ya citados. Para cambiar una decisión relevante, añadir ADR nuevo y marcar el anterior sustituido con enlace recíproco. Correcciones menores pueden aclararse sin fingir que la decisión original ya decía otra cosa.
