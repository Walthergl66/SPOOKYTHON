# Modos de uso

Estado: los modos de dominio `simulador` y `juego` se mantienen; la interfaz ofrece Reto, Simulador y Juego de operador. «Reto» es una evaluación automática, «Simulador» configura/observa una demo libre y «Jugar» permite intervenir una demo automática local mientras avanza. El modo operador no crea un tercer modo de dominio. Las API de personaje humano aún existen, pero ya no se enlazan desde el Jugar principal. Arquitectura compartida: [ADR-002](../arquitectura/decisiones/0002-dos-modos.md), [ADR-035](../arquitectura/decisiones/0035-flujo-evaluacion-reto.md) y [ADR-042](../arquitectura/decisiones/0042-juego-operador-mundo-interactivo.md).

| Experiencia | Control | Propósito y límite |
|---|---|---|
| Reto | Automático, presets R1/R2/R3; sin intervenciones humanas | Probar el motor y reportar resultados por separado. Usa el dominio `simulador`. |
| Simulador | Demo libre automática, con configuración local | Explorar perfiles y refugios; no es una evaluación oficial. Usa `simulador`. |
| Juego | Operador agrega entidades/eventos al mapa mientras el reloj automático avanza | Intervención lúdica local; no equivale a control de un personaje ni a métricas oficiales. Usa `simulador`. |

El modo de dominio `juego` sigue disponible en componentes/APIs humanas anteriores, pero no está conectado a la tarjeta Jugar actual.

La interfaz añade **Reto** con presets de Anochecer (20), Medianoche (80) y Apocalipsis (200). En el fixture Manta sus habitantes aparecen aleatoriamente en las zonas aproximadas de Tarqui, Los Esteros, Barbasquillo y Jocay, con un reparto equilibrado y reproducible por semilla. Las amenazas del Reto concentran una cuota provisional del 80% de cada tipo dentro de 3,5 km del ancla de Parque La Dolorosa y los eventos prefieren calles de esa área; queda una parte fuera para cubrir la ciudad. Simulador libre conserva sus apariciones y selección globales. Se usan el mismo motor, mapa y resolutor; cada ronda puede reiniciarse desde el panel y aún no se automatiza la campaña consecutiva de 15 minutos. Densidad, proporciones de tipos, radio, geometría/cuota exacta de sectores y turnos de evento son provisionales porque el enunciado no los especifica. Véanse [ADR-037](../arquitectura/decisiones/0037-spawn-reto-cuatro-sectores.md), [ADR-038](../arquitectura/decisiones/0038-foco-amenazas-reto.md) y [ADR-039](../arquitectura/decisiones/0039-reinicio-ronda-reto.md).

## Invariantes

Una partida tiene un modo fijo y un `runId`. Cambiar de modo inicia otra partida y no puede interrumpir una prueba por iniciativa de un visitante. Primera versión: una partida activa y un jugador humano; no prometer sesiones independientes concurrentes.

Ambos modos comparten grafo, reloj, zombies, cierres, reglas de mordida y refugios. El cliente anima posiciones confirmadas; no determina colisiones ni acelera el mundo. Los dormidos permanecen ocultos para jugador, panel y motor mientras corresponda.

En la demo del mapa Manta, ambos modos comparten el subgrafo urbano limitado por la caja de [ADR-030](../arquitectura/decisiones/0030-ventana-urbana-zona-jugable.md); no aparecen personajes o amenazas fuera de ella. Los mapas sintéticos conservan sus propios límites.

## Pantalla inicial prevista

- «Simulador»: demo libre; observar/iniciar o configurar requiere el control local de operador.
- «Reto»: presets de evaluación automática; los parámetros no definidos por el reto se muestran como provisionales.
- «Jugar»: iniciar/continuar un mundo local y colocar herramientas en una partida activa; detener las colocaciones cuando el mundo se pausa o corresponde a Reto.
- Durante una prueba oficial, mostrar observación y explicar que el juego está temporalmente ocupado.

Controles iniciales: clic en vecino, botones con nombre de destino, Tab/Enter y «Esperar». No usar WASD sin definir cómo elegir entre vecinos de un grafo irregular. Movimiento visual con opción de reducir animación, foco visible y estados que no dependan solo de color.

La demo sintética local tiene un control explícito de desarrollo, no un endpoint administrativo público. Se activa con `NAVIRA_LOCAL_DEMO_CONTROL=1`; el backend limita las operaciones a loopback y origen same-host. Despliegues no deben configurar este opt-in.

## Radio y final de partida

La ayuda consulta el mismo motor sobre la información observable y muestra recomendación y motivo. No ejecuta movimientos, no garantiza supervivencia y no tiene acceso a dormidos ocultos. Al terminar, mostrar turnos, distancia, ayuda usada y motivo de finalización; reiniciar depende de los permisos del operador. Flujos: [jugador](flujos/jugador.md), [espectador](flujos/espectador.md) y [operador](flujos/operador.md).
