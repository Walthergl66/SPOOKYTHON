# Pruebas, métricas y aceptación

Estado: estrategia parcialmente implementada; hay suites para modelo, grafo, resolutor, coordinador en memoria y contrato HTTP ASGI. Persistencia durable, carga, interfaz y rondas completas siguen pendientes.

## Niveles

1. Núcleo puro: grafos pequeños con resultados conocidos, sin AWS ni servidor.
2. Contratos: HTTP real, autenticación, formatos y casos de error.
3. Integración: simulador, motor, snapshots, panel y recuperación.
4. Carga: ráfagas concurrentes, ciclo completo y endpoint público.
5. Producto: una persona recorre juego y panel sin instrucciones del desarrollador.

## Matriz mínima

| ID | Caso | Resultado esperado |
|---|---|---|
| T-01 | Caminante con fase | Una calle cada dos turnos. |
| T-02 | Corredor y bloqueos | Dos pasos legales; trayectoria completa y objetivo según regla acordada. |
| T-03 | Horda | Nodo y vecinos intransitables. |
| T-04 | Dormido | No visible ni utilizable por motor antes de activación; la proyección pública omite ID, nodo y movimiento de zombies que continúan dormidos. `test_panel.py` cubre el panel; filtrado del motor permanece cubierto por pruebas del planificador. |
| T-05 | Coincidencia/cruce | Mordida final o sentido opuesto, incluidos ambos tramos de corredor. |
| T-06 | Orden de turno | Misma fase del mundo para todos; zombies antes de decisiones. |
| T-07 | Cierre en vivo | El grafo filtra arista dirigida o segmento físico cerrado; una regresión confirma activación por turno en el coordinador en memoria. |
| T-08 | Sin ruta/timeout | Acción válida o espera; sin falsa garantía de seguridad. |
| T-09 | Refugio | Estado final correcto según orden acordado de mordida/llegada. |
| T-10 | Repetición/reinicio | Misma decisión en misma instantánea; ninguna caché cruza partidas. |
| T-11 | Ráfaga | 20, 80 y 200 solicitudes concurrentes cada dos segundos. |
| T-12 | Aparición humana | Nodo elegible y solicitud tardía incorporada en turno correcto; CAM-036 cubre servicio y hook antes de movimiento, no el ciclo de juego ensamblado. |
| T-13 | Propiedad/acciones | Otra sesión no controla; clics múltiples no conceden pasos extra. CAM-036 cubre cookie de propiedad, concurrencia de dos uniones y origen, no todavía autorización de acciones. |
| T-14 | Órdenes tardías/duplicadas | Rechazo o acuse idempotente; no aplicar al turno siguiente. |
| T-15 | Reconexión | El panel recibe snapshot inicial/por versión; heartbeat detecta canal vivo; al reconectar carga el snapshot vigente, sin deltas incompletos, detener mundo o mezclar partidas. `test_panel.py` cubre secuencia posterior y cambio de partida; UI reconecta por WebSocket. Persistencia duradera/multi-worker no cubierta. |
| T-16 | Separación de modos | Rondas oficiales sin humanos ni cambio de modo. |
| T-17 | Paridad | Mismo estado e intenciones dan mismo resultado con control humano o automático; hay una regresión del resolutor, aún parcial. |
| T-18 | Snapshot/recuperación | El coordinador genera estados completos; un adaptador local CAS bajo lock admite un solo escritor por versión. Persistencia durable y recuperación entre procesos siguen pendientes. |
| T-19 | Accesibilidad | Juego y selección por teclado, foco visible y estados no basados solo en color. |
| T-20 | Documentación | Enlaces locales válidos e inventario completo. |
| T-21 | Integridad SDD | IDs, requisitos, tareas, CA, pruebas y matriz coherentes; verificación exige CAM/evidencia. |
| T-22 | Predicción | Comparación reproducible entre base y mejora con semillas/escenarios y límites de información declarados. |
| T-23 | AWS y entrega | Salud/API/WebSocket, permisos/TLS, Budget, costos y entregables con evidencia real y enlaces comprobados. |
| T-24 | Variación y reproducción estocástica | Configuración/semilla/versiones/entradas idénticas reproducen; otra semilla y una perturbación controlada pueden divergir; la misma instantánea HTTP conserva la decisión. |

