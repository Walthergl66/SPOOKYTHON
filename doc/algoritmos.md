# Motor de rutas y predicción

Estado: movimiento zombie y ciclo local implementados parcialmente en `src/navira/simulation/`; Dijkstra dirigido está conectado a la decisión `/paso`; CAM-033 añade `src/navira/routing/temporal.py` como núcleo experimental separado, aún no integrado. El punto de entrada predeterminado no carga estado. Evaluación completa y tiempos del proceso real siguen pendientes.

## Referencia inicial

Dijkstra sobre el grafo vigente con costo base en metros y factor configurable por tipo de calle. El valor neutral de cada factor es 1.0; no introduce preferencia no confirmada. `encontrar_ruta()` respeta dirección, aristas/segmentos cerrados y nodos peligrosos visibles. `seleccionar_refugio()` puede respetar el refugio objetivo o elegir el menor costo, desempata por ID del refugio y usa calles como desempate final. El origen bloqueado puede salir; no se permite entrar a un nodo bloqueado. La información de bloqueos debe ser una proyección permitida, nunca la ubicación privada de dormidos.

El costo ponderado se expresa en metros relativos. Los factores por tipo y su aplicación son parámetros de diseño, no una fórmula oficial de eficiencia; velocidad y duración por turno no se mezclan hasta resolver P-01. El caso de uso integrado evita peligros visibles del snapshot actual, pero no modela riesgo futuro ni garantiza supervivencia. La ruta HTTP se puede configurar mediante `crear_app(servicio_decision)`; falta cargar/configurar estado/mapa en el proceso ordinario.

## Mejora temporal

P3-01 implementa `src/navira/routing/temporal.py` como núcleo experimental no conectado a `/paso`. El estado de búsqueda es `(nodo, acciones/turnos)`, con horizonte inicial configurable de seis turnos (1–12), acción de espera y condiciones por fase inyectadas. El primer paso usa bloqueos/cierres del snapshot observable; los siguientes usan el pronóstico suministrado. Los cierres confirmados persisten porque el modelo actual no ofrece reaperturas. Cada invocación limita expansiones y tiempo; un límite agotado descarta toda ruta parcial para preservar la alternativa Dijkstra.

Prioridades lexicográficas adoptadas para este núcleo (ADR-010): validez topológica/bloqueos conocidos, exposición futura acumulada, turnos hasta refugio, metros ponderados y secuencia estable de acciones. El valor de exposición por nodo y fase acepta [0, 1]; la suma es un puntaje de ordenamiento, no probabilidad calibrada de mordida o supervivencia. Los nodos actuales bloqueados no se entran; la espera avanza el estado temporal.

Los límites iniciales por invocación son 20.000 expansiones y 25 ms. Estos no son un presupuesto global por partida ni prueban que 200 recomendaciones quepan en dos segundos. Una búsqueda truncada, sin horizonte suficiente o con riesgo estimado no garantiza optimalidad global ni supervivencia. P3-02 generará pronósticos; P3-03 comparará baseline y temporal antes de seleccionar política. Esta fase no modifica la recomendación HTTP.

Si se optimizan turnos, la heurística debe ser una cota inferior en saltos; si se usa tiempo ponderado, mantener unidades compatibles. No sumar metros, segundos y probabilidades sin normalización y justificación. Registrar fórmula, parámetros y escenario de ajuste.

## Predicciones por tipo

- Caminante: fase de movimiento y distribución sobre vecinos legales.
- Corredor: objetivo probable a tres saltos, dos movimientos y alternativas por empate; reevaluar al cambiar sobrevivientes.
- Horda: nodo y vecindad bloqueados; dinámica exacta pendiente de confirmación.
- Dormido: el motor no conoce posición antes de activarse. Al aparecer, recalcular como caminante.

El prototipo aplica valores provisionales registrados en [pendientes](pendientes.md): caminante elige al azar una calle saliente en su fase de dos turnos; corredor persigue por ruta dirigida más corta hasta tres saltos, empate por ID de sobreviviente y objetivo fijo durante sus dos tramos; horda permanece fija; dormido usa radio topológico de dos saltos y no se mueve por defecto en el turno de activación. Dijkstra y el caso de uso están integrados; la app predeterminada todavía no inicia una partida ni carga mapa.

La demo muestrea posiciones iniciales de sobrevivientes y zombies elegibles desde el RNG privado de la partida; también sortea la fase inicial de caminantes. La CLI/API demo obtiene una semilla nueva de la entropía del sistema cuando no se especifica y el reporte de CLI registra la semilla efectiva. Semilla explícita, mapa, perfil y versión de algoritmo reproducen el reporte dentro de la misma versión. El cambio de semilla puede desviar movimiento y activar zombies a distancias distintas, lo que cambia bloqueos y rutas. Esto completa solo la generación estocástica base de P1-05: la composición de los perfiles sigue fija, el corredor persigue por regla determinista, la horda no se mueve y el resultado no afirma una distribución oficial. La generación no debe inventar cantidades/distribuciones oficiales (P-09) ni una regla de movimiento de horda (P-07). Mantener la planificación de ruta estable para el mismo snapshot; las variaciones del mundo cambian el snapshot y fuerzan un nuevo cálculo.

No bloquear todos los nodos alcanzables por cualquier corredor en cualquier futuro: puede inmovilizar todo el mapa. Usar riesgo acotado y comparar políticas. No usar la semilla del simulador para adivinar movimientos.

## Presupuesto de cálculo

- Preparar bloqueos, distancias y riesgos compartidos una vez por turno.
- Trabajar sobre snapshots locales reconstruibles; ninguna consulta remota dentro de cada expansión.
- Separar cómputo CPU del HTTP; establecer límites de tiempo y expansiones medidos.
- Mantener una decisión base disponible y sustituirla solo si llega una mejora antes del plazo.
- Priorizar sobrevivientes en peligro si el presupuesto global no permite refinar todos.
- Limitar y cachear recomendaciones de radio para que no perjudiquen la prueba de carga.

La preparación global también cuenta dentro de los dos segundos. Medir latencia HTTP y ciclo completo; no ocultar trabajo precalculado fuera del reloj. Criterios: [pruebas](pruebas.md). Referencia conceptual consultada: [SIPP original](https://www.cs.cmu.edu/~maxim/files/sipp_icra11.pdf); su implementación completa no forma parte del compromiso inicial.
