# Motor de rutas y predicción

Estado: CAM-058 integra la búsqueda temporal de exposición observable en `/paso`, el simulador y la ruta prevista del panel; Dijkstra queda como respaldo ante horizonte, presupuesto o falta de ruta temporal. El punto de entrada predeterminado no carga estado. Evaluación HTTP/carga y reglas oficiales siguen pendientes.

## Referencia inicial

Dijkstra sobre el grafo vigente con costo base en metros y factor configurable por tipo de calle. El valor neutral de cada factor es 1.0; no introduce preferencia no confirmada. `encontrar_ruta()` respeta dirección, aristas/segmentos cerrados y nodos peligrosos visibles. `seleccionar_refugio()` puede respetar el refugio objetivo o elegir el menor costo, desempata por ID del refugio y usa calles como desempate final. El origen bloqueado puede salir; no se permite entrar a un nodo bloqueado. La información de bloqueos debe ser una proyección permitida, nunca la ubicación privada de dormidos.

El costo ponderado se expresa en metros relativos. Los factores por tipo y su aplicación son parámetros de diseño, no una fórmula oficial de eficiencia; velocidad y duración por turno no se mezclan hasta resolver P-01. El caso de uso primero evita la exposición futura estimada visible; si la búsqueda no produce un trayecto completo usa Dijkstra para conservar una recomendación válida. Una exposición baja no equivale a menos mordidas garantizadas. La ruta HTTP se puede configurar mediante `crear_app(servicio_decision)`; falta cargar/configurar estado/mapa en el proceso ordinario.

## Mejora temporal

P3-01 implementa `src/navira/routing/temporal.py` y CAM-058 lo integra al caso de uso activo. El estado de búsqueda es `(nodo, acciones/turnos)`, con horizonte configurado en 12 turnos, acción de espera y condiciones por fase inyectadas. El primer paso usa bloqueos/cierres del snapshot observable; los pasos futuros usan el pronóstico suministrado. Los cierres confirmados persisten porque el modelo actual no ofrece reaperturas. Cada búsqueda limita expansiones y tiempo (25 ms por defecto); un resultado parcial, presupuesto agotado o refugio fuera del horizonte descarta la salida temporal y usa Dijkstra.

CAM-034 añade `src/navira/routing/prediccion.py`, que genera las condiciones futuras desde `ZombieObservable` y `SobrevivienteObservable`; no recibe `Partida`, fase privada ni RNG. Los caminantes ramifican uniformemente sobre salidas legales y mezclan las dos fases posibles; los corredores siguen el objetivo provisional más cercano con posiciones de sobrevivientes congeladas; las hordas conservan su bloqueo de nodo/vecinos según la regla estática provisional. CAM-059 agrega el puntaje de las aristas que un zombie puede cruzar en sentido opuesto al sobreviviente. La búsqueda distingue esos cruces de cierres viales; un cruce confirmado solo bloquea el paso del turno actual. Las puntuaciones de nodo/arista se limitan por paso, pero no son probabilidades calibradas de mordida o supervivencia. Si ninguna política encuentra una ruta completa a refugio, el caso de uso intenta un paso de salida legal hacia el menor riesgo observable y luego una ruta estática restante; no garantiza que ese paso salve al sobreviviente. La uniformidad, posiciones fijas y horda estática no reemplazan P-02/P-03/P-07/P-09.

Prioridades lexicográficas de la ruta activa (ADR-018, sustituye selección de política de ADR-012): validez topológica/bloqueos conocidos, menor exposición futura acumulada, menos turnos hasta refugio, metros ponderados y secuencia estable de acciones. El valor de exposición por nodo y fase acepta [0, 1]; la suma es un puntaje de ordenamiento, no probabilidad calibrada de mordida o supervivencia. Los nodos actuales bloqueados no se entran; la espera avanza el estado temporal. Para evaluar partidas, el orden de resultado real es menos mordidos primero y, solo en empate, más evacuados.

Los límites iniciales por invocación son 20.000 expansiones y 25 ms. Estos no son un presupuesto global por partida ni prueban que 200 recomendaciones quepan en dos segundos; la medición local CAM-058 observó una recomendación temporal de hasta 25,194 ms en la matriz registrada y aún no incluye HTTP/carga. Una búsqueda truncada, sin horizonte suficiente o con riesgo estimado no garantiza optimalidad global ni supervivencia. CAM-059 cachea el trayecto por snapshot para que panel y acción automática compartan la misma primera acción aunque el presupuesto temporal fuese variable; la caché solo conserva la versión vigente. La evaluación de alta intensidad registrada durante CAM-059 sigue mostrando resultados con muchas mordidas, así que se necesitan más pares con la configuración real antes de afirmar mejora estable.

Si se optimizan turnos, la heurística debe ser una cota inferior en saltos; si se usa tiempo ponderado, mantener unidades compatibles. No sumar metros, segundos y probabilidades sin normalización y justificación. Registrar fórmula, parámetros y escenario de ajuste.