## Medición de la prueba de fuego

Tres rondas consecutivas de cinco minutos, 150 turnos cada una. Máximo teórico si nadie sale antes: `150 × (20 + 80 + 200) = 45.000` solicitudes. Ronda 3 promedia 100 solicitudes/segundo, pero la carga decisiva es la ráfaga de 200.

Medir desde el cliente que llama `/paso`: inicio antes del envío y fin tras recibir respuesta completa. Registrar errores y timeouts, sin excluirlos para mejorar percentiles. Separar métricas internas de pruebas públicas desde una ubicación identificada. Registrar simultáneamente preparación, planificación, resolución y retraso del reloj de dos segundos.

Metas internas: p95 ≤150 ms, errores/timeouts <0,5 %, cero pasos inválidos generados y ningún retraso sostenido del reloj. Son objetivos; no escribir «cumplido» sin reporte real.

Rúbrica del endpoint: p95 ≤150 ms: 10; ≤300: 7; ≤500: 4; superior: 0. El contrato exige menos de 500 ms aunque la tabla use ese límite. Disponibilidad: errores/fuera de tiempo <0,5 %: 10; <2 %: 6; <5 %: 3; resto: 0. Fórmula exacta de eficiencia/supervivencia pendiente de aclaración; conservar datos sin inventar una equivalencia oficial.

## Comparación de políticas

Ejecutar Dijkstra y política mejorada sobre los mismos escenarios, versiones y lista de semillas, con semillas de validación distintas de las de ajuste. Guardar parámetros y cambios del generador. No escoger solo ejecuciones favorables. Reportar vivos, evacuados y pendientes por separado. Las trayectorias pueden divergir por persecución aunque se repita semilla.

## Evidencia y comandos

P0-04: desde `frontend/`, `npm ci && npm run build` verifica lockfile, TypeScript estricto y bundle de producción. La pantalla inicial soporta selección de modos con teclado mediante botones semánticos, estados `aria-pressed`, foco visible y movimiento reducido; revisar visualmente en anchos móvil y escritorio al cambiar el layout. `.github/workflows/ci.yml` ejecuta además la suite unittest y validadores documentales en GitHub Actions. La compilación local no demuestra que el workflow haya corrido en remoto.

Cada reporte debe incluir revisión de código, mapa, escenario, semilla, modo, parámetros, origen del cliente, fechas, métricas y limitaciones. Guardar en `doc/resultados/` cuando existan; no crear resultados ficticios.

Comprobación documental disponible: `python3 scripts/check_docs.py`. El resto de comandos se documentará tras crear la aplicación; no suponer que `pytest`, un benchmark o un build ya están configurados.

Validación SDD disponible: `python3 scripts/check_sdd.py` y regresiones del comprobador mediante `python3 -m unittest discover -s tests -p 'test_check_sdd.py'`. T-20/T-21 verifican metodología documental; T-01 a T-19, T-22 a T-24 siguen pendientes total o parcialmente como pruebas de aplicación/operación. Referencias: [SPEC](especificaciones/README.md), [trazabilidad](trazabilidad.md).

El modelo de mapa tiene regresiones con `python -m unittest discover -s tests -p 'test_mapa.py' -v`. Estas pruebas verifican el grafo y el filtrado de cierres; no prueban eventos temporales, turnos ni un dataset real de Manta.

Las entidades e intenciones tienen regresiones con `python -m unittest discover -s tests -p 'test_modelo.py' -v`. Verifican identidad de partida/turno/fase y compatibilidad del contrato entre modos; no prueban aún la resolución de movimientos.

