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
| T-11 | Ráfaga | 20, 80 y 200 solicitudes concurrentes cada dos segundos. CAM-044 mide una corrida local por cohorte con p95 <93 ms, cero errores y ciclos <481 ms, pero solo 12/15/13 turnos antes de terminar; duración/repeticiones/entorno de evaluación faltan. |
| T-12 | Aparición humana | Nodo elegible y solicitud tardía incorporada en turno correcto; CAM-036 cubre servicio/hook y CAM-039 verifica incorporación previa a los zombies del siguiente turno. |
| T-13 | Propiedad/acciones | Otra sesión no controla; clics múltiples no conceden pasos extra. CAM-036 cubre cookie de propiedad/concurrencia de unión; CAM-037 cubre cookie propietaria/origen en autorización de acción, no integración completa del resolutor. |
| T-14 | Órdenes tardías/duplicadas | Rechazo o acuse idempotente; no aplicar al turno siguiente. CAM-040 verifica rechazo tras el deadline, reintento idempotente y resolución/registro con puerta compartida local; falta carrera multiproceso. |
| T-15 | Reconexión | El panel recibe snapshot inicial/por versión; heartbeat detecta canal vivo; al reconectar carga el snapshot vigente, sin deltas incompletos, detener mundo o mezclar partidas. `test_panel.py` cubre secuencia posterior/cambio de partida y CAM-043 prueba `GET /juego/mi-personaje` con cookie, posición actual y última orden; falta recorrido real de navegador. Persistencia duradera/multi-worker no cubierta. |
| T-16 | Separación de modos | Rondas oficiales sin humanos ni cambio de modo; CAM-039 comprueba intención humana y NPC en el resolutor común. CAM-042 usa la ruta visible ya proyectada para una sugerencia opcional, sin leer datos ocultos; falta recorrido automatizado/manual end-to-end. |
| T-17 | Paridad | Mismo estado e intenciones dan mismo resultado con control humano o automático; hay una regresión del resolutor, aún parcial. |
| T-18 | Snapshot/recuperación | El coordinador genera estados completos; un adaptador local CAS bajo lock admite un solo escritor por versión. Persistencia durable y recuperación entre procesos siguen pendientes. |
| T-19 | Accesibilidad | Juego y selección por teclado, foco visible y estados no basados solo en color. CAM-038 usa botones/fieldset nativos; CAM-045 agrega skip link, foco visible para selector y anuncios acotados del deadline. CAM-047 verifica manualmente Tab/Enter/Space en enlace de salto y selección de modo; el juego end-to-end, lector de pantalla y auditoría WCAG siguen pendientes. |
| T-20 | Documentación | Enlaces locales válidos e inventario completo. |
| T-21 | Integridad SDD | IDs, requisitos, tareas, CA, pruebas y matriz coherentes; verificación exige CAM/evidencia. |
| T-22 | Predicción | Comparación reproducible entre base y mejora con semillas/escenarios y límites de información declarados. |
| T-23 | AWS y entrega | Salud/API/WebSocket, permisos/TLS, Budget, costos y entregables con evidencia real y enlaces comprobados. |
| T-24 | Variación y reproducción estocástica | Configuración/semilla/versiones/entradas idénticas reproducen; otra semilla y una perturbación controlada pueden divergir; la misma instantánea HTTP conserva la decisión. |
| T-25 | Caducidad de sesión humana local | TTL deslizante usa reloj monotónico; lectura válida renueva; una cookie vencida recibe 410 y ningún visitante distinto puede tomar el cupo/personaje reservado. No acredita expiración durable ni coordinación multiproceso. |
| T-26 | Operación del simulador de demo local | Control oculto sin opt-in; loopback y same-origin requeridos; inicio/pausa/continuación/reinicio se reflejan en un run publicado por el panel y validan entrada. |
| T-27 | Mapa cartográfico 3D y movimiento de actores | Compilación frontend, carga visual del estilo de Manta, atribución, controles 2D/3D, cámara que encuadra la envolvente del grafo OSM ampliado, controles «Todo Manta»/«Ver partida», fichas visibles por la zona, animación entre snapshots, actualización WebSocket tras iniciar otro run, edificios con altura y navegación limitada. T-38 verifica grafo y muestra territorial; límites del proveedor, OSM y payload quedan declarados. T-38 comprueba la ampliación jugable de la envolvente OSM, cobertura muestreada y rutas hacia refugios. Los límites OSM y el payload requieren evaluación adicional. |
| T-28 | Perfil sintético de amenazas por intensidad | En el fixture Manta, cada intensidad crea un conteo escalado al grafo, distribuye posiciones por varios sectores, conserva la composición del perfil y mantiene dormidos ocultos. La misma semilla/perfil/mapa reproduce composición, ubicaciones y fases. No valida densidad oficial. |
| T-29 | Incidentes viales en demo local | Los cierres aleatorios respetan semilla e intensidad, se aplican en el turno configurado y el panel publica metadatos solo luego de aplicarlos, sin revelar segmentos futuros. |
| T-30 | Prioridad de mordidas y ruta temporal | Una exposición futura mayor se evita aunque la ruta alternativa sea más larga; el comparador considera mejor cualquier resultado con menos mordidos aunque tenga menos evacuados y usa evacuados solo para desempatar. Verificación funcional; no acredita mejora universal ni seguridad real. |
| T-31 | Correspondencia de ruta y acción | Panel y decisión del servidor para el mismo snapshot/actor devuelven un mismo trayecto cacheado; al versionar un snapshot se invalida la ruta anterior. Los actores se calculan de forma independiente, sin bloquear toda la ronda en un único lock. |
| T-32 | Riesgo de cruces en rutas | El pronóstico visible estima la probabilidad de que un zombie use una arista opuesta del mismo segmento; un cruce confirmado afecta solo el turno actual y no se confunde con un cierre persistente. Dormidos y RNG privado permanecen fuera. |
| T-33 | Escape cuando no hay ruta completa | Si un zombie ocupa la única ruta hasta el refugio y hay un vecino libre, el planificador recomienda moverse hacia una salida; la acción y ruta mostrada coinciden. Si todos los vecinos están ocupados/cerrados, la espera sigue siendo válida. |
| T-34 | Evacuación terminal | Una persona evacuada en un nodo que luego ocupa una horda no vuelve a ser elegible para mordida; su estado permanece evacuado. |
| T-35 | Plan compartido y descongestión suave | En el mismo snapshot los pasos se asignan conjuntamente; con exposición equivalente se distribuyen por salidas alternativas legales, una nueva versión invalida el plan y la vista previa/action comparten la asignación. No se infieren capacidades ni seguridad garantizada. |
| T-36 | Límite del pronóstico | En una ruta más larga que el pronóstico, la exposición de turnos no modelados aporta cero al puntaje; no se repite la última condición conocida. |
| T-37 | Dificultad inicial de la demo | Sin intensidad en el control HTTP local, la demo usa intensidad media; eventos y selector siguen configurables. |
| T-38 | Mapa jugable ampliado de Manta | Conteos concuerdan con sidecar, sectores urbanos/rurales seleccionados tienen red cercana, cada nodo incluido puede alcanzar refugio en dirección de calles, y el campo de rutas compartido coincide con Dijkstra bajo cierres/bloqueos. Cobertura muestreada no es auditoría calle por calle ni límite municipal. |

