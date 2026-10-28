# ADR-046 — Demo pública anónima con mundos aislados

Fecha: 2026-10-28  
Estado: aceptada para implementación temporal  
Origen: solicitud del usuario para que visitantes públicos prueben Reto, Simulador y Jugar.

## Contexto

La decisión previa [ADR-045](0045-evaluacion-aws-privada.md) diseñó staging privado y excluyó los controles locales de una publicación. El usuario cambió el objetivo: una URL abierta para que cualquier persona pueda probar los tres modos. Un mundo global permitiría que visitantes reinicien o alteren la prueba de otros. Estado actual, rutas, reloj y RNG residen en memoria y dependen de un coordinador de un proceso.

## Decisión

1. Mantener el requisito de público abierto a visitantes, pero asignar un control/mundo propio a cada navegador por cookie opaca anónima `HttpOnly`, `Secure` en producción y `SameSite=Strict`.
2. Mantener un único proceso/replica y limitar sesiones simultáneas a tres por defecto. Un token aleatorio se guarda como hash SHA-256 en el registro en memoria; las acciones no reciben ni eligen `runId` de otras sesiones.
3. Expirar mundos tras 10.800 segundos de inactividad, cerrar su reloj y perder el estado al reinicio. Cookie de duración máxima de 24 horas. El frontend obtiene cookie antes de montar el dashboard.
4. Validar Origin same-host en mutaciones y WebSocket. Mantener `/paso` con API key. Nginx sirve UI y API bajo un solo origen/TLS y limita la tasa de endpoints públicos por IP.
5. Limitar instancias concurrentes conforme al cupo y mantener topes ya definidos por mundo. No usar DynamoDB/Redis en esta demo temporal ni anunciar persistencia, alta disponibilidad o seguridad contra bots sofisticados.
6. Ejecutar la instancia Lightsail temporal por tres días como máximo previsto y eliminarla al terminar; el Budget de US$10 es alerta, no hard cap.

## Alternativas

- Un mundo global compartido: rechazado porque los visitantes se interfieren entre sí.
- Abrir control local directo sin sesión: rechazado por falta de aislamiento y posibilidad de modificar estado de otros.
- Registro compartido en DB/Redis con varias réplicas: pospuesto; aporta persistencia/escala, complejidad y costo que la demo de tres días no requiere.

## Consecuencias

Las sesiones son independientes en un único proceso y se destruyen al reiniciar. Los límites reducen consumo casual, pero la URL sigue siendo pública y solicitudes automatizadas pueden consumir los cupos. La primera publicación temporal usa una Lightsail VM `medium_3_0` en Ohio, Docker/Nginx y un nombre nip.io con certificado Let's Encrypt; `nip.io` es un servicio de terceros y no un dominio del proyecto. Debe supervisarse AWS y detener/eliminar la instancia al concluir; reservar Static IP o dejar recursos auxiliares puede conservar cargos. Varios visitantes detrás de una IP pueden compartir el límite de Nginx. Una sesión activa que exceda el máximo por inactividad pierde su mundo.

La prueba ASGI cubre tres modos y aislamiento, pero la carga concurrente externa, autenticación administrativa, protección contra abuso a gran escala, durabilidad y recuperación continúan pendientes. La API conserva la key maestra en servidor; no se inyecta al bundle.

## Vínculos

[PRD-13](../../producto/PRD.md), [TRD-19](../../producto/TRD.md), [SPEC-011](../../metodo/especificaciones/SPEC-011-demo-publica-multisesion.md), [seguridad](../../operacion/seguridad.md), [infraestructura](../../operacion/infraestructura.md), [costos](../../operacion/costos.md), CAM-126.
