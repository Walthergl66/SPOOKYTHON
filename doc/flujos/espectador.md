# Flujo del espectador

Estado: consulta HTTP de mapa/snapshot implementada parcialmente; WebSocket y recuperación siguen previstos. El espectador observa ambos modos y no modifica la partida.

1. Abrir el panel y obtener estado en `/panel/estado`; si hay una partida activa, obtener el mapa versionado por `/panel/mapa`.
2. Mostrar estado de partida, turno, fase, versión de snapshot/mapa, modo y hora local de consulta; la hora local no es un timestamp de confirmación del servidor.
3. Suscribirse a WebSocket y descartar mensajes repetidos o antiguos según partida y secuencia.
4. Actualizar capas del mapa, cierres, hordas, sobrevivientes y refugios. Los dormidos sin activar no aparecen.
5. Seleccionar un sobreviviente para ver su ruta prevista y la razón disponible; distinguir una predicción de un movimiento confirmado.
6. Ver métricas de la modalidad correspondiente, sin presentar juego humano como evaluación del motor.
7. En CAM-031, el usuario puede solicitar una nueva consulta manual. La reconexión automática, marca de datos desactualizados por heartbeat y reanudación de eventos quedan para P4-02.

No exponer API keys, cookies ajenas, estado aleatorio o datos privados. No ofrecer botones administrativos activos sin autorización. Reflejar «sin partida», «en curso», «finalizada» e «interrumpida» como estados diferentes. No reconstruir el mapa completo por cada evento.