## Medición de la prueba de fuego

Tres rondas consecutivas de cinco minutos, 150 turnos cada una. Máximo teórico si nadie sale antes: `150 × (20 + 80 + 200) = 45.000` solicitudes. Ronda 3 promedia 100 solicitudes/segundo, pero la carga decisiva es la ráfaga de 200.

Medir desde el cliente que llama `/paso`: inicio antes del envío y fin tras recibir respuesta completa. Registrar errores y timeouts, sin excluirlos para mejorar percentiles. Separar métricas internas de pruebas públicas desde una ubicación identificada. Registrar simultáneamente preparación, planificación, resolución y retraso del reloj de dos segundos.

Metas internas: p95 ≤150 ms, errores/timeouts <0,5 %, cero pasos inválidos generados y ningún retraso sostenido del reloj. Son objetivos; no escribir «cumplido» sin reporte real.

Rúbrica del endpoint: p95 ≤150 ms: 10; ≤300: 7; ≤500: 4; superior: 0. El contrato exige menos de 500 ms aunque la tabla use ese límite. Disponibilidad: errores/fuera de tiempo <0,5 %: 10; <2 %: 6; <5 %: 3; resto: 0. Fórmula exacta de eficiencia/supervivencia pendiente de aclaración; conservar datos sin inventar una equivalencia oficial.

