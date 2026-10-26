# Motor de rutas y predicción

Estado: movimiento zombie y ciclo local implementados parcialmente en `src/navira/simulation/`; Dijkstra dirigido y selección de refugio están implementados como núcleo puro en `src/navira/routing/dijkstra.py`. Integración con `/paso`, mapa real, escenarios, supervivencia y tiempos siguen pendientes/sin medir.

## Referencia inicial

Dijkstra sobre el grafo vigente con costo base en metros y factor configurable por tipo de calle. El valor neutral de cada factor es 1.0; no introduce preferencia no confirmada. `encontrar_ruta()` respeta dirección, aristas/segmentos cerrados y nodos peligrosos visibles. `seleccionar_refugio()` puede respetar el refugio objetivo o elegir el menor costo, desempata por ID del refugio y usa calles como desempate final. El origen bloqueado puede salir; no se permite entrar a un nodo bloqueado. La información de bloqueos debe ser una proyección permitida, nunca la ubicación privada de dormidos.

El costo ponderado se expresa en metros relativos. Los factores por tipo y su aplicación son parámetros de diseño, no una fórmula oficial de eficiencia; velocidad y duración por turno no se mezclan hasta resolver P-01. El núcleo no está conectado a `/paso` y no prueba una política completa contra mordidas dinámicas.

## Mejora temporal

Estado de búsqueda: `(nodo, turno futuro)`. Horizonte inicial configurable: seis turnos; ejecutar solo el primer paso y recalcular en cada turno. Incluir espera como acción. Descartar colisiones conocidas; el futuro incierto se representa como riesgo, no como conocimiento exacto.

Prioridades: validez, evitar mordidas conocidas, riesgo futuro, turnos hasta refugio y costo de calle. La función exacta de combinación de riesgo/tiempo se decide mediante experimentos registrados, no queda fijada por este documento. Una búsqueda truncada o con riesgo estimado no garantiza optimalidad global ni supervivencia.

Si se optimizan turnos, la heurística debe ser una cota inferior en saltos; si se usa tiempo ponderado, mantener unidades compatibles. No sumar metros, segundos y probabilidades sin normalización y justificación. Registrar fórmula, parámetros y escenario de ajuste.

## Predicciones por tipo

- Caminante: fase de movimiento y distribución sobre vecinos legales.
- Corredor: objetivo probable a tres saltos, dos movimientos y alternativas por empate; reevaluar al cambiar sobrevivientes.
- Horda: nodo y vecindad bloqueados; dinámica exacta pendiente de confirmación.
- Dormido: el motor no conoce posición antes de activarse. Al aparecer, recalcular como caminante.

El prototipo aplica valores provisionales registrados en [pendientes](pendientes.md): caminante elige al azar una calle saliente en su fase de dos turnos; corredor persigue por ruta dirigida más corta hasta tres saltos, empate por ID de sobreviviente y objetivo fijo durante sus dos tramos; horda permanece fija; dormido usa radio topológico de dos saltos y no se mueve por defecto en el turno de activación. Dijkstra existe como utilidad pura, pero el planificador que consulta `/paso` sigue pendiente.

No bloquear todos los nodos alcanzables por cualquier corredor en cualquier futuro: puede inmovilizar todo el mapa. Usar riesgo acotado y comparar políticas. No usar la semilla del simulador para adivinar movimientos.

## Presupuesto de cálculo

- Preparar bloqueos, distancias y riesgos compartidos una vez por turno.
- Trabajar sobre snapshots locales reconstruibles; ninguna consulta remota dentro de cada expansión.
- Separar cómputo CPU del HTTP; establecer límites de tiempo y expansiones medidos.
- Mantener una decisión base disponible y sustituirla solo si llega una mejora antes del plazo.
- Priorizar sobrevivientes en peligro si el presupuesto global no permite refinar todos.
- Limitar y cachear recomendaciones de radio para que no perjudiquen la prueba de carga.

La preparación global también cuenta dentro de los dos segundos. Medir latencia HTTP y ciclo completo; no ocultar trabajo precalculado fuera del reloj. Criterios: [pruebas](pruebas.md). Referencia conceptual consultada: [SIPP original](https://www.cs.cmu.edu/~maxim/files/sipp_icra11.pdf); su implementación completa no forma parte del compromiso inicial.
