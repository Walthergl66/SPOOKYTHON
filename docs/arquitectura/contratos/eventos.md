# Eventos de tiempo real

Estado: `WS /ws/panel` implementado localmente en CAM-032 para snapshots observables completos y heartbeat. El contrato de eventos de turno/jugador de esta sección sigue previsto; cierres programados y snapshots se confirman actualmente en memoria, no en almacenamiento durable.

## Sobre común

```json
{
  "schemaVersion":1,
  "tipo":"turno.resuelto",
  "runId":"juego-001",
  "secuencia":32,
  "turno":12,
  "fase":"resuelto",
  "emitidoEn":"2026-10-26T16:00:00Z",
  "datos":{}
}
```

`secuencia` es creciente por partida, independiente del número de turno; hay varios eventos por turno. El cliente no usa timestamps como criterio único de orden. La fase distingue estado tras mover zombies de resultado tras mover sobrevivientes.

| Evento | Destinatario | Contenido |
|---|---|---|
| `partida.iniciada` | Observadores | Modo, versiones y estado inicial permitido. |
| `turno.abierto` | Observadores/jugador | Instantánea observable de decisión y `cierreAccionesEn` en juego. |
| `orden.recibida` | Solo sesión propietaria | Acuse, ID y secuencia de orden; no otra cookie o token. |
| `turno.resuelto` | Observadores | Posiciones finales, mordidas, llegadas, cierres y métricas. |
| `partida.finalizada` | Observadores | Motivo, clasificación y resumen de resultados. |
| `partida.interrumpida` | Observadores | Interrupción explícita, sin afirmar continuación. |

### Canal implementado del panel

El endpoint `WS /ws/panel` es de solo lectura y valida `Origin` contra el host de la solicitud. El servidor entrega un `panel.snapshot` inmediatamente tras aceptar la conexión, luego resuelve el proveedor de panel vigente y consulta la clave confirmada `(runId, snapshotVersion)` cada 250 ms; publica un nuevo snapshot completo al cambiar. Volver a resolver el proveedor permite que una conexión abierta siga la partida que el control local crea o reinicia. `secuencia` usa el `snapshotVersion` de esa partida. Si todavía no hay partida, el snapshot lleva `runId: null`, `secuencia: 0`, `fase: "sin_partida"` y `datos: {"estado":"sin_partida"}`. `emitidoEn` es fecha UTC del servidor.

```json
{
  "schemaVersion": 1,
  "tipo": "panel.snapshot",
  "runId": "juego-001",
  "secuencia": 32,
  "turno": 12,
  "fase": "resuelta",
  "emitidoEn": "2026-10-26T16:00:00Z",
  "datos": {"estado": "activa", "runId": "juego-001", "snapshotVersion": 32}
}
```

Cada dos segundos sin cambios el servidor publica `panel.latido` con `schemaVersion`, `runId`, `secuencia` y `emitidoEn`; no incluye estado adicional. El cliente descarta secuencias repetidas o antiguas de la misma partida. Las secuencias mayores se aceptan porque cada `panel.snapshot` reemplaza el estado completo, no es un delta. Un cambio de `runId` reemplaza toda la partida anterior. Después de reconectar siempre llega primero el snapshot vigente, por lo que no existe hueco de suscripción que requiera replay de deltas. El cliente muestra reconexión/desactualización y reintenta con backoff exponencial.

CAM-057 añade `datos.eventosCiudad`: lista de cierres viales que el coordinador ya aplicó, con ID, turno y causa genérica. CAM-082 añade `segmentoId`, `lat` y `lng` del punto medio del segmento cerrado para ubicar el marcador y la alerta. La cantidad (1–10) y el calendario futuros permanecen privados; los eventos programados nunca se filtran al panel antes de su aplicación. La publicación coincide con un snapshot cuya planificación ya excluye el segmento.

En un snapshot de juego, `datos.decisionRestanteMs` es el restante estimado al proyectar el estado. Solo alimenta el contador visual; el reloj del navegador no es autoridad. La acción vuelve a validar el deadline monotónico bajo la puerta compartida y puede rechazarse si vence durante el envío.

Esta proyección no implementa el catálogo de eventos de partida/jugador de arriba, ni historial, replay durable, límites de conexión o coordinación multi-proceso. La estrategia es válida para el repositorio de una tarea local; una futura publicación durable requiere ordenar la confirmación del evento con la persistencia del snapshot.

## Reanudación

1. Obtener instantánea completa con `runId`, fase y última secuencia confirmada.
2. Abrir suscripción vinculada a esa versión y recibir eventos posteriores; el servidor debe evitar el hueco entre descargar y suscribirse mediante cursor/buffer o reenviando otra instantánea.
3. Descartar duplicados y mensajes de partidas anteriores. Ante salto de secuencia o cambio de partida, solicitar nueva instantánea.
4. Mostrar desconexión y última actualización; no simular que sigue conectado.

Primera versión puede publicar instantáneas completas por turno para simplificar consistencia; validar tamaño y costo antes de adoptar deltas. Nunca publicar antes de confirmar persistencia. La reconexión no pausa la partida ni revive al jugador.