## Comparación de políticas

Ejecutar Dijkstra y política mejorada sobre los mismos escenarios, versiones y lista de semillas, con semillas de validación distintas de las de ajuste. Guardar parámetros y cambios del generador. No escoger solo ejecuciones favorables. Reportar vivos, evacuados y pendientes por separado. Las trayectorias pueden divergir por persecución aunque se repita semilla.

## Evidencia y comandos

### T-26 — Control local y tablero del simulador

`cd backend && PYTHONPATH=src .venv/bin/python -m unittest tests.test_control_simulador_demo -v` comprueba que las rutas están ocultas sin opt-in, que conexiones remotas/orígenes ajenos se rechazan, que una configuración fuera de rango recibe 422 y que iniciar/pausar publica el mismo `runId`, modo y mapa por HTTP. `cd frontend && npm run build` verifica compilación del tablero/control. Esto no certifica una superficie administrativa pública, persistencia, cadencia sostenida o despliegue.

### T-27 — Cartografía 3D del panel

`cd frontend && npm run build` verifica compilación MapLibre/TypeScript. En navegador con red, revisar que el estilo vectorial de Manta cargue, se vea la atribución, el control alterne inclinación 2D/3D, la cámara encuadre la ventana cartográfica documentada, el exterior se enmascare, arrastrar no permita salir del recorte y el control no aleje más allá de la vista general. Revisar que las fichas distingan sobrevivientes/zombies, sus posiciones transiten con snapshots y un run iniciado desde esa pestaña actualice sin recarga; revisar además que la UI informe caída del renderer/tiles. CAM-052 agrega una regresión WebSocket de cambio de contexto y una prueba manual con 80 sobrevivientes; CAM-053 comprueba el recorte en 2D/3D y al arrastrar. La comprobación visual no certifica disponibilidad del proveedor, altura real de edificios, precisión cartográfica, límite administrativo ni seguridad de evacuación. El estado de fallo de proveedor/WebGL está implementado, pero no se inyectó una falla controlada en navegador.

### T-28/T-29 — Intensidad e incidentes sintéticos

`cd backend && PYTHONPATH=src .venv/bin/python -m unittest tests.test_demo tests.test_panel tests.test_control_simulador_demo -v` cubre densidad y reparto por sectores en el fixture de Manta, composición/semilla reproducible, ocultamiento de dormidos, inicio del control con intensidad y publicación de incidentes solo tras aplicar el cierre. `cd frontend && npm run build` comprueba los campos de configuración y la proyección del panel. Los perfiles son dificultad sintética; no representan densidades, eventos ni rutas oficiales.

### T-30 — Política de ruta con riesgo prioritario

`cd backend && PYTHONPATH=src .venv/bin/python -m unittest tests.test_decidir_paso tests.test_evaluacion_rutas -v` comprueba que una exposición futura observable prevalece sobre distancia, que el pronóstico se comparte por versión de snapshot y que la comparación ordena por mordidos ascendentes y evacuados descendentes. La integración usa horizonte máximo de 12 turnos, presupuesto por búsqueda y Dijkstra si la ruta temporal no termina. Para resultado emparejado, ejecutar `cd backend && PYTHONPATH=src .venv/bin/python -m navira.evaluacion_rutas --semillas 101 202 303 --escenarios caminantes mixto horda --poblaciones 20 80 200 --turnos 6 --horizonte 12`; es una prueba sintética local, no T-11 ni una garantía de menor mordida para cada semilla.

