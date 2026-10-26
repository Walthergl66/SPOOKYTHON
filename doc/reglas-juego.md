# Reglas del mundo

Estado: implementación parcial del grafo, movimiento zombie, cierres programados y resolución de intenciones en `src/navira/`; el bucle de reloj, transporte de eventos y escenarios siguen pendientes. Fuente: [reto](referencias/reto-original.md). Dudas: [pendientes](pendientes.md).

## Reglas obligatorias

| ID | Regla | Aplicación |
|---|---|---|
| R-01 | Grafo de unas 300 intersecciones y cuatro refugios | Preservar identidad, latitud, longitud, distancia y tipo de calle. |
| R-02 | Turnos de dos segundos; zombies primero | El reloj pertenece al servidor. |
| R-03 | Un movimiento de sobreviviente es a un vecino por calle habilitada o a sí mismo | Movimiento inválido equivale a espera; mantener reglas iguales para humano y automático. |
| R-04 | Caminante: una calle cada dos turnos, dirección aleatoria | Registrar su fase y el estado aleatorio privado. |
| R-05 | Corredor: dos calles por turno; persigue a un sobreviviente a tres nodos o menos | Contar saltos en el grafo vigente y registrar los dos tramos. |
| R-06 | Horda bloquea su nodo y todos los vecinos | No reducir el bloqueo al nodo central. Su movimiento exacto está pendiente. |
| R-07 | Dormido invisible hasta que un sobreviviente está a dos nodos o menos; despierta como caminante | No filtrar sus datos en proyección, predicción ni ayudas de la radio. |
| R-08 | Eventos eliminan aristas transitables | Invalidar rutas y decisiones basadas en la versión anterior. |
| R-09 | Mordida por coincidencia de nodo al final del turno | Resolver tras aplicar conjuntamente los movimientos. |
| R-10 | Mordida por cruzar la misma calle en sentido opuesto | Comparar cada tramo zombie, incluido el primero de un corredor. |
| R-11 | `/paso` responde en menos de 500 ms | Un timeout deja quieto al sobreviviente; no equivale a estar a salvo. |
| R-12 | Cada sobreviviente puede dirigirse al refugio elegido por el equipo | La política de rutas selecciona destino; llegada y mordida respetan el orden acordado. |

## Decisiones de diseño

- Modos comparten reglas y resolución. En juego, el humano decide por su personaje y el resto usa el motor.
- Una arista por turno para sobrevivientes. Distancia/velocidad se consideran adicionalmente; confirmar su relación con la eficiencia oficial (P-01).
- Identificar un segmento de calle de forma canónica para detectar cruces aunque tenga dos aristas dirigidas. No confundir segmentos paralelos físicamente distintos.
- No declarar una mordida en un nodo intermedio solo porque un corredor pasó por él: aplicar R-09 y R-10, salvo aclaración oficial.
- Mordida conocida no significa movimiento topológicamente inválido. El motor evita ese destino; si el jugador lo elige legalmente, el resolutor aplica la consecuencia. La horda sí restringe transitabilidad.
- Un sobreviviente mordido no vuelve a decidir. Un evacuado deja de participar después de resolver su llegada de manera válida.
- Un destino marcado como zona segura se interpreta siempre dentro de la amenaza y fuente que lo respalda. En el fixture actual, “Zona Segura” corresponde a los mapas de evacuación por tsunami del GAD Manta; no acredita seguridad ante terremotos ni sustituye alertas oficiales. Ver [fuentes y límites](mapa-manta.md).
- El mundo usa una secuencia aleatoria privada por partida para seleccionar estados iniciales y decisiones que las reglas dejan al azar. Una modificación pequeña de la entrada puede desviar el recorrido y alterar rutas, encuentros, mordidas y evacuaciones siguientes.
- La aleatoriedad no reemplaza las reglas: el corredor sigue persiguiendo según la regla configurada; la horda sigue bloqueando nodo y vecinos; sus movimientos quedan sometidos a P-07. El motor conserva respuesta estable para solicitudes repetidas sobre la misma instantánea.

## Supuestos pendientes de confirmar

Activación/fase inicial de dormidos (P-02), objetivo y desempate del corredor (P-03), seguridad de refugios y orden de llegada (P-04), eficiencia y supervivencia oficial (P-05), movimiento de hordas (P-07), calles dirigidas y bloqueo de ambos sentidos (P-08). No presentar estas interpretaciones como texto oficial.

Valores provisionales del prototipo: dormido detecta supervivientes a dos saltos no dirigidos al inicio de la fase zombie y espera el resto de ese turno; el corredor elige superviviente por menor distancia dirigida y después por ID, manteniendo objetivo durante sus dos pasos; hordas quedan estáticas; mordida se resuelve antes de evacuar. La activación del dormido en el mismo turno es configurable. Cierres aceptan ID de arista o segmento físico. Cambiar estos supuestos requiere registrar la aclaración fuente.

## Escenarios obligatorios

| Ronda | Duración | Sobrevivientes | Condiciones |
|---|---|---:|---|
| Anochecer | 5 minutos | 20 | Solo caminantes. |
| Medianoche | 5 minutos | 80 | Caminantes, corredores y hordas; colapso de un puente. |
| Apocalipsis | 5 minutos | 200 | Todos los tipos; dos calles bloqueadas en vivo. |

Cantidad de zombies y distribución no están definidas en la fuente; parametrizarlas y confirmar criterios (P-09). Los perfiles `libre`, `caminantes`, `mixto` y `horda` y la generación de 1–200 sobrevivientes son fixtures sintéticos para desarrollo; no fijan distribución ni dificultad oficial. Conservar escenario, semilla, versión, eventos y órdenes para repetir una ejecución; no se promete que un cambio mínimo produzca siempre resultados distintos, sino que puede propagarse por las dependencias del mundo.

## Extras

Capacidad de refugios: reservas consistentes y liberación al morir/cambiar destino. Rescate: cinco camionetas, doble velocidad y cuatro pasajeros cada una. Ambos requieren ampliar reglas y pruebas mediante decisión explícita antes de implementarse.
