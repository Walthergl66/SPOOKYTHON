# Modos de uso

Estado: los modos de dominio `simulador` y `juego` se mantienen; la interfaz ofrece demo libre, flujo de reto y juego humano. «Reto» usa partidas automáticas de modo `simulador`; no crea un tercer modo de dominio. El control local continúa protegido por opt-in y loopback. Arquitectura compartida: [ADR-002](../arquitectura/decisiones/0002-dos-modos.md), [ADR-035](../arquitectura/decisiones/0035-flujo-evaluacion-reto.md).

| Aspecto | Simulador | Juego |
|---|---|---|
| Control | Todos automáticos vía `/paso` | Un humano y personajes automáticos. |
| Propósito | Medir el motor y ejecutar rondas oficiales | Llevar tu personaje aleatorio a un refugio. |
| Vista | Mapa global, rutas y métricas | Personaje, vecinos, refugios y cuenta atrás. |
| Decisión | Motor | Calle elegida o espera; radio opcional. |
| Resultado | Reporte de ronda | Evacuado, mordido o partida interrumpida. |
| Medición | Métricas oficiales automáticas | Métricas de juego separadas. |

La interfaz añade **Reto** con presets de Anochecer (20), Medianoche (80) y Apocalipsis (200). En el fixture Manta sus habitantes aparecen aleatoriamente en las zonas aproximadas de Tarqui, Los Esteros, Barbasquillo y Jocay, con un reparto equilibrado y reproducible por semilla. Las amenazas del Reto concentran una cuota provisional del 80% de cada tipo dentro de 3,5 km del ancla de Parque La Dolorosa y los eventos prefieren calles de esa área; queda una parte fuera para cubrir la ciudad. Simulador libre conserva sus apariciones y selección globales. Se usan el mismo motor, mapa y resolutor; cada ronda puede reiniciarse desde el panel y aún no se automatiza la campaña consecutiva de 15 minutos. Densidad, proporciones de tipos, radio, geometría/cuota exacta de sectores y turnos de evento son provisionales porque el enunciado no los especifica. Véanse [ADR-037](../arquitectura/decisiones/0037-spawn-reto-cuatro-sectores.md), [ADR-038](../arquitectura/decisiones/0038-foco-amenazas-reto.md) y [ADR-039](../arquitectura/decisiones/0039-reinicio-ronda-reto.md).

## Invariantes

Una partida tiene un modo fijo y un `runId`. Cambiar de modo inicia otra partida y no puede interrumpir una prueba por iniciativa de un visitante. Primera versión: una partida activa y un jugador humano; no prometer sesiones independientes concurrentes.

Ambos modos comparten grafo, reloj, zombies, cierres, reglas de mordida y refugios. El cliente anima posiciones confirmadas; no determina colisiones ni acelera el mundo. Los dormidos permanecen ocultos para jugador, panel y motor mientras corresponda.

En la demo del mapa Manta, ambos modos comparten el subgrafo urbano limitado por la caja de [ADR-030](../arquitectura/decisiones/0030-ventana-urbana-zona-jugable.md); no aparecen personajes o amenazas fuera de ella. Los mapas sintéticos conservan sus propios límites.

## Pantalla inicial prevista

- «Simulador»: demo libre; observar/iniciar o configurar requiere el control local de operador.
- «Reto»: presets de evaluación automática; los parámetros no definidos por el reto se muestran como provisionales.
- «Jugar»: entrar en partida habilitada; si no existe, mostrar estado y acción permitida, sin dar permisos administrativos anónimos.
- Durante una prueba oficial, mostrar observación y explicar que el juego está temporalmente ocupado.

Controles iniciales: clic en vecino, botones con nombre de destino, Tab/Enter y «Esperar». No usar WASD sin definir cómo elegir entre vecinos de un grafo irregular. Movimiento visual con opción de reducir animación, foco visible y estados que no dependan solo de color.

La demo sintética local tiene un control explícito de desarrollo, no un endpoint administrativo público. Se activa con `NAVIRA_LOCAL_DEMO_CONTROL=1`; el backend limita las operaciones a loopback y origen same-host. Despliegues no deben configurar este opt-in.

## Radio y final de partida

La ayuda consulta el mismo motor sobre la información observable y muestra recomendación y motivo. No ejecuta movimientos, no garantiza supervivencia y no tiene acceso a dormidos ocultos. Al terminar, mostrar turnos, distancia, ayuda usada y motivo de finalización; reiniciar depende de los permisos del operador. Flujos: [jugador](flujos/jugador.md), [espectador](flujos/espectador.md) y [operador](flujos/operador.md).
