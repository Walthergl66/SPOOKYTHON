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
| T-04 | Dormido | No visible ni utilizable por motor antes de activación. |
| T-05 | Coincidencia/cruce | Mordida final o sentido opuesto, incluidos ambos tramos de corredor. |
| T-06 | Orden de turno | Misma fase del mundo para todos; zombies antes de decisiones. |
| T-07 | Cierre en vivo | El grafo filtra arista dirigida o segmento físico cerrado; una regresión confirma activación por turno en el coordinador en memoria. |
| T-08 | Sin ruta/timeout | Acción válida o espera; sin falsa garantía de seguridad. |
| T-09 | Refugio | Estado final correcto según orden acordado de mordida/llegada. |
| T-10 | Repetición/reinicio | Misma decisión en misma instantánea; ninguna caché cruza partidas. |
| T-11 | Ráfaga | 20, 80 y 200 solicitudes concurrentes cada dos segundos. |
| T-12 | Aparición humana | Nodo elegible y solicitud tardía incorporada en turno correcto. |
| T-13 | Propiedad/acciones | Otra sesión no controla; clics múltiples no conceden pasos extra. |
| T-14 | Órdenes tardías/duplicadas | Rechazo o acuse idempotente; no aplicar al turno siguiente. |
| T-15 | Reconexión | Estado confirmado, sin detener mundo o revivir. |
| T-16 | Separación de modos | Rondas oficiales sin humanos ni cambio de modo. |
| T-17 | Paridad | Mismo estado e intenciones dan mismo resultado con control humano o automático; hay una regresión del resolutor, aún parcial. |
| T-18 | Snapshot/recuperación | El coordinador genera estados completos; un adaptador local CAS bajo lock admite un solo escritor por versión. Persistencia durable y recuperación entre procesos siguen pendientes. |
| T-19 | Accesibilidad | Juego y selección por teclado, foco visible y estados no basados solo en color. |
| T-20 | Documentación | Enlaces locales válidos e inventario completo. |
| T-21 | Integridad SDD | IDs, requisitos, tareas, CA, pruebas y matriz coherentes; verificación exige CAM/evidencia. |
| T-22 | Predicción | Comparación reproducible entre base y mejora con semillas/escenarios y límites de información declarados. |
| T-23 | AWS y entrega | Salud/API/WebSocket, permisos/TLS, Budget, costos y entregables con evidencia real y enlaces comprobados. |

## Medición de la prueba de fuego

Tres rondas consecutivas de cinco minutos, 150 turnos cada una. Máximo teórico si nadie sale antes: `150 × (20 + 80 + 200) = 45.000` solicitudes. Ronda 3 promedia 100 solicitudes/segundo, pero la carga decisiva es la ráfaga de 200.

Medir desde el cliente que llama `/paso`: inicio antes del envío y fin tras recibir respuesta completa. Registrar errores y timeouts, sin excluirlos para mejorar percentiles. Separar métricas internas de pruebas públicas desde una ubicación identificada. Registrar simultáneamente preparación, planificación, resolución y retraso del reloj de dos segundos.

Metas internas: p95 ≤150 ms, errores/timeouts <0,5 %, cero pasos inválidos generados y ningún retraso sostenido del reloj. Son objetivos; no escribir «cumplido» sin reporte real.

Rúbrica del endpoint: p95 ≤150 ms: 10; ≤300: 7; ≤500: 4; superior: 0. El contrato exige menos de 500 ms aunque la tabla use ese límite. Disponibilidad: errores/fuera de tiempo <0,5 %: 10; <2 %: 6; <5 %: 3; resto: 0. Fórmula exacta de eficiencia/supervivencia pendiente de aclaración; conservar datos sin inventar una equivalencia oficial.

## Comparación de políticas

Ejecutar Dijkstra y política mejorada sobre los mismos escenarios, versiones y lista de semillas, con semillas de validación distintas de las de ajuste. Guardar parámetros y cambios del generador. No escoger solo ejecuciones favorables. Reportar vivos, evacuados y pendientes por separado. Las trayectorias pueden divergir por persecución aunque se repita semilla.

## Evidencia y comandos

Cada reporte debe incluir revisión de código, mapa, escenario, semilla, modo, parámetros, origen del cliente, fechas, métricas y limitaciones. Guardar en `doc/resultados/` cuando existan; no crear resultados ficticios.

Comprobación documental disponible: `python3 scripts/check_docs.py`. El resto de comandos se documentará tras crear la aplicación; no suponer que `pytest`, un benchmark o un build ya están configurados.

Validación SDD disponible: `python3 scripts/check_sdd.py` y regresiones del comprobador mediante `python3 -m unittest discover -s tests -p 'test_check_sdd.py'`. T-20/T-21 verifican metodología documental; T-01 a T-19 y T-22/T-23 siguen pendientes como pruebas de aplicación/operación. Referencias: [SPEC](especificaciones/README.md), [trazabilidad](trazabilidad.md).

El modelo de mapa tiene regresiones con `python -m unittest discover -s tests -p 'test_mapa.py' -v`. Estas pruebas verifican el grafo y el filtrado de cierres; no prueban eventos temporales, turnos ni un dataset real de Manta.

Las entidades e intenciones tienen regresiones con `python -m unittest discover -s tests -p 'test_modelo.py' -v`. Verifican identidad de partida/turno/fase y compatibilidad del contrato entre modos; no prueban aún la resolución de movimientos.

El resolutor de un turno tiene regresiones con `python -m unittest discover -s tests -p 'test_resolver.py' -v` (11 pruebas). Cubren fases de caminante, dos tramos de corredor, horda, despertar, espera en movimiento inválido, mordidas por nodo y cada cruce, prioridad de mordida sobre llegada y uso del mismo resolutor en ambos modos. La regla exacta de dormidos, desempate del corredor y llegada siguen configurables/provisionales; esta suite no verifica ocultamiento de información.

El coordinador y reloj local tienen regresiones con `python -m unittest discover -s tests -p 'test_coordinador.py' -v` (7 pruebas). Cubren snapshots/versiones, flujo de decisión y resolución separados para juego, cierre en turno objetivo y aplicación única, versión obsoleta, apertura del turno siguiente, referencias inválidas y plazo monotónico. No prueban escritura condicional real, concurrencia de procesos, recuperación durable ni un bucle de reloj continuo.

El puerto de persistencia y el adaptador local tienen regresiones con `python -m unittest discover -s tests -p 'test_snapshots_persistidos.py' -v` (3 pruebas). Cubren ciclo CAS completo, rechazo de versión antigua, inserción duplicada y carrera de dos hilos donde solo un escritor gana. No prueban DynamoDB, múltiples procesos/hosts, apagado abrupto ni recuperación durable.

El contrato HTTP de base tiene pruebas con `python -m unittest discover -s tests -p 'test_api_http.py' -v` (5 pruebas), cubriendo salud pública, autenticación ausente/incorrecta/configurada, forma exacta del éxito y rechazos 422. Además se probó localmente Uvicorn con `curl`: `/salud` 200, `/paso` autenticado 200 y sin clave 401. El smoke test no mide p95 ni valida rutas reales.
