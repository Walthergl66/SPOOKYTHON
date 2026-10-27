# ADR-009 — WebSocket de panel con snapshots completos

Fecha: 2026-10-26  
Estado: implementada localmente; operación multi-proceso y durabilidad pendientes  
Origen: P4-02 de SPEC-003 para frescura y recuperación del panel  

## Contexto y restricciones

La aplicación actual mantiene una sola partida en un repositorio en memoria con compare-and-swap. No hay outbox transaccional ni almacenamiento durable de eventos. Un canal de deltas sin buffer perdería transiciones durante desconexiones y podría mostrar estados de partidas distintas. El panel es público y de solo lectura; no debe transportar la API key de `/paso` ni datos privados.

## Decisión

`GET /panel/estado` y `/panel/mapa` se complementan con `WS /ws/panel`. El handshake exige cabecera `Origin` del mismo host. Cada conexión publica inmediatamente una proyección observable completa; luego inspecciona la clave `(runId, snapshotVersion)` cada 250 ms y publica otra proyección completa cuando cambia. `snapshotVersion` es la secuencia por partida. Se envía `panel.latido` cada dos segundos sin cambios para que el navegador detecte datos desactualizados. El cliente descarta secuencias repetidas/antiguas de la misma partida, acepta una secuencia mayor como snapshot autoritativo completo y reconecta con espera exponencial hasta ocho segundos.

## Alternativas consideradas

- Deltas y buffer durable: no hay almacenamiento/outbox que confirme los eventos junto con el snapshot.
- Notificación en memoria desde cada CAS: exige enlazar todos los caminos de escritura y no resuelve recuperación entre procesos.
- Polling HTTP del navegador: evita el canal push, pero genera solicitudes repetidas y dificulta el estado de conexión.

## Consecuencias, límites y costos

- Una reconexión empieza con el snapshot vigente, sin solicitar deltas desde un cursor viejo; un salto de secuencia es seguro porque cada mensaje cambia el estado completo.
- El polling de 250 ms es por conexión y solo serializa la proyección cuando cambia la versión; esta primera implementación asume una tarea y un repositorio en proceso.
- Al reiniciar el proceso no se recupera estado; no se publica resultado antes de leer la versión confirmada del repositorio actual, pero este repositorio no es durable.
- El control `Origin` evita navegadores de otros sitios; no sustituye TLS, límites de conexión/frecuencia, política de red o autenticación de operador en despliegue.
- No se conserva un historial de eventos ni se afirman varios procesos, alta disponibilidad o replay durable.

## Supuestos y pendientes relacionados

Persistencia durable, outbox/eventos por turno, cuotas y límites por conexión se mantienen pendientes para la fase de infraestructura. Véanse [contrato de eventos](../contratos/eventos.md), [seguridad](../../operacion/seguridad.md), P4-02 y pendientes P-07/P-09.

## Documentos y módulos propietarios afectados

`src/navira/api/routes.py`, `src/navira/application/consultar_panel.py`, `frontend/src/shared/realtime/panel.ts` y el flujo del espectador.

## Evidencia de implementación/verificación

CAM-032: pruebas ASGI de snapshot inicial, cambio de versión, heartbeat, rechazo cross-origin y reconexión desde una versión posterior; suite frontend de producción compilada. No acredita transporte desplegado ni recuperación entre procesos.