### T-31/T-32 — Previsualización exacta y cruces

`cd backend && env PYTHONPATH=tests .venv/bin/python -m unittest test_decidir_paso test_ruta_temporal test_prediccion_rutas -v` comprueba que panel/decisión llaman una vez al planificador por actor y snapshot, que un cruce zombie conocido solo bloquea el paso presente y que el pronóstico asigna exposición a la arista sobreviviente opuesta en segmentos bidireccionales. Estas pruebas validan coherencia de intención y regla de exposición; no demuestran menos mordidos en una partida aleatoria.

T-33 queda cubierto por `test_sin_ruta_completa_escapa_de_zombie_si_hay_vecino_libre` en `backend/tests/test_decidir_paso.py`, dentro de la suite de planificación indicada arriba. El desempate prioriza riesgo observable para el siguiente turno y después costo estático hacia un refugio; no promete que el camino futuro permanezca abierto.

T-34 queda cubierto por `test_sobreviviente_ya_evacuado_no_puede_ser_mordido_en_turnos_posteriores` en `backend/tests/test_resolver.py`. La mordida se evalúa solo para sobrevivientes activos al comenzar las decisiones; evacuar después de una resolución válida conserva el estado terminal.

T-35 queda cubierto parcialmente por `test_plan_compartido_reparte_un_embudo_sin_cambiar_reglas_de_riesgo` en `backend/tests/test_decidir_paso.py`. Confirma asignaciones distintas en un grafo mínimo y coincidencia con la recomendación. No mide mejora de mordidas en cohortes ni reglas de colisión del resolutor.

T-36 queda cubierto por `test_no_extiende_el_ultimo_riesgo_pronosticado_mas_alla_del_horizonte` en `backend/tests/test_decidir_paso.py`. Confirma que el planificador no interpreta como amenaza persistente un último turno pronosticado cuando ya no existe información para la cola de la ruta. No afirma que esos turnos desconocidos sean seguros; para esa cola solo decide el costo topológico disponible.

T-37 queda cubierto por `test_inicio_usa_dificultad_media_si_no_se_envia_configuracion` en `backend/tests/test_control_simulador_demo.py`. Comprueba el default en la petición de inicio local; `frontend/npm run build` valida el cambio de valor inicial de la UI. La compilación no sustituye una inspección visual interactiva de todos los selectores.

Frontend (CAM-068, F6): desde `frontend/`, `npm test` ejecuta vitest 5.0.5 sobre `src/domain/{panel,game,simulator}.test.ts` (19 pruebas en el lote 1; 27 correctas tras F3, CAM-070; `npm test` ejecuta 59 pruebas en 6 archivos tras F4 y F5, CAM-072, incluidas `mapFeatures.test.ts` y pruebas de infraestructura de `game`). Backend (CAM-069, que revierte el aplanado de CAM-067): `cd backend && PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py'` (178 pruebas tras CAM-069; 181 correctas, sin `-v`, tras CAM-071); el paquete vive en `backend/src/navira/`, se instala con `python -m pip install -e '.[test]'` y se arranca con `uvicorn navira.main:app --app-dir src`.

P0-04: desde `frontend/`, `npm ci && npm run build` verifica lockfile, TypeScript estricto y bundle de producción. La pantalla inicial soporta selección de modos con teclado mediante botones semánticos, estados `aria-pressed`, foco visible y movimiento reducido; revisar visualmente en anchos móvil y escritorio al cambiar el layout. `.github/workflows/ci.yml` ejecuta además la suite unittest y validadores documentales en GitHub Actions. La compilación local no demuestra que el workflow haya corrido en remoto.

Cada reporte debe incluir revisión de código, mapa, escenario, semilla, modo, parámetros, origen del cliente, fechas, métricas y limitaciones. Guardar en `docs/calidad/resultados/` cuando existan; no crear resultados ficticios.

