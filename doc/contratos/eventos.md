# Eventos de tiempo real

Estado: transporte WebSocket y proyecciones siguen previstos; los cierres de ciudad programados y su aplicación al snapshot en memoria ya están en `simulation/coordinador.py`. Los eventos públicos usan exclusivamente proyección observable.

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

## Reanudación

1. Obtener instantánea completa con `runId`, fase y última secuencia confirmada.
2. Abrir suscripción vinculada a esa versión y recibir eventos posteriores; el servidor debe evitar el hueco entre descargar y suscribirse mediante cursor/buffer o reenviando otra instantánea.
3. Descartar duplicados y mensajes de partidas anteriores. Ante salto de secuencia o cambio de partida, solicitar nueva instantánea.
4. Mostrar desconexión y última actualización; no simular que sigue conectado.

Primera versión puede publicar instantáneas completas por turno para simplificar consistencia; validar tamaño y costo antes de adoptar deltas. Nunca publicar antes de confirmar persistencia. La reconexión no pausa la partida ni revive al jugador.
