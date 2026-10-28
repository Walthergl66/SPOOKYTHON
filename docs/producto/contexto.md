# Contexto del proyecto

Estado: alcance acordado; implementación local parcial. Fecha: 2026-10-27.

## Problema y objetivo

Track A «Escape de Manta Zombie»: construir en AWS un motor que recomiende el siguiente movimiento hacia un refugio mientras zombies y cierres de calles cambian el mapa. Es una demostración de rutas dinámicas aplicables a evacuación y despacho; no es un sistema validado para emergencias reales.

Nombre oficial elegido por el usuario: **Navira**. Identificador técnico previsto: `navira`; paquete backend previsto: `src/navira/`. MantaSafe fue únicamente el nombre de trabajo anterior y se conserva en referencias históricas. El directorio local continúa en `SPOOKYTHON`; no se ha solicitado renombrarlo. Decisión: [ADR-006](../arquitectura/decisiones/0006-nombre-navira.md).

## Solicitudes explícitas del usuario

1. Analizar el reto y proponer una solución viable.
2. Preparar un plan de implementación.
3. Incorporar dos modos: simulador automático y juego en el que una persona aparece aleatoriamente y lleva su personaje a un refugio.
4. Modularizar toda la documentación en `docs/`, registrar el contexto de cada cambio y crear un `AGENTS.md` que exija revisar los `.md` antes de trabajar.
5. Incorporar PRD, TRD, ODDD y SDD. El usuario confirmó ODDD como orientación a objetos y diseño guiado por dominio (OO + DDD); la adopción conserva stack, modos y alcance existentes.
6. Establecer **Navira** como nombre de la app.
7. Al incorporar lugares seguros en Manta, Ecuador, considerar amenazas de tsunami y terremoto.
8. El simulador debe tener variación aleatoria de mundo y decisiones permitidas; cambios pequeños en semilla, estado o eventos pueden desviar la evolución posterior.
9. Aclaración del usuario (2026-10-26): el objetivo de la evacuación es encontrar rutas que minimicen las personas mordidas durante la simulación; las evacuaciones se consideran después de ese objetivo primario.
10. Solicitud del usuario (2026-10-27): ampliar todo el mapa y la zona jugable a Manta completa, más allá de la caja urbana anterior; se confirma incluir las zonas rurales y permitir aparición/rutas de juego en esa área.
11. Solicitud del usuario (2026-10-27): reducir a 5 km por lado el margen de navegación del mapa para enfocarlo en Manta, manteniendo íntegra la zona jugable.
12. Solicitud del usuario (2026-10-27): impedir que los zombies se acerquen a las zonas seguras en una cuadra alrededor; la regla se representa como un salto topológico alrededor de los refugios en partidas Manta.
13. Solicitud del usuario (2026-10-27): al iniciar la simulación sortear entre 1 y 10 incidentes viales; al aplicarse, alertar en el mapa con un punto amarillo parpadeante, cerrar esa zona para sobrevivientes y recalcular las recomendaciones de ruta.
14. Solicitud del usuario (2026-10-27): reemplazar el selector «Ruta observada» por selección directa de habitantes en el mapa y desplegar información del habitante y su ruta vigente.
15. Solicitud del usuario (2026-10-27): corregir habitantes que oscilan o dan vueltas; mantener su ruta estable y cambiarla cuando un zombie esté cerca.
16. Solicitud del usuario (2026-10-27): agregar una experiencia específica para la prueba de fuego del reto y conservar «Simulador» como demo libre.
17. Solicitud del usuario (2026-10-27): mostrar los modos al abrir la app en el orden Reto, Simulador y Jugar, con Reto seleccionado inicialmente.
18. Solicitud del usuario (2026-10-27): mostrar un único contador fijo de mordidos en el panel, conservando el total acumulado de la partida.
19. Solicitud del usuario (2026-10-27): al seleccionar habitantes durante el Reto, mostrar en el panel su ruta recomendada vigente.
20. Aclaración para resolver CAM-092: el snapshot no debe recalcular rutas para toda la población en todas las fases; al seleccionar un habitante, calcular bajo demanda únicamente su ruta y reflejarla en la ficha y el mapa.
21. Solicitud del usuario (2026-10-27): en el modo Reto, iniciar a los habitantes en los cuatro sectores nombrados por el enunciado: Tarqui, Los Esteros, Barbasquillo y Jocay. La semilla y los nodos concretos continúan aleatorios.
22. Solicitud del usuario (2026-10-27): agregar reinicio para la ronda del Reto y concentrar zombies, hordas e incidentes alrededor del centro de Manta porque la vista actual se percibe vacía.
23. Aclaración del usuario (2026-10-27): «Lo que el jurado va a buscar» lista errores comunes; si la ruta evita solo el nodo de una horda y pasa por un vecino, es un error. La regla oficial aplicable es R-06: bloquea el nodo y todos sus vecinos.
24. Solicitud del usuario (2026-10-27): completar las pruebas de las tres rondas de cinco minutos y las brechas de carga asociadas.
25. Solicitud del usuario (2026-10-27): en Simulador, mostrar inicialmente solo «Iniciar simulación»; después elegir puntos seguros, configurar la cantidad de habitantes y zombies, y dejar la velocidad fija en 4× sin selector.
26. Solicitud y confirmación del usuario (2026-10-27): organizar la app como tres experiencias —Reto, Simulador y Juego— y redefinir Juego como modo de operador. El mundo debe seguir corriendo mientras el usuario coloca habitantes, tipos de zombies, refugios e incidentes donde indique en el mapa.
27. Solicitud del usuario (2026-10-27): al empezar un nuevo Juego de operador, mostrar el mapa jugable de Manta vacío de habitantes, zombies, refugios e incidentes para que el usuario coloque las piezas.
28. Solicitud del usuario (2026-10-27): agregar en Jugar un botón visible para iniciar una nueva partida vacía mientras otra partida de operador está activa o pausada.