Comprobación documental disponible: `python3 backend/scripts/check_docs.py`. El resto de comandos se documentará tras crear la aplicación; no suponer que `pytest`, un benchmark o un build ya están configurados.

Validación SDD disponible: `python3 backend/scripts/check_sdd.py` y regresiones del comprobador mediante `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`. T-20/T-21 verifican metodología documental; T-01 a T-19, T-22 a T-24 siguen pendientes total o parcialmente como pruebas de aplicación/operación. Referencias: [SPEC](../metodo/especificaciones/README.md), [trazabilidad](../metodo/trazabilidad.md).

El modelo de mapa tiene regresiones con `cd backend && PYTHONPATH=src python -m unittest discover -s tests -p 'test_mapa.py' -v`. Estas pruebas verifican el grafo y el filtrado de cierres; no prueban eventos temporales, turnos ni un dataset real de Manta.

Las entidades e intenciones tienen regresiones con `cd backend && PYTHONPATH=src python -m unittest discover -s tests -p 'test_modelo.py' -v`. Verifican identidad de partida/turno/fase y compatibilidad del contrato entre modos; no prueban aún la resolución de movimientos.

El resolutor de un turno tiene regresiones con `cd backend && PYTHONPATH=src python -m unittest discover -s tests -p 'test_resolver.py' -v` (11 pruebas). Cubren fases de caminante, dos tramos de corredor, horda, despertar, espera en movimiento inválido, mordidas por nodo y cada cruce, prioridad de mordida sobre llegada y uso del mismo resolutor en ambos modos. La regla exacta de dormidos, desempate del corredor y llegada siguen configurables/provisionales; esta suite no verifica ocultamiento de información.

El coordinador y reloj local tienen regresiones con `cd backend && PYTHONPATH=src python -m unittest discover -s tests -p 'test_coordinador.py' -v` (7 pruebas). Cubren snapshots/versiones, flujo de decisión y resolución separados para juego, cierre en turno objetivo y aplicación única, versión obsoleta, apertura del turno siguiente, referencias inválidas y plazo monotónico. No prueban escritura condicional real, concurrencia de procesos, recuperación durable ni un bucle de reloj continuo.

El puerto de persistencia y el adaptador local tienen regresiones con `cd backend && PYTHONPATH=src python -m unittest discover -s tests -p 'test_snapshots_persistidos.py' -v` (3 pruebas). Cubren ciclo CAS completo, rechazo de versión antigua, inserción duplicada y carrera de dos hilos donde solo un escritor gana. No prueban DynamoDB, múltiples procesos/hosts, apagado abrupto ni recuperación durable.

El contrato HTTP de base tiene pruebas con `cd backend && PYTHONPATH=src python -m unittest discover -s tests -p 'test_api_http.py' -v` (5 pruebas), cubriendo salud pública, autenticación ausente/incorrecta/configurada, forma exacta del éxito y rechazos 422. Además se probó localmente Uvicorn con `curl`: `/salud` 200, `/paso` autenticado 200 y sin clave 401. El smoke test no mide p95 ni valida rutas reales.

El núcleo Dijkstra tiene regresiones con `cd backend && PYTHONPATH=src python -m unittest discover -s tests -p 'test_dijkstra.py' -v` (7 pruebas). Cubren peso/distancia, factor configurable por tipo, cierres, nodos bloqueados, ruta inexistente, desempates, selección de refugio y validaciones. No prueban mapa de Manta ni peligros futuros.

La búsqueda temporal experimental tiene regresiones con `cd backend && PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_ruta_temporal.py' -v` (8 pruebas). Cubren espera, horizonte, cierres por fase, exposición inyectada, ruta completa y límites de expansión/tiempo. CAM-033 registra una medición serial local; no verifica pronóstico de amenazas, comparación contra Dijkstra, T-22 ni latencia HTTP.

