# SPEC-005 — AWS, evaluación y entrega

ID: SPEC-005
Estado: en-revision
Requisitos: PRD-06, PRD-07, PRD-08, TRD-02, TRD-06, TRD-08, TRD-10, TRD-11
Tareas: P0-03, P0-05, P5-01, P5-02, P5-03, P6-01, P6-02, P6-03
Pruebas: T-11, T-16, T-18, T-23, T-50
Cambio: CAM-099
Evidencia: campañas locales en [CAM-098](../../calidad/resultados/campana-reto-cam098.md) y [CAM-099](../../calidad/resultados/repeticiones-reto-cam099.md); campaña efímera Fargate en AWS en [CAM-125](../../calidad/resultados/campana-aws-cam125.md). URL pública, evaluación oficial y entrega siguen pendientes.

## Objetivo y alcance

Desplegar el sistema vigente, demostrar tres rondas y entregar evidencia defendible. Fuentes: [infraestructura](../../operacion/infraestructura.md), [seguridad](../../operacion/seguridad.md), [costos](../../operacion/costos.md), [pruebas](../../calidad/pruebas.md). No afirma acceso AWS, presupuesto creado o recursos existentes.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-005-01 | Budget/alerta comprobados, despliegue reproducible en región permitida y URL pública con salud/API/WebSocket autenticados según contrato. | T-23 |
| CA-005-02 | Ráfagas y tres rondas registran latencia cliente, errores y ciclo completo, sin ocultar preparación o timeouts; objetivos y resultados se diferencian. | T-11, T-23 |
| CA-005-03 | Configuración, versiones, eventos y resultados permiten auditar rondas automáticas separadas del juego; recuperación no duplica turnos ni finge continuidad. | T-16, T-18 |
| CA-005-04 | README, endpoint, arquitectura exportada, fuente, costos/gasto real, captura y pitch cumplen entregables con enlaces comprobados. | T-23 |

## Plan y dependencias

P0-03 Budget/permisos y P0-05 salud temprana; P5 mide, revisa seguridad y ejecuta rondas; P6 prepara evidencias y entrega. P-06/P-11 y acceso AWS son dependencias externas; el núcleo local puede avanzar. Mantener aplicación hasta pitch y registrar cualquier interrupción. Ninguna tarifa estimada se declara factura real.

La estrategia privada adoptada en [ADR-045](../../arquitectura/decisiones/0045-evaluacion-aws-privada.md) usa una tarea efímera ECS Fargate para la campaña, sin endpoint administrativo remoto. CAM-125 ejecutó R1/R2/R3 en Ohio y terminó sin errores HTTP; el cliente HTTP inicia ASGI en loopback dentro de la tarea, por lo que esas métricas no miden ALB/CloudFront ni Internet. La ráfaga HTTP remota de `/paso` sigue pendiente. No se desplegó el staging web. La cuenta denegó App Runner por política organizativa. Estado, sesión y recuperación productiva siguen siendo volátiles/no verificados.

## Verificación

Identificar origen de medición, artefacto y mapa; el reporte CAM-125 registra digest, región, escenarios, métricas y límites. Para completar SPEC-005 aún falta desplegar/validar URL pública segura, TLS, salud/API/WebSocket extremo a extremo, ráfagas remotas, verificación efectiva de Budget/gasto, recuperación y entregables. No marcar la SPEC verificada con la sola campaña efímera.
