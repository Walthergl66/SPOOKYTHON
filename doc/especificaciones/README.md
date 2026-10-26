# Especificaciones funcionales y de cambios

Cada SPEC detalla aceptación y enlaza requisitos del [PRD](../PRD.md)/[TRD](../TRD.md), tareas existentes y pruebas. Método: [SDD](../SDD.md). Las fuentes especializadas siguen definiendo reglas y contratos; no mantener copias divergentes aquí.

| ID | Funcionalidad | Situación inicial |
|---|---|---|
| [SPEC-001](SPEC-001-mundo-simulacion.md) | Grafo, mundo y simulación | En curso; generador local estocástico parcial, no verificada integralmente. |
| [SPEC-002](SPEC-002-motor-paso.md) | Motor, `/paso` y mejora temporal | CAM-033/034 implementan núcleo temporal y pronóstico exploratorio; CAM-035 evalúa 27 pares locales y mantiene Dijkstra activa; CAM-044 mide una pasada HTTP local que acaba antes de 150 turnos. T-11/T-22, integración de producción y verificación integral siguen pendientes. |
| [SPEC-003](SPEC-003-panel-vivo.md) | Observación en vivo | Lista; CAM-031 verifica mapa/proyección manual y CAM-032 transporte local con snapshots completos, heartbeat y reconexión. CA-003-01/03/04 y validación integral siguen pendientes. |
| [SPEC-004](SPEC-004-juego-humano.md) | Control humano | CAM-036/037 implementan parcialmente sesión/aparición y órdenes locales; CAM-038 inicia controles frontend; CAM-039/040 integran ciclo demo; CAM-041/042 muestran timer y radio; CAM-043 recupera sesión tras recarga; CAM-045 mejora navegación/foco; CAM-046 implementa expiración local sin transferir personaje y CAM-047 verifica parte de navegación por teclado. Falta persistencia/reinicio, revocación productiva, TLS, resultado y T-14/T-15/T-19 integral. |
| [SPEC-005](SPEC-005-aws-evaluacion.md) | AWS, evaluación y entrega | Lista con dependencias externas pendientes. |
| [SPEC-006](SPEC-006-metodologia.md) | Incorporación PRD/TRD/ODDD/SDD | Ver estado y evidencia en su archivo. |
| [SPEC-007](SPEC-007-panel-operador-local.md) | Panel de simulación con control local de demo | Verificado localmente con CAM-050 y T-26; no habilita operaciones públicas ni despliegue. |
| [SPEC-008](SPEC-008-mapa-cartografico-3d.md) | Mapa cartográfico real con vista 3D | Implementada, no verificada de extremo a extremo — CAM-051/T-27; falta prueba de falla controlada y medir cobertura del proveedor. |

## Uso

Elegir la SPEC relacionada con la tarea, revisar sus pendientes y criterios, implementar el paso autorizado y registrar resultados reales. Estado `lista` no significa implementada ni da autorización para desplegar/publicar. Para cambios pequeños usar el flujo reducido; para cambios nuevos usar [plantilla](../plantillas/especificacion.md).

Mantener IDs estables, actualizar este índice al añadir una SPEC y enlazar el requisito en [trazabilidad](../trazabilidad.md). No marcar toda una funcionalidad verificada porque se completó una tarea parcial.