El resolutor de un turno tiene regresiones con `python -m unittest discover -s tests -p 'test_resolver.py' -v` (11 pruebas). Cubren fases de caminante, dos tramos de corredor, horda, despertar, espera en movimiento inválido, mordidas por nodo y cada cruce, prioridad de mordida sobre llegada y uso del mismo resolutor en ambos modos. La regla exacta de dormidos, desempate del corredor y llegada siguen configurables/provisionales; esta suite no verifica ocultamiento de información.

El coordinador y reloj local tienen regresiones con `python -m unittest discover -s tests -p 'test_coordinador.py' -v` (7 pruebas). Cubren snapshots/versiones, flujo de decisión y resolución separados para juego, cierre en turno objetivo y aplicación única, versión obsoleta, apertura del turno siguiente, referencias inválidas y plazo monotónico. No prueban escritura condicional real, concurrencia de procesos, recuperación durable ni un bucle de reloj continuo.

El puerto de persistencia y el adaptador local tienen regresiones con `python -m unittest discover -s tests -p 'test_snapshots_persistidos.py' -v` (3 pruebas). Cubren ciclo CAS completo, rechazo de versión antigua, inserción duplicada y carrera de dos hilos donde solo un escritor gana. No prueban DynamoDB, múltiples procesos/hosts, apagado abrupto ni recuperación durable.

El contrato HTTP de base tiene pruebas con `python -m unittest discover -s tests -p 'test_api_http.py' -v` (5 pruebas), cubriendo salud pública, autenticación ausente/incorrecta/configurada, forma exacta del éxito y rechazos 422. Además se probó localmente Uvicorn con `curl`: `/salud` 200, `/paso` autenticado 200 y sin clave 401. El smoke test no mide p95 ni valida rutas reales.

El núcleo Dijkstra tiene regresiones con `python -m unittest discover -s tests -p 'test_dijkstra.py' -v` (7 pruebas). Cubren peso/distancia, factor configurable por tipo, cierres, nodos bloqueados, ruta inexistente, desempates, selección de refugio y validaciones. No prueban mapa de Manta ni peligros futuros.

La búsqueda temporal experimental tiene regresiones con `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_ruta_temporal.py' -v` (8 pruebas). Cubren espera, horizonte, cierres por fase, exposición inyectada, ruta completa y límites de expansión/tiempo. CAM-033 registra una medición serial local; no verifica pronóstico de amenazas, comparación contra Dijkstra, T-22 ni latencia HTTP.

El pronóstico observable tiene regresiones con `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_prediccion_rutas.py' -v` (5 pruebas). Comprueba mezcla de fase desconocida de caminantes, seguimiento provisional de corredor con sobrevivientes observados, bloqueo estático de horda, validación de datos y rechazo explícito de dormidos. No confirma las reglas oficiales de movimiento ni una probabilidad de supervivencia; CAM-034 aún no completa T-22.

`PYTHONPATH=src /tmp/navira-env/bin/python -m navira.evaluacion_rutas --turnos 3` compara Dijkstra y temporal en 27 pares (tres perfiles sintéticos, tres semillas y cohortes 20/80/200), cada política en mundo reproducido e independiente. `test_evaluacion_rutas.py` verifica contrato de resultados y validación de parámetros. CAM-035 repite la matriz y confirma igualdad determinista de resultados; es evidencia T-22 parcial, no ronda oficial, latencia HTTP ni T-11.

El caso de uso de `/paso` tiene pruebas con `python -m unittest discover -s tests -p 'test_decidir_paso.py' -v` para sesión/turno/fase/personaje, selección de ruta, cierres, hordas, zombies activos, dormidos ocultos y cruces conocidos. `test_api_planner_integration.py` valida respuesta con política inyectada y errores HTTP 404/409/503. `test_demo.py` comprueba el bootstrap de un snapshot local hacia decisiones, la ruta HTTP demo y que el ensamblaje base conserva espera. El modo demo usa exclusivamente `data/maps/demo-sintetico.json`, no es el mapa de Manta ni ejecuta un reloj continuo.

