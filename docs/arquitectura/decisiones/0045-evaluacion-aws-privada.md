# ADR-045 — Evaluación AWS privada sin exponer controles locales

Fecha: 2026-10-28  
Estado: aceptada para diseño  
Origen: Fase 2 de la guía de despliegue de Navira.

## Contexto y restricciones

- `POST /paso` conserva su contrato y exige `x-api-key`; sin clave configurada responde 503 y una clave incorrecta responde 401.
- Los controles de Simulador, Reto y Juego son locales y opt-in. Sin opt-in responden 404; con opt-in exigen loopback y origen local.
- Estado, sesiones y coordinador son volátiles y de un proceso. Un reinicio no restaura la ronda.
- El evaluador actual ejecuta una campaña R1/R2/R3 completa, pero levanta su servidor ASGI loopback. No permite controlar el mundo de un servicio desplegado de forma remota.

## Decisión

1. El primer staging será privado, restringido por red a las direcciones de origen autorizadas del equipo, y `/paso` seguirá exigiendo API key. No se publicarán controles locales, rutas de operador ni la clave maestra en el frontend.
2. La campaña completa en AWS se ejecutará como tarea efímera ECS Fargate desde el mismo SHA/digest de imagen que se evalúa. Ejecutará `python -m navira.evaluacion_local --campana-reto`, sin listener público ni permisos para mutar el servicio de staging.
3. La ráfaga HTTP remota al staging será una medición separada usando `python -m navira.carga_http --url <URL-privada>/paso`; la clave se obtendrá desde configuración segura, no desde argumentos visibles, frontend o documentación.
4. Cada servicio/tarea mantiene un solo coordinador. `desiredCount` del servicio es 1; no se habilita autoscaling del motor.
5. Staging es volátil y apto solo para smoke: cualquier reinicio interrumpe e invalida el run y exige crear un `runId` nuevo. No se declara recuperación. No ejecutar la campaña completa sobre ese run hasta implementar persistencia/recuperación o demostrar una política equivalente.
6. La campaña Fargate mide el artefacto ejecutado en AWS, pero su HTTP usa loopback dentro de la tarea. No mide latencia de navegador, CloudFront, ALB ni el recorrido de red del endpoint desplegado; reportar esas mediciones por separado.

## Alternativas consideradas

- Añadir endpoints públicos de inicio, pausa, avance o campaña: rechazado porque transformaría el control local en interfaz administrativa remota.
- Reutilizar `/paso` para dirigir una campaña remota completa: insuficiente; esa ruta calcula una decisión, pero no autoriza al cliente a modificar o avanzar el mundo.
- Ejecutar una campaña sobre staging volátil y declararla recuperación: rechazado porque el reinicio pierde el mundo y no existe restauración durable.

## Consecuencias, límites y costos

- La tarea y el servicio son procesos separados; cada reporte identifica SHA/digest, región y tarea.
- Ocultar una URL no la vuelve privada; las restricciones deben materializarse en red/autenticación.
- El costo debe incluir las horas de campaña, logs y salida de red; recalcular para `us-east-2` antes de crear recursos.
- La Fase 3 debe implementar y verificar topología, configuración, imagen y tarea. Esta ADR no crea recursos ni constituye medición AWS.

## Pendientes relacionados

- P-06: cuenta/permisos y región de recursos; `us-east-2` fue elegida por el usuario.
- P-11: TLS extremo a extremo, dominio/certificado y restricción del origen.
- P-12/P-16: recuperación durable y coordinación multiproceso para operación de juego.
- P-19: aceptar límites de campaña Fargate loopback y validar por separado tráfico remoto.

## Documentos propietarios afectados

[SPEC-005](../../metodo/especificaciones/SPEC-005-aws-evaluacion.md), [guía de despliegue](../../operacion/guia-paso-a-paso-despliegue.md), [infraestructura](../../operacion/infraestructura.md), [seguridad](../../operacion/seguridad.md), [costos](../../operacion/costos.md), [pendientes](../../seguimiento/pendientes.md).

## Evidencia

Diseño registrado en CAM-113. Se deben volver a ejecutar las pruebas existentes de API key y de controles locales al verificar CAM-113. No hay despliegue AWS ni reporte AWS asociado a esta decisión.
