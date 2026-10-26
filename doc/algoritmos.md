# Motor de rutas y predicción

Estado: propuesta por etapas. No hay supervivencia ni tiempos medidos.

## Referencia inicial

Dijkstra sobre el grafo vigente con costos que consideren distancia y tipo de calle. Obtener campos reutilizables hacia los cuatro refugios. Para una acción inmediata, evaluar vecinos y espera; excluir aristas cerradas, horda y mordidas conocidas. Conservar una política base ejecutable antes de añadir predicción.

## Mejora temporal

Estado de búsqueda: `(nodo, turno futuro)`. Horizonte inicial configurable: seis turnos; ejecutar solo el primer paso y recalcular en cada turno. Incluir espera como acción. Descartar colisiones conocidas; el futuro incierto se representa como riesgo, no como conocimiento exacto.

Prioridades: validez, evitar mordidas conocidas, riesgo futuro, turnos hasta refugio y costo de calle. La función exacta de combinación de riesgo/tiempo se decide mediante experimentos registrados, no queda fijada por este documento. Una búsqueda truncada o con riesgo estimado no garantiza optimalidad global ni supervivencia.

Si se optimizan turnos, la heurística debe ser una cota inferior en saltos; si se usa tiempo ponderado, mantener unidades compatibles. No sumar metros, segundos y probabilidades sin normalización y justificación. Registrar fórmula, parámetros y escenario de ajuste.

## Predicciones por tipo

- Caminante: fase de movimiento y distribución sobre vecinos legales.
- Corredor: objetivo probable a tres saltos, dos movimientos y alternativas por empate; reevaluar al cambiar sobrevivientes.
- Horda: nodo y vecindad bloqueados; dinámica exacta pendiente de confirmación.
- Dormido: el motor no conoce posición antes de activarse. Al aparecer, recalcular como caminante.

No bloquear todos los nodos alcanzables por cualquier corredor en cualquier futuro: puede inmovilizar todo el mapa. Usar riesgo acotado y comparar políticas. No usar la semilla del simulador para adivinar movimientos.

## Presupuesto de cálculo

- Preparar bloqueos, distancias y riesgos compartidos una vez por turno.
- Trabajar sobre snapshots locales reconstruibles; ninguna consulta remota dentro de cada expansión.
- Separar cómputo CPU del HTTP; establecer límites de tiempo y expansiones medidos.
- Mantener una decisión base disponible y sustituirla solo si llega una mejora antes del plazo.
- Priorizar sobrevivientes en peligro si el presupuesto global no permite refinar todos.
- Limitar y cachear recomendaciones de radio para que no perjudiquen la prueba de carga.

La preparación global también cuenta dentro de los dos segundos. Medir latencia HTTP y ciclo completo; no ocultar trabajo precalculado fuera del reloj. Criterios: [pruebas](pruebas.md). Referencia conceptual consultada: [SIPP original](https://www.cs.cmu.edu/~maxim/files/sipp_icra11.pdf); su implementación completa no forma parte del compromiso inicial.
