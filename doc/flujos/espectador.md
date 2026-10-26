# Flujo del espectador

Estado: diseño previsto. El espectador observa ambos modos y no modifica la partida.

1. Abrir el panel y obtener mapa y proyección pública mediante las rutas de lectura del panel.
2. Mostrar estado de partida, turno, fecha de última actualización y conexión.
3. Suscribirse a WebSocket y descartar mensajes repetidos o antiguos según partida y secuencia.
4. Actualizar capas del mapa, cierres, hordas, sobrevivientes y refugios. Los dormidos sin activar no aparecen.
5. Seleccionar un sobreviviente para ver su ruta prevista y la razón disponible; distinguir una predicción de un movimiento confirmado.
6. Ver métricas de la modalidad correspondiente, sin presentar juego humano como evaluación del motor.
7. Si se pierde conexión, marcar datos como desactualizados. Al volver, descargar instantánea completa y reanudar eventos.

No exponer API keys, cookies ajenas, estado aleatorio o datos privados. No ofrecer botones administrativos activos sin autorización. Reflejar «sin partida», «en curso», «finalizada» e «interrumpida» como estados diferentes. No reconstruir el mapa completo por cada evento.
