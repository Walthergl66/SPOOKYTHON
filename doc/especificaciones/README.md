# Especificaciones funcionales y de cambios

Cada SPEC detalla aceptación y enlaza requisitos del [PRD](../PRD.md)/[TRD](../TRD.md), tareas existentes y pruebas. Método: [SDD](../SDD.md). Las fuentes especializadas siguen definiendo reglas y contratos; no mantener copias divergentes aquí.

| ID | Funcionalidad | Situación inicial |
|---|---|---|
| [SPEC-001](SPEC-001-mundo-simulacion.md) | Grafo, mundo y simulación | En curso; generador local estocástico parcial, no verificada integralmente. |
| [SPEC-002](SPEC-002-motor-paso.md) | Motor, `/paso` y mejora temporal | Lista con referencia base antes de predicción. |
| [SPEC-003](SPEC-003-panel-vivo.md) | Observación en vivo | Lista; CAM-030 agrega scaffold y CAM-031 verifica P4-01 manual. P4-02 y criterios de sincronización siguen pendientes. |
| [SPEC-004](SPEC-004-juego-humano.md) | Control humano | Lista con supuestos de sesión explícitos. |
| [SPEC-005](SPEC-005-aws-evaluacion.md) | AWS, evaluación y entrega | Lista con dependencias externas pendientes. |
| [SPEC-006](SPEC-006-metodologia.md) | Incorporación PRD/TRD/ODDD/SDD | Ver estado y evidencia en su archivo. |

## Uso

Elegir la SPEC relacionada con la tarea, revisar sus pendientes y criterios, implementar el paso autorizado y registrar resultados reales. Estado `lista` no significa implementada ni da autorización para desplegar/publicar. Para cambios pequeños usar el flujo reducido; para cambios nuevos usar [plantilla](../plantillas/especificacion.md).

Mantener IDs estables, actualizar este índice al añadir una SPEC y enlazar el requisito en [trazabilidad](../trazabilidad.md). No marcar toda una funcionalidad verificada porque se completó una tarea parcial.
