# ADR-015 — Control local y explícito de demos del simulador

Fecha: 2026-10-26
Estado: aceptada e implementada localmente en CAM-050
Origen: el usuario reportó que el frontend no permitía iniciar la simulación y pidió adaptar el diseño al tablero de referencia.

## Contexto

El frontend era una portada de selección/vista previa. El backend ordinario no tenía partida y el ejecutor automático existía como caso de uso/CLI, no como reloj controlable desde esa pantalla. Los contratos administrativos productivos requieren autorización propia y no deben exponer una API key maestra en el navegador.

## Decisión

Añadir un control de demo local activado solo por `NAVIRA_LOCAL_DEMO_CONTROL=1`. Bajo ese ensamblaje, el operador local puede configurar escenario sintético y población, iniciar, pausar, continuar y reiniciar. Un reloj local ejecuta la ronda automática a período nominal de dos segundos; el backend sigue siendo autoridad del turno, resolutor, posición y snapshots. Los controles POST exigen conexión loopback y que Origin/Host usen alias locales permitidos (`localhost`, `127.0.0.1`, `::1`). Sin el flag las rutas responden 404.

El frontend cambia a un tablero con el mapa como superficie principal, controles a la izquierda, cifras confirmadas y refugios del fixture a la derecha, y una secuencia derivada de snapshots recibidos. El control local usa por defecto el fixture parcial Manta, no el fixture topológico de cinco nodos; `NAVIRA_DEMO_MAP` permite elegir otro. Los valores sin evidencia aparecen como `—`; el mapa parcial no se presenta como navegación de emergencia ni acredita seguridad ante sismos.

## Alternativas

- Mantener botón de inicio deshabilitado porque no existe operador productivo: no resuelve el recorrido local de demo solicitado.
- Insertar una API key administrativa en JavaScript: rechazado porque expone una credencial privilegiada.
- Habilitar control anónimo general: rechazado; solo se acepta el opt-in local y loopback.
- Cambiar el juego humano o el contrato `/paso`: fuera de esta tarea, no es necesario para iniciar el simulador automático.

## Consecuencias y límites

La demo local ahora es operable desde el frontend y crea un run nuevo con aleatoriedad nueva cuando no se aporta semilla. El estado se pierde al apagar el proceso y el runner no prueba la cadencia sostenida, recuperación, AWS ni seguridad productiva. No configurar el flag en despliegue; cualquier panel de operador público necesita autenticación, autorización, TLS y auditoría independientes.

Documentos propietarios: [SPEC-007](../../metodo/especificaciones/SPEC-007-panel-operador-local.md), [API](../contratos/api.md), [seguridad](../../operacion/seguridad.md), [módulos frontend](../modulos/frontend.md), [plan](../../seguimiento/plan-implementacion.md) y [cambio CAM-050](../../seguimiento/cambios.md).
