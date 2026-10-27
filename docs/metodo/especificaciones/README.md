# Especificaciones funcionales y de cambios

Cada SPEC detalla aceptación y enlaza requisitos del [PRD](../../producto/PRD.md)/[TRD](../../producto/TRD.md), tareas existentes y pruebas. Método: [SDD](../SDD.md). Las fuentes especializadas siguen definiendo reglas y contratos; no mantener copias divergentes aquí.

| ID | Funcionalidad | Situación inicial |
|---|---|---|
| [SPEC-001](SPEC-001-mundo-simulacion.md) | Grafo, mundo y simulación | CAM-057 implementa parcialmente intensidad sintética por sectores, replay y cierres viales de demo; CAM-082 agrega sorteo 1–10, alerta y recálculo (T-44). P-07/P-09 y verificación integral siguen pendientes. |
| [SPEC-002](SPEC-002-motor-paso.md) | Motor, `/paso` y mejora temporal | CAM-033/034 implementan núcleo temporal y pronóstico; CAM-058 activa riesgo-primero; CAM-059 agrega cruces futuros, escape inmediato y correspondencia panel/acción (T-31/T-32/T-33); CAM-060 impide que evacuados vuelvan a ser mordidos (T-34). T-11/T-22, integración de producción y verificación integral siguen pendientes. |
| [SPEC-003](SPEC-003-panel-vivo.md) | Observación en vivo | Lista; CAM-031 verifica mapa/proyección manual, CAM-032 transporte local con snapshots completos/heartbeat/reconexión, CAM-079 conserva la interpolación ante snapshots sin movimiento nuevo y CAM-082/083 agregan alerta vial y detalle de sobreviviente/ruta por selección (T-44/T-45). CA-003-01/03/04 y validación integral siguen pendientes. |
| [SPEC-004](SPEC-004-juego-humano.md) | Control humano | CAM-036/037 implementan parcialmente sesión/aparición y órdenes locales; CAM-038 inicia controles frontend; CAM-039/040 integran ciclo demo; CAM-041/042 muestran timer y radio; CAM-043 recupera sesión tras recarga; CAM-045 mejora navegación/foco; CAM-046 implementa expiración local sin transferir personaje y CAM-047 verifica parte de navegación por teclado. Falta persistencia/reinicio, revocación productiva, TLS, resultado y T-14/T-15/T-19 integral. |
| [SPEC-005](SPEC-005-aws-evaluacion.md) | AWS, evaluación y entrega | Lista con dependencias externas pendientes. |
| [SPEC-006](SPEC-006-metodologia.md) | Incorporación PRD/TRD/ODDD/SDD | Ver estado y evidencia en su archivo. |
| [SPEC-007](SPEC-007-panel-operador-local.md) | Panel de simulación con control local de demo | CAM-050/063/079/081/082 y T-26/37/41/43/44 verifican control local, velocidad, continuidad visual, incidentes siempre activos y alerta cartográfica; no habilita operaciones públicas ni despliegue. |
| [SPEC-008](SPEC-008-mapa-cartografico-3d.md) | Mapa cartográfico real con vista 3D y actores animados | CAM-077 convierte la ventana urbana en límite jugable y restringe el selector (T-39). El fixture fuente OSM ampliado se conserva; cobertura, payload y fallback de proveedor mantienen sus límites documentados. |

## Uso

Elegir la SPEC relacionada con la tarea, revisar sus pendientes y criterios, implementar el paso autorizado y registrar resultados reales. Estado `lista` no significa implementada ni da autorización para desplegar/publicar. Para cambios pequeños usar el flujo reducido; para cambios nuevos usar [plantilla](../plantillas/especificacion.md).

Mantener IDs estables, actualizar este índice al añadir una SPEC y enlazar el requisito en [trazabilidad](../trazabilidad.md). No marcar toda una funcionalidad verificada porque se completó una tarea parcial.