Documentos de producto y método: [PRD](PRD.md), [TRD](TRD.md), [ODDD](../dominio/ODDD.md), [SDD](../metodo/SDD.md). Criterios por funcionalidad: [especificaciones](../metodo/especificaciones/README.md).

La versión principal actual separa Reto, Simulador y Juego de operador; sus reglas de dominio automáticas se comparten. La API de personaje humano queda como flujo implementado anterior y no está conectada a la navegación principal actual. Multijugador y múltiples partidas concurrentes no forman parte de la primera versión.

## Obligaciones del reto

- Grafo de Manta de unas 300 intersecciones, calles con distancia/tipo/velocidad y cuatro refugios. La aclaración del usuario pide considerar tsunami y terremoto; la evidencia actual de zonas del GAD cubre tsunami, mientras que la clasificación sísmica sigue pendiente. Ver [dataset](../dominio/mapa-manta.md) y [ADR-007](../arquitectura/decisiones/0007-mapa-manta-y-evidencia-de-amenazas.md).
- Turnos de dos segundos; zombies antes que sobrevivientes; cuatro tipos de zombie y cierres en vivo.
- `POST /paso` con el contrato exacto, API key y respuesta en menos de 500 ms.
- Simulador propio que publica estado y consulta al motor; mapa vivo y despliegue AWS.
- Flujo de reto con las rondas automáticas de 20/80/200 sobrevivientes, separado de la demo libre y del juego humano.
- AWS Budget con alerta desde el primer día, repositorio público e historial real de commits.
- README, arquitectura exportada, costos, endpoint, ejecución/medición documentadas y pitch.

Fuente completa y rúbrica: [reto original](../referencias/reto-original.md). Reglas detalladas: [reglas del juego](../dominio/reglas-juego.md).

## Prioridades

Primero reglas correctas, nivel base completo, supervivencia y latencia. Después predicción demostrable y juego humano mínimo. Capacidad de refugios y camionetas solo después de estabilizar las rondas. El juego es un complemento solicitado, no un sustituto de la evaluación automática.

Prueba: tres rondas de cinco minutos, con 20, 80 y 200 sobrevivientes. Dentro de la prueba: supervivencia 50 %, eficiencia 20 %, latencia 15 % y disponibilidad 15 %. La prueba pesa 40 % de la nota total. Objetivos internos: p95 ≤150 ms, errores/timeouts <0,5 %, cero decisiones inválidas y reloj dentro de su período. Todavía no hay resultados.

## Fechas proporcionadas

Entrega: miércoles 28 de octubre de 2026 a las 10:00, Ecuador continental (UTC−5). Demo: viernes 30, ULEAM, cinco minutos de pitch y tres de preguntas. Conservar estas fechas como datos del documento; si hay una prórroga, registrar la fuente antes de cambiarlas.

## Límites actuales

Existe una extracción OSM ampliada para simulación en una envolvente con margen del cantón (CAM-073); no certifica que estén todas las calles ni el límite municipal exacto, y no existe despliegue verificado. Las aclaraciones de reglas, cobertura del mapa y seguridad sísmica están en [pendientes](../seguimiento/pendientes.md). El trabajo debe empezar desde [estado actual](../seguimiento/estado-actual.md), sin asumir que los archivos previstos en el plan ya existen.
