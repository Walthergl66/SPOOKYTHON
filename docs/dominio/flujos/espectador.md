# Flujo del espectador

Estado: en CAM-032 se añade `WS /ws/panel` de snapshots completos, consulta por versión y heartbeat. El espectador observa ambos modos y no modifica la partida; la fuente sigue siendo un repositorio local en memoria.

1. Abrir el panel y obtener estado en `/panel/estado`; si hay una partida activa, obtener el mapa versionado por `/panel/mapa`.
2. Al conectar, recibir snapshot completo y mostrar estado, turno, fase, versión, modo y `emitidoEn` UTC del servidor; heartbeat sin cambios distingue conexión viva de una vista que dejó de recibir datos.
3. Suscribirse a `WS /ws/panel`; descartar secuencias repetidas/antiguas de la misma partida. Los mensajes son snapshots completos, así que se puede aceptar un salto de versión y recuperar la última vista sin aplicar deltas faltantes.
4. Actualizar capas del mapa, cierres, hordas, sobrevivientes y refugios. Los dormidos sin activar no aparecen.
5. Seleccionar un sobreviviente para ver su ruta prevista y la razón disponible; distinguir una predicción de un movimiento confirmado.
6. Ver métricas de la modalidad correspondiente, sin presentar juego humano como evaluación del motor.
7. La consulta manual sigue disponible como respaldo. Ante cierre, mostrar reconexión; el cliente vuelve a conectar con espera exponencial y el servidor entrega estado vigente de nuevo. No se detiene el mundo durante la desconexión.

No exponer API keys, cookies ajenas, estado aleatorio o datos privados. No ofrecer botones administrativos activos sin autorización. Reflejar «sin partida», «en curso», «finalizada» e «interrumpida» como estados diferentes. En el simulador automático, el panel mantiene una ruta prevista para cada sobreviviente activo en cualquier fase del turno para que la selección sea útil mientras corre la ronda; en juego humano, solo publica rutas durante la fase de decisiones. P4-02 no incluye outbox, historial durable, varios workers, cuotas ni despliegue; revisar ADR-009 antes de cambiar el transporte.