## Coordinación de cohortes

CAM-061/ADR-020 calculan rutas comunes para sobrevivientes activos que requieren reaccionar a peligro cercano. El orden por exposición actual y futura sigue aplicando; congestión no es un motivo autónomo para desviar. T-35 de grafo mínimo no demuestra reducción de mordidas; validar cohortes con semillas emparejadas y medir coste total por ronda.

## Estabilidad y replanteamiento de ruta

CAM-084 conserva el sufijo de una ruta automática completa en `SnapshotMundo`, y el coordinador lo recorta solo cuando la resolución confirma su primer movimiento. Un snapshot nuevo ya no implica por sí solo un camino nuevo. `DecidirPaso` mantiene el compromiso mientras el siguiente paso sea transitable y no haya un zombie visible a tres saltos topológicos o menos del habitante. Un cierre que afecte a cualquier arista restante invalida el compromiso; un zombie que ocupa el siguiente nodo o un cruce opuesto actual también impide seguirlo. Después se evalúa una alternativa con el pronóstico observable. Los zombies remotos que no están en el radio no provocan un rodeo preventivo.

Las rutas candidatas sin ciclos evitan avances de ida/vuelta que no acerquen al refugio. Las decisiones nuevas sin amenaza cercana usan la ruta dirigida más corta bajo cierres y peligros inmediatos. El radio es un parámetro de diseño, no una regla del reto ni una distancia métrica calibrada. Las consultas de panel y `/paso` son de lectura respecto al compromiso; solo la transición CAS guarda el residuo realmente ejecutado. Ver [ADR-034](decisiones/0034-rutas-estables-y-replanificacion-cercana.md).

## Predicciones por tipo

- Caminante: fase de movimiento y distribución sobre vecinos legales.
- Corredor: objetivo probable a tres saltos, dos movimientos y alternativas por empate; reevaluar al cambiar sobrevivientes.
- Horda: nodo y vecindad bloqueados; dinámica exacta pendiente de confirmación.
- Dormido: el motor no conoce posición antes de activarse. Al aparecer, recalcular como caminante.

El prototipo aplica valores provisionales registrados en [pendientes](../seguimiento/pendientes.md): caminante elige al azar una calle saliente en su fase de dos turnos; corredor persigue por ruta dirigida más corta hasta tres saltos, empate por ID de sobreviviente y objetivo fijo durante sus dos tramos; horda permanece fija; dormido usa radio topológico de dos saltos y no se mueve por defecto en el turno de activación. Dijkstra y el caso de uso están integrados; la app predeterminada todavía no inicia una partida ni carga mapa.

La demo muestrea posiciones iniciales de sobrevivientes y zombies elegibles desde el RNG privado de la partida; también sortea la fase inicial de caminantes. La CLI/API demo obtiene una semilla nueva de la entropía del sistema cuando no se especifica y el reporte de CLI registra la semilla efectiva. Semilla explícita, mapa, perfil y versión de algoritmo reproducen el reporte dentro de la misma versión. El cambio de semilla puede desviar movimiento y activar zombies a distancias distintas, lo que cambia bloqueos y rutas. Esto completa solo la generación estocástica base de P1-05: la composición de los perfiles sigue fija, el corredor persigue por regla determinista, la horda no se mueve y el resultado no afirma una distribución oficial. La generación no debe inventar cantidades/distribuciones oficiales (P-09) ni una regla de movimiento de horda (P-07). Mantener la planificación de ruta estable para el mismo snapshot; las variaciones del mundo cambian el snapshot y fuerzan un nuevo cálculo.

No bloquear todos los nodos alcanzables por cualquier corredor en cualquier futuro: puede inmovilizar todo el mapa. Usar riesgo acotado y comparar políticas. No usar la semilla del simulador para adivinar movimientos.

## Presupuesto de cálculo

- Preparar bloqueos, distancias y riesgos compartidos una vez por turno.
- Trabajar sobre snapshots locales reconstruibles; ninguna consulta remota dentro de cada expansión.
- Separar cómputo CPU del HTTP; establecer límites de tiempo y expansiones medidos.
- Mantener una decisión base disponible y sustituirla solo si llega una mejora antes del plazo.
- Priorizar sobrevivientes en peligro si el presupuesto global no permite refinar todos.
- Limitar y cachear recomendaciones de radio para que no perjudiquen la prueba de carga.

La preparación global también cuenta dentro de los dos segundos. Medir latencia HTTP y ciclo completo; no ocultar trabajo precalculado fuera del reloj. Criterios: [pruebas](../calidad/pruebas.md). Referencia conceptual consultada: [SIPP original](https://www.cs.cmu.edu/~maxim/files/sipp_icra11.pdf); su implementación completa no forma parte del compromiso inicial.
