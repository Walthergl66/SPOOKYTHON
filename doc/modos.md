# Modos de uso

Estado: alcance previsto. Arquitectura compartida: [ADR-002](decisiones/0002-dos-modos.md).

| Aspecto | Simulador | Juego |
|---|---|---|
| Control | Todos automáticos vía `/paso` | Un humano y personajes automáticos. |
| Propósito | Medir el motor y ejecutar rondas oficiales | Llevar tu personaje aleatorio a un refugio. |
| Vista | Mapa global, rutas y métricas | Personaje, vecinos, refugios y cuenta atrás. |
| Decisión | Motor | Calle elegida o espera; radio opcional. |
| Resultado | Reporte de ronda | Evacuado, mordido o partida interrumpida. |
| Medición | Métricas oficiales automáticas | Métricas de juego separadas. |

## Invariantes

Una partida tiene un modo fijo y un `runId`. Cambiar de modo inicia otra partida y no puede interrumpir una prueba por iniciativa de un visitante. Primera versión: una partida activa y un jugador humano; no prometer sesiones independientes concurrentes.

Ambos modos comparten grafo, reloj, zombies, cierres, reglas de mordida y refugios. El cliente anima posiciones confirmadas; no determina colisiones ni acelera el mundo. Los dormidos permanecen ocultos para jugador, panel y motor mientras corresponda.

## Pantalla inicial prevista

- «Simulador»: observar partida; iniciar o configurar requiere rol operador.
- «Jugar»: entrar en partida habilitada; si no existe, mostrar estado y acción permitida, sin dar permisos administrativos anónimos.
- Durante una prueba oficial, mostrar observación y explicar que el juego está temporalmente ocupado.

Controles iniciales: clic en vecino, botones con nombre de destino, Tab/Enter y «Esperar». No usar WASD sin definir cómo elegir entre vecinos de un grafo irregular. Movimiento visual con opción de reducir animación, foco visible y estados que no dependan solo de color.

## Radio y final de partida

La ayuda consulta el mismo motor sobre la información observable y muestra recomendación y motivo. No ejecuta movimientos, no garantiza supervivencia y no tiene acceso a dormidos ocultos. Al terminar, mostrar turnos, distancia, ayuda usada y motivo de finalización; reiniciar depende de los permisos del operador. Flujos: [jugador](flujos/jugador.md), [espectador](flujos/espectador.md) y [operador](flujos/operador.md).