`test_simulacion_automatica.py` verifica una ronda completa con Dijkstra, el orden de movimiento zombie antes de la recomendación, continuación desde fase de decisiones persistida, apertura del siguiente turno y rechazo de versión antigua/modo incompatible. La suite no mide un reloj continuo, durabilidad ni concurrencia entre procesos.

`test_juego_sesion.py` cubre P4B-01 local: sesión única por partida, dos intentos concurrentes, aparición reproducible en nodo no refugio con ruta, sesión idempotente por cookie, ausencia de candidato sin reservar cupo, partida de juego activa, espera fuera de fase PREPARACION, hook de incorporación previo a movimiento zombie y Origin/cookie HttpOnly-Secure-SameSite. No cubre expiración/revocación P-12, DynamoDB, múltiples procesos, controles de acciones o recorrido de interfaz.

`test_simulacion_mapa_manta.py` ejecuta tres turnos de perfiles sintéticos sobre el fixture de Manta con 20/80/200 sobrevivientes, semilla fija y regla de movimiento del fixture; comprueba versión de mapa, inicios fuera de refugios y pasos vecinos o de espera. No verifica exactitud cartográfica ni seguridad de los refugios. El resultado exploratorio reproducible está en [CAM-025](resultados/simulacion-manta-cam025.md); no es una ronda oficial ni una medición de carga.

`test_simulador_demo.py` verifica el CLI local: limita rondas, imprime JSON por línea, reproduce escenario/semilla, registra la semilla generada si se omite, prueba variación posible de caminantes por semilla y divergencia de rutas en una trayectoria de varios turnos, omite dormidos en el reporte, evacúa el perfil libre y crea cohortes sintéticas de 20/80/200. `test_demo.py` confirma que repetir una solicitud sobre el mismo snapshot conserva decisión y versión. T-24 está cubierto parcialmente para replay local/variación; no cubre recuperación durable/versionado entre despliegues ni cascadas de eventos oficiales. El fixture pequeño tiene cuatro nodos no refugio, por lo que los personajes pueden compartir posición. CAM-020 incluye una ráfaga local concurrente por cohorte; fue un smoke de una sola ejecución con estado fijo y no cumple T-11, que requiere repeticiones/intervalo y medir en el entorno de evaluación.

`test_carga_http.py` verifica agregación de conteos, errores y percentiles mediante un emisor controlado; `test_demo.py` valida el ensamblaje de cohortes por argumentos y variables de entorno. Para llamar transporte HTTP real, iniciar Uvicorn con `NAVIRA_DEMO=1`, `NAVIRA_DEMO_SURVIVORS` y `NAVIRA_DEMO_SEED` iguales al cliente y correr `python -m navira.carga_http`. Los resultados del smoke local CAM-020 están en [carga local](resultados/carga-local-cam020.md); no reemplazan T-11 contra el entorno/ubicación de evaluación.

El evaluador `python -m navira.evaluacion_local` crea un servidor Uvicorn de loopback, envía solicitudes autenticadas a `/paso` para cada sobreviviente activo, usa los destinos HTTP como intenciones y avanza el snapshot al terminar la ráfaga del turno. Programa los inicios con reloj monotónico; `--periodo-segundos` configura la cadencia, con valor predeterminado de 2 s. Registra intervalo/retraso de inicio y duración del ciclo para detectar sobrepasos. Ejemplo corto: `--turnos 3 --poblaciones 20 80 200 --concurrencia 200 --semilla 20261026 --periodo-segundos 2`. La clave de servicio es aleatoria y temporal y no aparece en el JSON. `test_evaluacion_local.py` comprueba contrato, versiones, avance de turnos y cadencia HTTP. Evidencia CAM-028 y CAM-029 en [reporte multi-turno](resultados/evaluacion-multi-turno-cam028.md) y [reporte temporizado](resultados/evaluacion-cadencia-cam029.md). CAM-029 cubre tres turnos por cohorte en loopback; no dura cinco minutos ni usa entorno remoto, composición oficial o repeticiones. T-11 y las rondas oficiales siguen pendientes.