El pronóstico observable tiene regresiones con `cd backend && PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_prediccion_rutas.py' -v` (5 pruebas). Comprueba mezcla de fase desconocida de caminantes, seguimiento provisional de corredor con sobrevivientes observados, bloqueo estático de horda, validación de datos y rechazo explícito de dormidos. No confirma las reglas oficiales de movimiento ni una probabilidad de supervivencia; CAM-034 aún no completa T-22.

`cd backend && PYTHONPATH=src .venv/bin/python -m navira.evaluacion_rutas --turnos 3` compara Dijkstra y temporal en 27 pares (tres perfiles sintéticos, tres semillas y cohortes 20/80/200), cada política en mundo reproducido e independiente. `test_evaluacion_rutas.py` verifica contrato de resultados y validación de parámetros. CAM-035 repite la matriz y confirma igualdad determinista de resultados; es evidencia T-22 parcial, no ronda oficial, latencia HTTP ni T-11.

El caso de uso de `/paso` tiene pruebas con `cd backend && PYTHONPATH=src python -m unittest discover -s tests -p 'test_decidir_paso.py' -v` para sesión/turno/fase/personaje, selección de ruta, cierres, hordas, zombies activos, dormidos ocultos y cruces conocidos. `test_api_planner_integration.py` valida respuesta con política inyectada y errores HTTP 404/409/503. `test_demo.py` comprueba el bootstrap de un snapshot local hacia decisiones, la ruta HTTP demo y que el ensamblaje base conserva espera. El modo demo usa exclusivamente `backend/data/maps/demo-sintetico.json`, no es el mapa de Manta ni ejecuta un reloj continuo.

`test_simulacion_automatica.py` verifica una ronda completa con Dijkstra, el orden de movimiento zombie antes de la recomendación, continuación desde fase de decisiones persistida, apertura del siguiente turno y rechazo de versión antigua/modo incompatible. La suite no mide un reloj continuo, durabilidad ni concurrencia entre procesos.

`test_juego_sesion.py` cubre P4B-01 local: sesión única por partida, dos intentos concurrentes, aparición reproducible en nodo no refugio con ruta, sesión idempotente por cookie, ausencia de candidato sin reservar cupo, partida de juego activa, espera fuera de fase PREPARACION, hook de incorporación previo a movimiento zombie, Origin/cookie HttpOnly-Secure-SameSite y T-25/CAM-046/049: renovación del TTL con reloj controlado; unión, recuperación y acción responden HTTP 410 y borran la cookie vencida; una cookie distinta recibe 409 y no toma el cupo actual. No cubre expiración durable/revocación productiva, DynamoDB, múltiples procesos, controles completos de acciones o recorrido de interfaz.

`test_ordenes_juego.py` cubre P4B-02/T-13/T-14 parcialmente (12 pruebas): cookie y propiedad, `Origin`, snapshot como autoridad de posición, fase/turno, vecino dirigido/cierre, bloqueo de horda, aceptación de riesgo por zombie activo, espera, idempotencia concurrente, conflicto al reutilizar `accionId` con otro cuerpo, reemplazo por secuencia del servidor y ausencia de movimiento al registrar. CAM-043 agrega dos pruebas HTTP de recuperación: se exigen la cookie existente, se lee la ubicación actual del snapshot y la última orden, y sin cookie no se crea otro personaje. El adaptador es memoria; aún no se prueba el consumo por el resolutor, cierre concurrente del turno, reloj límite, durable/multi-worker ni recorrido de navegador.

`test_coordinador_juego.py` cubre el avance P5-04 (2 pruebas): orden humana consumida junto al NPC por resolución común, rechazo de orden tardía y repetición de resolución, además de aparición tardía antes del movimiento zombie del siguiente turno. `test_demo.py` arranca `NAVIRA_GAME_DEMO=1`, espera el runner local de dos segundos y comprueba que volver a unirse conserva un personaje humano único. No verifica cadencia sostenida, recuperación tras reinicio, persistencia durable, TLS ni workers múltiples.

