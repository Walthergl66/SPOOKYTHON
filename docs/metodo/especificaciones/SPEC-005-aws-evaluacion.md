# SPEC-005 — AWS, evaluación y entrega

ID: SPEC-005
Estado: lista
Requisitos: PRD-06, PRD-07, PRD-08, TRD-02, TRD-06, TRD-08, TRD-10, TRD-11
Tareas: P0-03, P0-05, P5-01, P5-02, P5-03, P6-01, P6-02, P6-03
Pruebas: T-11, T-16, T-18, T-23
Cambio: CAM-087
Evidencia: parcial; la ventana de duración del evaluador local se conserva tras cierre temprano, pero las rondas oficiales, carga continua, AWS y entregables siguen pendientes.

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

## Verificación

Identificar origen de medición, revisión de código, versión mapa y escenario en cada reporte. Verificar permisos y TLS, contar errores y limitar retención sin perder evidencia. No hay pruebas de AWS ejecutadas. Cualquier parte no comprobada queda pendiente aun si CloudFormation existe.
