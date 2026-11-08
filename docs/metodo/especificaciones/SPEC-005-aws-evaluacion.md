# SPEC-005 — AWS, evaluación y entrega

ID: SPEC-005
Estado: sustituida
Requisitos: PRD-06, PRD-07, PRD-08, TRD-02, TRD-06, TRD-08, TRD-10, TRD-11
Tareas: P0-03, P0-05, P5-01, P5-02, P5-03, P6-01, P6-02, P6-03
Pruebas: T-11, T-16, T-18, T-23, T-50
Cambio: CAM-161
Evidencia: campañas locales en [CAM-098](../../calidad/resultados/campana-reto-cam098.md) y [CAM-099](../../calidad/resultados/repeticiones-reto-cam099.md); campaña efímera Fargate ejecutada históricamente en [CAM-125](../../calidad/resultados/campana-aws-cam125.md); demo Lightsail y smoke HTTPS histórico CAM-126..128/CAM-158. El uso de AWS y su workflow se retiraron en CAM-161/ADR-055. Esta SPEC ya no autoriza ni instruye aprovisionamiento AWS; la topología pública actual vive en SPEC-011. El estado de recursos AWS remotos queda desconocido (P-25).

## Objetivo y alcance

La intención original de evaluación/entrega y sus criterios técnicos se conservan como referencia histórica. La parte específica de AWS quedó sustituida por CAM-161/ADR-055; la medición externa que aún sea necesaria se debe ejecutar sobre la topología activa Vercel + Render y documentar en la tarea correspondiente. Fuentes vigentes: [infraestructura](../../operacion/infraestructura.md), [seguridad](../../operacion/seguridad.md), [costos](../../operacion/costos.md), [pruebas](../../calidad/pruebas.md) y [SPEC-011](SPEC-011-demo-publica-multisesion.md).

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-005-01 | Budget/alerta comprobados, despliegue reproducible en región permitida y URL pública con salud/API/WebSocket autenticados según contrato. | T-23 |
| CA-005-02 | Ráfagas y tres rondas registran latencia cliente, errores y ciclo completo, sin ocultar preparación o timeouts; objetivos y resultados se diferencian. | T-11, T-23 |
| CA-005-03 | Configuración, versiones, eventos y resultados permiten auditar rondas automáticas separadas del juego; recuperación no duplica turnos ni finge continuidad. | T-16, T-18 |
| CA-005-04 | README, endpoint, arquitectura exportada, fuente, costos/gasto real, captura y pitch cumplen entregables con enlaces comprobados. | T-23 |

## Plan y dependencias

Este plan de tareas es histórico para despliegues AWS. La estrategia vigente se describe en ADR-054/055. Los requisitos de evaluación de rendimiento todavía pueden aplicar, pero no implican AWS ni despliegue AWS. Ninguna tarifa estimada se declara factura real.

Históricamente, [ADR-045](../../arquitectura/decisiones/0045-evaluacion-aws-privada.md) usó una tarea efímera Fargate; CAM-125 ejecutó R1/R2/R3 en Ohio con HTTP loopback. La demo pública de [ADR-046](../../arquitectura/decisiones/0046-demo-publica-multisesion.md) fue desplegada en Lightsail y comprobada por HTTPS CAM-126..128/CAM-158. ADR-047/050 registran un CD Lightsail planeado, no exitoso. Estos hechos no describen infraestructura activa ni su estado remoto actual.

## Verificación

La campaña CAM-125 es evidencia histórica, no evaluación de la topología vigente. No completar ni reactivar esta SPEC AWS. Los criterios de rendimiento, recuperación y entrega que sigan vigentes se deben trazar a requisitos y trabajo nuevos sobre el hosting activo; recursos/cargos AWS siguen en P-25.