CAM-038 del frontend se comprueba con `cd frontend && npm run build`, que ejecuta TypeScript estricto y bundle Vite. CAM-041/042 agregan cuenta atrás y sugerencia opcional de radio; la última reutiliza la ruta observable del snapshot y requiere clic explícito. CAM-045 agrega skip link, foco visible también para el `select` y anuncio accesible por umbral de cierre; CAM-047 prueba manualmente en navegador el salto al contenido y selección de modos con Tab/Enter/Space. El flujo humano end-to-end no se completó porque el backend observado en el puerto 8000 ofrecía modo simulador y la instancia local de juego de prueba ya estaba terminal; tampoco se ejecuta lector de pantalla o auditoría WCAG. No hay runner de componentes y T-19 sigue parcial.

`test_simulacion_mapa_manta.py` ejecuta tres turnos de perfiles sintéticos sobre el fixture de Manta con 20/80/200 sobrevivientes, semilla fija y regla de movimiento del fixture; comprueba versión de mapa, inicios fuera de refugios y pasos vecinos o de espera. No verifica exactitud cartográfica ni seguridad de los refugios. El resultado exploratorio reproducible está en [CAM-025](resultados/simulacion-manta-cam025.md); no es una ronda oficial ni una medición de carga.

`test_simulador_demo.py` verifica el CLI local: limita rondas, imprime JSON por línea, reproduce escenario/semilla, registra la semilla generada si se omite, prueba variación posible de caminantes por semilla y divergencia de rutas en una trayectoria de varios turnos, omite dormidos en el reporte, evacúa el perfil libre y crea cohortes sintéticas de 20/80/200. `test_demo.py` confirma que repetir una solicitud sobre el mismo snapshot conserva decisión y versión. T-24 está cubierto parcialmente para replay local/variación; no cubre recuperación durable/versionado entre despliegues ni cascadas de eventos oficiales. El fixture pequeño tiene cuatro nodos no refugio, por lo que los personajes pueden compartir posición. CAM-020 incluye una ráfaga local concurrente por cohorte; fue un smoke de una sola ejecución con estado fijo y no cumple T-11, que requiere repeticiones/intervalo y medir en el entorno de evaluación.

`test_carga_http.py` verifica agregación de conteos, errores y percentiles mediante un emisor controlado; `test_demo.py` valida el ensamblaje de cohortes por argumentos y variables de entorno. Para llamar transporte HTTP real, iniciar Uvicorn con `NAVIRA_DEMO=1`, `NAVIRA_DEMO_SURVIVORS` y `NAVIRA_DEMO_SEED` iguales al cliente y correr `python -m navira.carga_http`. Los resultados del smoke local CAM-020 están en [carga local](resultados/carga-local-cam020.md); no reemplazan T-11 contra el entorno/ubicación de evaluación.

El evaluador `python -m navira.evaluacion_local` crea un servidor Uvicorn de loopback, envía solicitudes autenticadas a `/paso` para cada sobreviviente activo, usa los destinos HTTP como intenciones y avanza el snapshot al terminar la ráfaga del turno. Programa los inicios con reloj monotónico; `--periodo-segundos` configura la cadencia, con valor predeterminado de 2 s. Registra intervalo/retraso de inicio y duración del ciclo para detectar sobrepasos. Ejemplo corto: `--turnos 3 --poblaciones 20 80 200 --concurrencia 200 --semilla 20261026 --periodo-segundos 2`. La clave de servicio es aleatoria y temporal y no aparece en el JSON. `test_evaluacion_local.py` comprueba contrato, versiones, avance de turnos y cadencia HTTP. Evidencia CAM-028 y CAM-029 en [reporte multi-turno](resultados/evaluacion-multi-turno-cam028.md) y [reporte temporizado](resultados/evaluacion-cadencia-cam029.md). CAM-044 solicitó 150 turnos por cohorte, pero el juego sintético finalizó en 12/15/13; p95 y cadencia cumplen las metas en esa muestra corta, no hay cinco minutos por cohorte ni repeticiones y no se usa entorno remoto/composición oficial. T-11 y las rondas oficiales siguen pendientes.
