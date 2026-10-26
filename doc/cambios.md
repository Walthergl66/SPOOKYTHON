# Historial de cambios y contexto

Registro acumulativo. No reemplaza commits; al existir un repositorio operativo, enlazar revisión real sin inventarla. Las dos primeras entradas se reconstruyen de esta conversación, no de un historial Git comprobado.

## CAM-040 — Reloj y juego demo local

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para implementar las fases pendientes y mantener commits separados.
- Especificación/tarea: SPEC-004, P5-04 parcial; PRD-05/06, TRD-03/04/05/06/09/12; T-12/T-14/T-15/T-16/T-19 parciales. No verifica SPEC-004 ni completa P5-04.
- Motivo: hacer ejecutable localmente el juego humano sobre el coordinador CAM-039, con cierre de turno autoritativo y recuperación del mismo personaje al volver a unirse.
- Resultado: `PuertaDecisiones` comparte lock y deadline monotónico; rechaza órdenes nuevas al vencimiento y conserva los acuses idempotentes. `RelojJuegoLocal` arranca/detiene con lifespan ASGI, abre ventanas de 1,7 s y alinea ciclos nominales de 2 s. `NAVIRA_GAME_DEMO=1` ensambla juego sintético y servicios efímeros. Vite reenvía `/juego` junto a panel/WebSocket.
- Archivos: coordinador/puerta/reloj de aplicación, ensamblaje `main.py`, `demo.py`, tests del coordinador y `test_demo.py`, `frontend/vite.config.ts`, README raíz/frontend; contratos API, módulos, flujos de jugador/simulador, pruebas, SPEC-004, trazabilidad, plan, pendientes y estado.
- Decisión: el game demo es opt-in y usa mapa sintético, un hilo/proceso, snapshots/sesiones/órdenes en memoria. No altera el modo demo del simulador ni el contrato `/paso`. Cualquier despliegue requiere TLS, expiración/revocación de sesión y almacenamiento/coordinación durables.
- Verificación: suite completa (147 pruebas OK); `frontend/npm run build`; `python3 scripts/check_docs.py` (67 Markdown/69 archivos); `python3 scripts/check_sdd.py` (seis SPEC) y regresiones del validador (8 OK); `compileall`, `git diff --check`. Smoke HTTP ASGI con semilla 45 avanzó de turno 0 a 1 y una segunda llamada a unirse devolvió el mismo `jugadorId`; es una sola ejecución local, no métrica sostenida.
- Límites: no hay temporizador visible en UI, radio, sesión con expiración, recuperación tras caída/reinicio, persistencia durable, multi-worker, TLS/despliegue ni prueba sostenida de cadencia. El fixture demo no representa Manta. P5-04 y T-14/T-15/T-19 permanecen parciales.
- Siguiente paso: completar UI de deadline/resultado y la recuperación tras desconexión; revisar seguridad de sesión y luego retomar P5-02 antes de considerar despliegue.
- Commit: se crea commit local individual en `master`.

## CAM-039 — Integración local del ciclo de juego

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario para avanzar las fases restantes y mantener cambios separados en `master`.
- Especificación/tarea: SPEC-004, P5-04 parcial; PRD-05/06, TRD-03/04/05/06/09/12; T-12/T-14/T-16 parciales. No verifica SPEC-004.
- Motivo: conectar sesión/aparición y órdenes humanas con el ciclo versionado y el mismo resolutor utilizado por los personajes automáticos.
- Resultado: `CoordinadorJuego.preparar()` incorpora una aparición pendiente antes de mover zombies, prepara/retoma decisiones con CAS y no repite movimiento al reintentar. `resolver()` consume la última orden humana aceptada o espera si falta; calcula intenciones de NPC por `DecidirPaso` y confirma una resolución conjunta. `RegistrarOrdenHumana` acepta una puerta `RLock` opcional para que el integrador la comparta y serialice el registro frente al cierre/resolución en un proceso.
- Archivos principales: `src/navira/application/coordinador_juego.py`, `src/navira/application/ordenes.py`, `tests/test_coordinador_juego.py`; SPEC-004, flujo jugador, módulos backend, pruebas, plan, trazabilidad, pendientes y estado actual.
- Decisión: integrar mediante aplicación sobre puertos existentes y CAS, sin duplicar reglas ni modificar el resolutor. No se crea reloj/worker hasta definir e implementar el deadline monotónico. El lock compartido no es multiproceso.
- Verificación: pruebas enfocadas de coordinador y órdenes: 12 OK; suite completa (`PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v`): 146 OK; `python3 scripts/check_docs.py` (67 Markdown/69 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho pruebas `test_check_sdd.py`, `compileall` y `git diff --check` correctos.
- Límites: integración aún no ensamblada en `main.py`/demo; no hay ciclo continuo, plazo 1,7 s, recuperación durable/tras reinicio, T-14/T-15/T-19 integral, radio, TLS ni sesión con expiración. Un método `resolver()` no debe llamarse antes del cierre temporal cuando se añada el runner.
- Siguiente paso: P5-04, implementar ventana monotónica compartida, cierre atómico y runner local opt-in; luego validar reconexión/resultado end-to-end.
- Commit: commit local individual en `master` tras ejecutar las validaciones declaradas.

## CAM-038 — Controles humanos en frontend

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases restantes, con un commit individual por fase en `master`.
- Especificación/tarea: SPEC-004, P4B-03 parcial; inicia evidencia T-19 sin completar T-19 ni verificar la SPEC.
- Motivo: convertir la selección «Jugar» en una interfaz que consuma sesión/órdenes y deje claro el momento en que una intención fue recibida frente al movimiento confirmado.
- Resultado: el panel añade controles de unión, posición propia, espera y vecinos dirigidos habilitados; muestra peligro observable por zombies activos, bloqueos de horda, envío, acuse/error y reintento de red con el mismo `accionId`. Los controles se deshabilitan cuando el snapshot no está fresco o no se aceptan decisiones. La identidad se recupera mediante cookie same-origin HttpOnly, sin guardar token en JavaScript. El modo juego informa que la instancia predeterminada no tiene partida habilitada.
- Decisión: reutilizar el mapa/snapshot de `WS /ws/panel` y los contratos CAM-036/037; no hacer movimiento optimista ni crear partidas desde la selección de modo.
- Archivos: `frontend/src/features/game/GameControls.tsx`, `frontend/src/shared/api/game.ts`, `frontend/src/app/App.tsx`, `frontend/src/styles.css`; módulos frontend, flujo de jugador, pruebas, SPEC-004, trazabilidad, plan, estado e historial.
- Verificación: `frontend/npm run build` compila TypeScript y Vite; suite backend completa (144 pruebas OK); `python3 scripts/check_docs.py` (67 Markdown/69 archivos); `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas); ocho pruebas del validador SDD; `compileall` y `git diff --check` correctos. Smoke de navegador local mostró snapshot real del simulador, selector de modo y estado en vivo. No hubo recorrido de los controles de una partida porque el backend demo no ensambla un modo de juego activo.
- Límites: UI inicial, sin radio ni temporizador/cierre autoritativo; el backend aún no arma el ciclo humano y el endpoint puede responder 503 en la app predeterminada. No se acredita recorrido jugable, T-19 WCAG, durable, reconexión de sesión tras reinicio, seguridad real del mapa ni despliegue.
- Siguiente acción: P5-04, ensamblar un ciclo local modo juego que llame aparición antes de zombies, consuma orden humana junto a órdenes automáticas y publique resultados confirmados; definir cierre monotónico/atómico (P-16) antes de T-14 integral.
- Commit: individual local en `master` después de validaciones locales.

## CAM-037 — Órdenes humanas idempotentes

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases restantes, con un commit individual por fase en `master`.
- Especificación/tarea: SPEC-004, P4B-02; aporta evidencia parcial a T-13/T-14, pero no completa sus criterios ni verifica la SPEC.
- Motivo: recibir intención humana sin confiar en posición/identidad del cliente, permitir reintentos de red y reemplazar una orden válida antes de resolver el turno.
- Resultado: `POST /juego/accion` autentica sesión/origen, comprueba run, personaje humano activo, modo/turno/fase y destino dirigido habilitado. Rechaza cierres topológicos y bloqueos de horda; no rechaza un nodo por riesgo de zombie activo. `OrdenHumana` conserva versión de snapshot; `RepositorioOrdenesMemoria` serializa `accionId`, secuencia creciente por partida y última orden por personaje/turno. Repetir la misma acción y cuerpo devuelve su acuse original; variar cuerpo con la misma clave devuelve 409.
- Decisión: se implementa el contrato existente de [orden humana](contratos/api.md), sin cambiar el movimiento confirmado ni el orden común de resolución. El repositorio volátil se ubica en `adapters/`; `application/ordenes.py` solo define el puerto y el caso de uso.
- Archivos: `src/navira/application/ordenes.py`, `src/navira/adapters/ordenes_memoria.py`, schemas/ruta/ensamblaje API y `tests/test_ordenes_juego.py`; módulos, contrato, datos, ODDD, flujo, seguridad, pruebas, pendientes, SPEC-004, plan, trazabilidad, estado e historial.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_ordenes_juego.py' -v` (10 OK) y suite completa (`144` pruebas OK); `python3 scripts/check_docs.py` (67 Markdown/69 archivos); `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas); `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 OK); `compileall`, `git diff --check` y `frontend/npm run build` correctos. La salida de uso inválido del CLI es el caso negativo esperado en la suite.
- Límites: el adaptador es memoria de un proceso; el coordinador todavía no consume el resultado ni comparte transacción con las órdenes. El cierre solo se contrasta con la fase actual; no hay deadline monotónico ni cierre atómico contra una solicitud concurrente. No se afirma persistencia durable ni T-14 completo (P-16).
- Siguiente acción: P4B-03, controles y estado de personaje en UI usando la cookie same-origin; luego conectar aparición, bandeja de órdenes y cierre de turno al ciclo de juego antes de afirmar recorrido jugable.
- Commit: individual local en `master` después de validaciones locales.

## CAM-036 — Sesión propietaria y aparición humana local

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario para construir las fases restantes, con un commit independiente por fase en `master`.
- Especificación/tarea: SPEC-004, P4B-01; aporta evidencia parcial a T-12/T-13, pero no verifica la SPEC ni completa T-12/T-13.
- Motivo: habilitar la entrada del jugador humano al modo juego sin aceptar posición del navegador, reservar más de un propietario o revelar información privada de zombies dormidos.
- Resultado: caso de uso `UnirseAJuego`, repositorio local de sesiones que conserva solo hash SHA-256 del token y `POST /juego/unirse` con cookie opaca `HttpOnly`, `Secure` por defecto, `SameSite=Strict`, `Path=/juego` y validación de Origin same-host. La aparición usa RNG privado versionado para escoger un nodo elegible no-refugio, no ocupado por sobrevivientes/zombies activos, no bloqueado y con ruta a refugio. Una entrada posterior a PREPARACION queda pendiente para un hook que el coordinador debe llamar antes del movimiento zombie.
- Decisión: [ADR-013](decisiones/0013-sesion-y-aparicion-humana-local.md). Un solo propietario humano; sesión y snapshot permanecen en adaptadores separados, locales y volátiles.
- Archivos: `src/navira/application/juego.py`, `src/navira/api/routes.py`, `src/navira/api/schemas.py`, `src/navira/main.py`, `tests/test_juego_sesion.py`; API, datos, ODDD, seguridad, flujo de jugador, módulos, pruebas, SPEC-004, plan, trazabilidad e índices.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_juego_sesion.py' -v` (7 pruebas OK); suite completa (`134` pruebas OK); `python3 scripts/check_docs.py` (67 Markdown/69 archivos); `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas); `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 OK); `compileall`, `git diff --check` y `frontend/npm run build` correctos. La salida de uso inválido del CLI dentro de la suite es el caso negativo esperado.
- Límites: el hook todavía no se invoca desde el coordinador, el modo predeterminado no ensambla el servicio, no existen órdenes/autorización de acciones ni UI jugable, y las sesiones no expiran ni sobreviven reinicios. P-11/P-12 siguen abiertas. La aparición CAS y el repositorio de sesiones no forman una transacción durable.
- Siguiente acción: P4B-02, registro de órdenes humanas con propiedad, fase/turno, idempotencia por `accionId`, sustitución atómica y acuse sin mover directamente al personaje.
- Commit: uno local e individual en `master` después de cerrar todas las comprobaciones locales.

## CAM-035 — Comparación emparejada de políticas de ruta

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario de las fases restantes, con un commit individual por fase en `master`.
- Especificación/tarea: SPEC-002, P3-03 y T-22 parcial; usa P3-01/CAM-033 y P3-02/CAM-034. No completa T-11 ni SPEC-002.
- Motivo: comparar Dijkstra y la candidata temporal bajo mundos emparejados, conservando línea base ante límites o falta de evidencia operativa.
- Resultado: CLI reproducible `python -m navira.evaluacion_rutas`; avanza ambos mundos de forma independiente con misma semilla/perfil/población y un snapshot versionado, calcula recomendaciones desde proyección observable, aplica el mismo resolutor y reporta evacuados/mordidos/activos, fallback y tiempos de funciones.
- Decisión: [ADR-012](decisiones/0012-seleccion-politica-baseline.md). Dijkstra se mantiene activa en `/paso`; el candidato temporal queda solo en el evaluador hasta reglas y medición HTTP concurrente.
- Archivos: `src/navira/evaluacion_rutas.py`, `src/navira/routing/prediccion.py` (búsqueda de objetivo de corredor acotada por alcance), `tests/test_evaluacion_rutas.py`; pruebas, módulo backend, SPEC-002, plan, matriz, reporte, ADR e índices/estado.
- Verificación/evidencia: 27 pares (3 perfiles sintéticos × 3 semillas × poblaciones 20/80/200), 3 turnos por partida, repetidos dos veces con idénticos resultados de mundo; ver [reporte CAM-035](resultados/comparacion-rutas-cam035.md). Temporal sumó 15 evacuados, igualó mordidas; fue mejor en 15 pares, igual en 12, peor en ninguno. Suite completa (`127` pruebas OK), `python3 scripts/check_docs.py` (66 Markdown/68 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructurales), pruebas del validador SDD (8 OK), `compileall`, `git diff --check` y `frontend/npm run build` correctos. Suma de observaciones, no inferencia estadística ni supervivencia.
- Límites: los mundos son sintéticos y cortos; el predictor conserva supuestos provisionales; el tiempo reportado es de funciones locales, no HTTP/latencia concurrente. `2.027` recomendaciones recurrieron a Dijkstra por falta de ruta dentro del horizonte/limitación. T-22 es parcial y T-11 pendiente.
- Siguiente acción: completar validación end-to-end de P3-03/T-11 cuando corresponda, sin activar temporal en `/paso` antes de verificar p95 desde cliente y reglas aceptadas. Después priorizar sesión de juego local, manteniendo AWS/publicación como dependencias externas.
- Commit: individual local en `master`, tras cerrar verificaciones.

## CAM-034 — Pronóstico observable de amenazas por escenarios

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases restantes, con un commit por fase en `master`.
- Especificación/tarea: SPEC-002, P3-02 parcial; enlaza con P3-01/CAM-033 y CA-002-05. La comparación de políticas T-22 queda para P3-03.
- Motivo: proveer condiciones futuras para el buscador temporal sin entregarle fase privada, estado completo de partida o RNG.
- Resultado: pronóstico por fases de ocupación de caminantes, corredores y hordas observables, compatible con `CondicionTurno`. El resultado enumera supuestos y produce un puntaje de exposición, nunca probabilidad calibrada.
- Decisión: [ADR-011](decisiones/0011-pronostico-visible-por-escenarios.md). Caminantes mezclan fases desconocidas y bifurcan uniformemente por salidas; los corredores persiguen con posiciones actuales de sobrevivientes congeladas; las hordas mantienen bloqueo estático provisional. Dormidos son rechazados.
- Archivos: `src/navira/routing/prediccion.py`, `tests/test_prediccion_rutas.py`, algoritmo, módulos, SPEC-002, plan, trazabilidad, pruebas, ADR e índices.
- Verificación: suite completa (`125` pruebas OK; incluye 5 de pronóstico), `python3 scripts/check_docs.py` (64 Markdown/66 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas), `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 OK), `compileall`, `git diff --check` y `frontend/npm run build` correctos. El mensaje CLI de argumentos inválidos es la salida esperada de una prueba negativa.
- Límites: no usa el estado/RNG privados y no se integra en `/paso`; la salida del corredor presupone sobrevivientes quietos, la horda no se mueve y la mezcla uniforme no valida distribuciones oficiales. No demuestra T-22, supervivencia ni latencia. P3-02 queda parcial hasta cerrar sus dependencias de reglas/evaluación.
- Siguiente acción: P3-03 compara Dijkstra con búsqueda temporal/pronóstico en escenarios y semillas declarados; mantener Dijkstra salvo mejora replicable y dentro del presupuesto.
- Commit: individual local en `master`, al completar verificaciones.

## CAM-033 — Núcleo de búsqueda temporal acotada

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases restantes, con un commit por fase en `master`.
- Especificación/requisitos/tareas: SPEC-002, P3-01, CA-002-05 parcial. P3-02/P3-03, T-11/T-22 y la verificación integral de SPEC-002 siguen pendientes.
- Motivo: explorar planificación por turnos con espera y riesgos observables, con presupuesto explícito, antes de sustituir Dijkstra.
- Resultado: módulo puro de búsqueda temporal `(nodo, turnos)`, acciones de espera/movimiento, cierres y exposición futura inyectados. Costo lexicográfico de exposición, turnos, metros ponderados y desempate estable. Límite de horizonte, expansiones y tiempo; ante agotamiento o falta de refugio en horizonte no se retorna una ruta parcial.
- Decisión: [ADR-010](decisiones/0010-busqueda-temporal-acotada.md). El módulo no se integra en `/paso`, no genera pronósticos, no consume RNG ni conoce dormidos; Dijkstra permanece como política activa.
- Archivos: `src/navira/routing/temporal.py`, `tests/test_ruta_temporal.py`; algoritmo, módulo backend, plan, SPEC-002, matriz de trazabilidad, pruebas, ADR, reporte e índices/estado.
- Evidencia: [reporte CAM-033](resultados/busqueda-temporal-cam033.md), una única medición serial sobre fixture parcial de Manta con escenario sintético `mixto`, semilla `20261026`, horizonte 6 y presupuesto 25 ms. Cohortes 20/80/200: p95 de función 1,331/1,514/1,291 ms; no es HTTP, T-11, T-22, medición de ronda ni evidencia de supervivencia.
- Verificación de cierre: suite completa (`120` pruebas OK; incluye 8 de ruta temporal), `python3 scripts/check_docs.py` (63 Markdown/65 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas), `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 OK), `compileall`, `git diff --check` y `frontend/npm run build` correctos. El mensaje CLI de `argparse` dentro de la suite es una salida esperada de una prueba que verifica argumentos inválidos; la suite termina OK.
- Límites: condiciones futuras son entradas de prueba/puerto, no una predicción implementada; reglas P-02/P-03/P-07/P-09 siguen abiertas. Un horizonte sin ruta no demuestra que el destino sea inalcanzable. P3-01 no termina T-22 ni SPEC-002.
- Siguiente acción: P3-02, construir pronóstico observable sin revelar dormidos ni estado privado, revisando reglas y pendientes; preservar Dijkstra hasta comparar.
- Commit: individual local en `master`, se completa al cerrar verificaciones.

## CAM-032 — WebSocket de snapshots completos y recuperación del panel

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases restantes; un commit separado por fase en `master`.
- Especificación/requisitos/tareas: SPEC-003, P4-02, CA-003-02 y T-15 local. No cierra la SPEC integral ni cubre sesión de juego.
- Motivo: que el panel reciba turnos confirmados y se recupere de desconexiones sin aplicar deltas faltantes o mezclar partidas.
- Resultado: `WS /ws/panel` entrega snapshot observable inmediato y snapshot completo ante cambio de `(runId, snapshotVersion)`, heartbeat cada 2 s y rechazo de handshake con otro/missing origin. Poll de clave cada 250 ms; cada conexión reconectada comienza desde la versión vigente. La UI valida los sobres, aplica secuencia, cambia de run sin conservar el snapshot anterior, presenta conexión/desactualización y usa backoff exponencial. Predicción Dijkstra no se calcula fuera de la fase de decisiones.
- Decisión: [ADR-009](decisiones/0009-panel-ws-snapshots-completos.md), snapshot completo en vez de delta/buffer porque el almacenamiento actual es en memoria, no outbox durable.
- Archivos principales: `src/navira/api/routes.py`, `application/consultar_panel.py`, `tests/test_panel.py`, cliente React `frontend/src/shared/realtime/panel.ts`, API de mapa, `App.tsx` y proxy; contrato de eventos/API, seguridad, arquitectura, módulos, flujo de espectador, SPEC-003, plan, pruebas, trazabilidad, índice, ADR, README y estado.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py'` (112 pruebas OK); `python3 scripts/check_docs.py` (61 Markdown en `doc/`, 63 archivos); `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas); `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 OK); `compileall`, `git diff --check` y `frontend/npm run build` correctos. Las 12 pruebas enfocadas de `test_panel.py` comprueban snapshot inicial, cambio de versión/fase/run, heartbeat, origen cross-origin y reconexión a secuencia posterior. Smoke visual local a través de Vite/Uvicorn confirmó `EN VIVO`.
- Límites: almacenamiento volátil y único proceso; la conexión requiere mismo host y un Origin browser; no hay outbox, historial de deltas, límites por conexión, multi-worker, sesión/órdenes de juego ni despliegue. No se verificó desconexión real del navegador; el smoke solo comprobó conexión viva. El mapa Manta sigue parcial y no es una guía de emergencia.
- Siguiente acción: P3-01, búsqueda temporal acotada sobre el snapshot/política Dijkstra, manteniendo P2-03 como referencia/evaluación parcial y sin afirmar que la evaluación oficial ya está completa.
- Commit: se crea commit local individual de P4-02 en `master`, después de cerrar suite/validadores.

## CAM-031 — Proyección inicial de mapa y estado para el panel

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases pendientes, con commits individuales en `master`.
- Especificación/requisitos/tareas: SPEC-003 sigue lista; PRD-04/06 y TRD-05/07/09; P4-01 verificado para mapa/capas/ruta/métricas con consulta manual. P4-02/CA-003-02 continúa pendiente. T-04 y primer tramo de ruta tienen regresiones.
- Motivo: alimentar el panel con un snapshot confirmado y una versión de mapa coherente, evitando exponer dormidos o estado privado.
- Resultado: `GET /panel/estado` devuelve sin partida o proyección activa; `GET /panel/mapa` entrega el grafo de la versión activa. Ambas lecturas no requieren API key maestra ni mutan el mundo. La proyección incluye rutas dirigidas completas por sobreviviente activo con la política Dijkstra/peligros visibles compartida con `/paso`. La UI valida formato y versión, permite elegir personaje para dibujar su ruta, presenta modo real del servidor y deja el selector de modo como vista previa.
- Archivos principales: `src/navira/application/consultar_panel.py`, schemas/rutas/API y ensamblaje; `tests/test_panel.py`; `frontend/src/shared/api/panel.ts`, `features/map/CityMap.tsx`, `app/App.tsx`, estilos y proxy Vite. Documentos propietarios: contratos, datos, módulos, espectador, seguridad, pruebas, SPEC-003, trazabilidad, plan, índice, README y estado.
- Decisión/ADR: se sigue la ruta de lectura limitada ya prevista en `doc/contratos/api.md` y el flujo de espectador; no altera `/paso` o el contrato del reto, por lo que no requiere ADR nueva.
- Verificación: suite completa (106 pruebas OK), `python3 scripts/check_docs.py` (60 Markdown en `doc/`, 62 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas) y `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 pruebas OK); `compileall`, `git diff --check`, `npm ci` (24 paquetes, cero vulnerabilidades reportadas) y `npm run build` correctos. Smoke navegador local con Uvicorn/Vite y fixture Manta: muestra versión `manta-osm-d76772f9d9e9`, 300 nodos y 4 refugios. Una medición local única de `consultar_estado()` observó 12,12/42,68/101,47 ms para cohortes 20/80/200; no son percentiles ni medición del endpoint remoto.
- Límites: la fixture tiene cobertura parcial, no certifica seguridad sísmica ni es guía de emergencia. Las rutas se limitan al snapshot y no predicen futuro o garantizan seguridad. No hay consulta automática/WebSocket/reconexión ni endpoint de panel desplegado. El CI remoto no se ejecutó.
- Siguiente acción: P4-02 implementa transporte de eventos/frescura/reconexión; los criterios de actualización en vivo quedan pendientes.
- Commit: commit individual de P4-01 en `master`, registrado tras cerrar sus verificaciones.

## CAM-030 — Base compilable del frontend y CI

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario para avanzar las fases restantes, creando un commit separado por fase.
- Especificación/requisitos/tareas: SPEC-003 lista; PRD-04/PRD-06, TRD-05/07/09; P0-04 verificada por sus criterios locales. CA-003-01..04 permanecen pendientes porque no hay panel conectado.
- Motivo: habilitar una base frontend ejecutable y automatizar verificaciones antes de construir el panel real.
- Resultado: scaffold React + TypeScript + Vite, vista inicial responsiva Navira, selector local de los modos simulador/juego y estado explícito sin partida. La imagen costera es ilustrativa, no cartografía de navegación. Workflow Actions ejecuta suite backend/validadores y build frontend para push a `master` o pull request.
- Archivos: `frontend/` (fuentes, lockfile y guía local), `.github/workflows/ci.yml`, `.gitignore`, README raíz, módulos frontend, pruebas, SPEC índice, plan, estado e historial.
- Decisión: sin ADR; no se cambia arquitectura documentada ni contrato, y se conserva React/TypeScript/Vite previsto. Leaflet continúa pendiente para mapa interactivo.
- Validación: `npm ci` y `npm run build` (correctos; 24 paquetes, cero vulnerabilidades reportadas); suite completa backend (100 pruebas); `python3 scripts/check_docs.py` y `python3 scripts/check_sdd.py` correctos; revisión del árbol de accesibilidad y captura local en viewport móvil. `git diff --check` se ejecutará al cierre.
- Validación no ejecutada: workflow remoto porque el cambio aún no está publicado; no se afirma CI de GitHub exitoso.
- Límites: selector solo cambia copy; no inicia partidas ni consume `/panel/estado`, `/panel/mapa` o WebSocket. No se implementa mapa vivo, controles, sesión o comportamiento offline.
- Siguiente acción: diseñar P4-01 contra snapshot/proyección observable y contratos reales existentes, preservando ocultamiento de dormidos; seguir con un commit independiente por fase.
- Commit: se registra después de cerrar y verificar la fase.

## CAM-029 — Evaluador HTTP con cadencia configurable

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario; siguiente paso de CAM-028 para medir el evaluador con el período de dos segundos que requiere T-11.
- Especificación/requisitos/tareas: SPEC-002, CA-002-04 parcial, P2-03 y P5-01 en curso; T-11 parcial. No verifica la SPEC.
- Base Git: `master`, commit `4f943d8`; conserva el commit CAM-028 separado.
- Resultado: `evaluacion_local.py` programa inicios con reloj monotónico, admite `periodo_segundos`/`--periodo-segundos` (2 s por defecto), y reporta intervalos, retrasos y duración/cumplimiento del período por turno. Las solicitudes siguen leyendo una sola versión por turno y se resuelven después de la tanda HTTP.
- Archivos: `src/navira/evaluacion_local.py`, `tests/test_evaluacion_local.py`; documentos propietarios del módulo, pruebas, plan, SPEC-002, trazabilidad, índice, estado y [reporte CAM-029](resultados/evaluacion-cadencia-cam029.md).
- Evidencia local: tres turnos por cohorte 20/80/200 con mapa `manta-osm-d76772f9d9e9`, escenario sintético `mixto`, semilla `20261026`, concurrencia máxima 200 y cadencia 2 s. 877 solicitudes, cero fallos HTTP, p95 18,017/54,593/103,734 ms, ciclos máximos 59,078/207,267/479,105 ms y retraso máximo de inicio 0,176/0,072/0,074 ms. Los datos completos y límites están en el reporte.
- Límites: corrida local única y corta; no son 150 turnos, no dura cinco minutos por ronda, no usa poblaciones oficiales de zombies ni cliente remoto/AWS. No verifica T-11 ni latencia sostenida, supervivencia general, persistencia durable, cartografía para uso real o seguridad sísmica. P-07 y P-09 siguen abiertos.
- Verificación: prueba enfocada `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_evaluacion_local.py' -v` (5 pruebas correctas); suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (100 pruebas correctas); `python3 scripts/check_docs.py` (60 Markdown en doc/, 62 archivos comprobados); `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas); `PYTHONPATH=src /tmp/navira-env/bin/python -m compileall -q src tests` y `git diff --check` correctos. Corrida CLI guardada temporalmente en `/tmp/navira-evaluacion-local-cam029.json`; el resumen versionado está en el reporte. El cambio quedó en un commit individual local. `git push origin master` no pudo leer credenciales HTTPS; la conexión GitHub también rechazó crear el árbol remoto con HTTP 403 `Resource not accessible by integration`. `git ls-remote` confirmó que `origin/master` permaneció en `fa7ebd8`; no se afirma publicado.
- Siguiente paso: cerrar P-09/parámetros de escenario antes de identificar poblaciones oficiales; luego ejecutar 150 turnos por ronda y medir en el entorno de evaluación. Mientras tanto el evaluador admite `--turnos 150 --periodo-segundos 2`, pero una corrida local no cierra la evaluación oficial.

## CAM-028 — Evaluación HTTP multi-turno en Manta

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario; siguiente acción de CAM-025/estado actual para medir `/paso` mientras el mundo avanza.
- Especificación/tareas: SPEC-002, P2-03 y T-11 parciales; CA-002-04 parcial. No se verifica T-11 ni toda la SPEC.
- Base Git: el usuario confirmó publicación y `git ls-remote` verificó que `origin/master` coincidía con `fa7ebd8` antes de esta tarea. El trabajo se realiza directamente en `master`, como pidió el usuario.
- Resultado: nuevo CLI local crea contexto sobre el fixture Manta, sirve FastAPI con Uvicorn en loopback, consulta por HTTP a cada sobreviviente activo de cada turno y resuelve usando los destinos recibidos. Cada turno comparte snapshot; las fallas se contabilizan y se convierten en espera para completar la transición. La API no adquiere rutas nuevas. Se usa una clave aleatoria temporal que no se imprime.
- Archivos: `src/navira/evaluacion_local.py`, `src/navira/carga_http.py`, `tests/test_evaluacion_local.py`; documentos propietarios de pruebas, módulos, plan, SPEC-002, índice, estado y reporte en [resultados](resultados/evaluacion-multi-turno-cam028.md).
- Evidencia: una matriz de cinco turnos por cohorte con semilla `20261026`, perfil sintético `mixto` y hasta 200 workers produjo 91/374/911 solicitudes para 20/80/200 personas, todas HTTP 200 y 0 fallidas. p95 local: 20,712/52,781/109,847 ms. Duración total por cohorte: 0,320/0,809/1,841 s.
- Límites: Uvicorn y cliente comparten host; no se espera el período de 2 s ni se ejecutan cinco minutos/rondas oficiales. No acredita p95 desplegado, T-11, supervivencia general, distribución oficial, exactitud cartográfica ni seguridad ante tsunami/sismo. T-11 y P2-03 siguen en curso.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (98 pruebas OK); incluye integración HTTP real, avance de versión y replay de resultados del mundo con la misma semilla. `python3 scripts/check_docs.py` (59 Markdown en doc/, 61 archivos), `python3 scripts/check_sdd.py` (seis SPEC), `compileall` y `git diff --check` correctos. La matriz CLI produjo el reporte resumido versionado; JSON íntegro temporal en `/tmp/navira-evaluacion-local-cam028.json`. El commit local se creó, pero `git push origin master` falló porque Git no pudo leer credenciales HTTPS; el remoto sigue en `fa7ebd8`.
- Siguiente paso: publicar el commit local CAM-028 cuando se restablezca autenticación de escritura; después medir con reloj real y duración requerida al confirmar parámetros P-09 y repetir desde el entorno remoto antes de afirmar objetivos de rendimiento.

## CAM-027 — Continuar en `master` y preservar commits por cambio

- Fecha: 2026-10-26, Ecuador continental.
- Origen: ante la falta de autenticación para publicar `main`, el usuario elige `master` y pide mantener un commit separado por cada cosa implementada.
- Resultado: `master` local avanzó en fast-forward hasta el historial completo. Se eliminaron las ramas locales `feat/navira-*` y `main` después de confirmar que sus commits son ancestros de `master`. El remoto no se ha modificado.
- Granularidad: se conservaron los commits ya existentes, uno por fase/cambio; no se hizo squash ni se reescribió el historial. `git log --reverse origin/master..HEAD` mostró los 21 commits locales previos a esta entrada; CAM-027 agrega un commit documental aparte.
- Verificación: estado limpio antes de documentar, avance fast-forward y revisión del historial con `git log --oneline --reverse origin/master..HEAD`. El push de prueba sigue limitado por la falta de credenciales registrada en CAM-026.
- Pendiente: publicar `master` cuando GitHub esté autenticado con permiso de escritura. El remoto aún está en `6e3e9c02e21e64c25b185b14ac5544bdf69dab99`.

## CAM-026 — Consolidación local en `main` y publicación pendiente

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario pide eliminar ramas de fase, trabajar directamente en `main` y subir los cambios.
- Motivo: centralizar en `main` el historial de implementación ya integrado y ajustar el flujo de trabajo según la instrucción actual.
- Resultado local: se creó `main` desde `e5e9e749adb93af73dbcdd095fe8cb2d8d23042b`; incluye los 20 commits posteriores a `master`. No se creó un commit de merge porque la rama de trabajo ya descendía directamente de `master`.
- Verificación remota: el remoto solo tiene `master` en `6e3e9c02e21e64c25b185b14ac5544bdf69dab99`. `git push --set-upstream origin main` falló porque Git no pudo solicitar credenciales HTTPS en esta sesión. La integración GitHub conectada rechazó crear `main` con HTTP 403 y el navegador no tiene sesión iniciada.
- Límite: `main` aún no está en GitHub ni es rama predeterminada; no se eliminó `origin/master`. La eliminación de ramas locales se completa después de registrar este cambio y verificar que todas estén contenidas en `main`.
- Siguiente paso: habilitar una sesión GitHub con escritura, publicar `main`, cambiar y comprobar la rama predeterminada, y luego borrar las referencias obsoletas según [estado actual](estado-actual.md).

## CAM-001 — Análisis y plan inicial

- Fecha: 2026-10-26.
- Origen: el usuario solicita analizar el reto y preparar un plan de implementación.
- Motivo: convertir requisitos, rúbrica y plazo en una solución construible.
- Resultado: propuesta de núcleo de rutas, simulador, stack AWS y fases; archivo original preparado en `docs/PLAN_IMPLEMENTACION.md`, ahora conservado como [referencia histórica](referencias/plan-previo.md).
- Decisiones relacionadas: ADR-001 y ADR-003, formalizadas después.
- Verificación: lectura del reto y creación del documento. Ninguna aplicación, prueba de carga o infraestructura ejecutada.
- Pendiente: construir la base y comprobar accesos, reglas ambiguas y costos reales.

## CAM-002 — Incorporación de juego humano

- Fecha: 2026-10-26.
- Origen: el usuario pide entrar al simulador como personaje aleatorio y mantener ambos modos.
- Motivo: añadir una experiencia interactiva distintiva sobre el mismo motor.
- Resultado: se amplía el plan con control humano, aparición, sesión, órdenes por turno, radio y métricas separadas.
- Decisión relacionada: ADR-002; un jugador por partida es el límite inicial de diseño, no una implementación multijugador.
- Verificación: revisión y actualización documental; sin código de juego.
- Pendiente: implementar control y probar que no cambia las reglas de simulación.

## CAM-003 — Documentación modular y entrada para agentes

- Fecha: 2026-10-26; concluido después de la instrucción «continúa» que retomó la misma tarea.
- Origen: el usuario pide `contexto.md`, arquitectura, flujos por rol, documentación modular de todo el proyecto y un `AGENTS.md` que ordene revisar los Markdown de `doc/`.
- Motivo: conservar intención, responsabilidades y contexto de cada cambio aunque se cambie de agente o se interrumpa una sesión.
- Archivos: `README.md`, `AGENTS.md`, documentos indexados en [doc/README.md](README.md), enlace compatible `docs/PLAN_IMPLEMENTACION.md` y `scripts/check_docs.py`.
- Resultado: contexto/estado separados, reglas y flujos, módulos, API/eventos/datos, algoritmos, infraestructura, seguridad, costos, pruebas, plan vigente, pendientes, ADR, plantillas e historial. Se preservan fuente del reto y plan anterior sin convertirlos en contratos vigentes.
- Decisión relacionada: ADR-004. La documentación canónica usa `doc/`, en singular.
- Verificación: comprobador local de enlaces e inventario y comparación de la copia del reto con el adjunto; resultados finales en [estado actual](estado-actual.md). No se ejecutaron pruebas de aplicación porque no existe implementación.
- Limitaciones: Budget, recursos, URLs, código, rendimiento y remoto Git siguen sin verificar. Los flujos y tecnologías describen diseño, no servicios existentes.
- Siguiente acción: P0-01 y P0-02 del [plan](plan-implementacion.md); configurar Budget cuando haya acceso autorizado.

## CAM-004 — Incorporación PRD, TRD, ODDD y SDD

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario solicita implementar las cuatro prácticas y confirma ODDD como OO + DDD.
- Especificación: SPEC-006; requisito TRD-13; tareas M0-01 a M0-04. No se implementan funcionalidades del juego en esta intervención.
- Motivo: enlazar necesidades, restricciones, dominio, criterios, tareas, pruebas y evidencia sin duplicar arquitectura/roadmap/bitácora.
- Archivos: PRD/TRD/ODDD/SDD, seis SPEC con índice y matriz, dos plantillas, ADR-005, referencia de propuesta, validación `scripts/check_sdd.py` y sus regresiones. Se actualizan AGENTS, índice, contexto, continuidad, plan, pruebas y enlaces de modelo/arquitectura.
- Decisiones: conservar stack, `doc/`, roles y ambos modos; flujo reducido para cambios pequeños y autorización persistente sin aprobaciones rutinarias repetidas. No instalar skills/hooks/frameworks ni crear agentes por seguir una plantilla.
- Verificación: validadores documentales correctos, seis SPEC con trazabilidad válida, ocho regresiones correctas y copia exacta de la propuesta SDD. Revisión de criterios y comandos en [evidencia de SPEC-006](resultados/verificacion-sdd.md).
- Discrepancia encontrada: la ruta antigua `docs/PLAN_IMPLEMENTACION.md` ya no existe; se corrigen afirmaciones vigentes del índice/AGENTS sin recrear una carpeta paralela. El plan histórico se conserva y no se reescriben entradas anteriores para ocultar la diferencia.
- Límites: comprobar estructura no verifica app, latencia, seguridad desplegada ni factura. Funcionalidades SPEC-001 a SPEC-005 permanecen sin implementar.
- Siguiente paso: iniciar P0-01/P0-02 con SPEC-002 y el modelo ODDD cuando se solicite construir; las tareas de aplicación siguen pendientes.

## CAM-005 — Nombre oficial Navira

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario indica «el nombre de la app sera Navira».
- Flujo SDD reducido: cambio de identidad documental, sin nuevos requisitos o comportamiento; PRD vigente y ADR-006. Se conservan SPEC, criterios y tareas existentes.
- Resultado: **Navira** como nombre oficial e identificador técnico previsto `navira`, con paquete futuro `src/navira/`.
- Archivos: README, AGENTS, contexto, PRD/TRD, ODDD, módulos backend, plan, índice ADR y estado actual; nueva decisión ADR-006.
- Historia: el plan anterior y demás referencias históricas conservan su contenido. No se renombra el directorio `SPOOKYTHON` ni se migra código de app inexistente.
- Verificación: validadores documentales y SDD; resultado del cierre en [estado actual](estado-actual.md). No se requieren nuevas pruebas funcionales porque solo cambia documentación e identidad prevista.
- Siguiente paso: P0-01/P0-02 con el nombre Navira cuando se inicie la construcción.

## CAM-006 — Base local de backend y contrato inicial

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario autoriza comenzar la construcción por fases, con una rama `feat/...` y un commit por fase.
- Especificación/tareas: SPEC-002, P0-01 y P0-02; requisitos PRD-03, TRD-01, TRD-06 y TRD-09. Criterio cubierto parcialmente: contrato y autenticación iniciales; no se declara verificada la SPEC.
- Rama: `feat/navira-backend-base`.
- Motivo: crear un punto de arranque local para el backend y fijar el contrato de transporte antes de construir grafo y simulación.
- Archivos: `pyproject.toml`, `.env.example`, `src/navira/`, fixtures de contrato/mapa mínimo, README, documentos de API/backend, plan y estado.
- Resultado: aplicación FastAPI con `GET /salud`, `POST /paso`, esquema estricto, API key configurable y caso de uso temporal de espera determinista. La espera es válida por el contrato, pero no calcula rutas ni garantiza seguridad. No se exponen rutas auxiliares ni estado inexistente.
- Verificación: instalación editable de `pyproject.toml` correcta en entorno aislado `/tmp/navira-env`; `python3 scripts/check_docs.py` y `python3 scripts/check_sdd.py` correctos; parseo AST de módulos Python, lectura de fixtures JSON/`pyproject.toml` y `git diff --check` correctos. No se ejecutó la API ni pruebas HTTP; el arranque aún queda pendiente.
- Límites: no existe mapa de Manta, simulador, persistencia, Dijkstra, latencia medida ni despliegue. P0-01/P0-02 permanecen en curso hasta verificar instalación/arranque y pruebas de contrato.
- Siguiente paso: arrancar y verificar el endpoint HTTP; después construir grafo/mundo en P1.

## CAM-007 — Modelo y validación de grafo

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario pide continuar la construcción por fases, con rama y commit propios para cada fase.
- Especificación/tarea: SPEC-001, P1-01; requisitos PRD-01, TRD-09 y TRD-12; CA-001-01 parcial y T-07 parcial.
- Rama: `feat/navira-map-graph`.
- Motivo: validar el formato de la red vial antes de cargar datos geográficos de la ciudad.
- Archivos: `src/navira/domain/mapa.py`, fixture sintético, `tests/test_mapa.py`, documentos de datos, pruebas, pendientes, módulos, SPEC-001, plan, README y estado.
- Resultado: nodos WGS84, calles dirigidas con segmento físico estable, refugios, índice de adyacencia, parser JSON y validaciones de IDs/referencias/unidades/categorías. Los cierres pueden apuntar a un sentido o al segmento completo; calles paralelas permanecen independientes.
- Verificación: `python -m unittest discover -s tests -p 'test_mapa.py' -v`: diez pruebas correctas. El fixture sintético de cuatro nodos supera el validador con umbral cuatro. `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py` y `git diff --check` correctos.
- Límites: no hay extracción OpenStreetMap, polígono de Manta, mapa real de unas 300 intersecciones ni refugios reales. P1-01 permanece en curso; P1-02 a P1-05 no implementadas. P0-01/P0-02 aún requieren ejecución HTTP.
- Siguiente paso: preparar el dataset real de Manta y cerrar P1-01; luego continuar con entidades e intenciones.

## CAM-008 — Entidades e intenciones compartidas

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario para implementar Navira fase por fase.
- Especificación/tarea: SPEC-001, P1-02; requisitos PRD-02, PRD-06 y TRD-09; CA-001-06 parcial y T-17 parcial.
- Rama: `feat/navira-world-model`.
- Motivo: fijar el modelo del mundo y el contrato temporal antes de implementar las reglas de movimiento.
- Archivos: `src/navira/domain/modelo.py`, `tests/test_modelo.py`, documentos ODDD, modos, datos, módulos backend, pruebas, SPEC-001, plan y estado.
- Resultado: modelos inmutables para partida, sobreviviente, zombie e intención; el modo queda fijo y cada intención se valida contra run, turno, fase y personaje. Ambos modos usan la misma forma de intención.
- Verificación: siete regresiones de dominio correctas con `python -m unittest discover -s tests -p 'test_modelo.py' -v`. Se verifican estados y vínculo temporal, no la aplicación de movimientos.
- Límites: no hay transición de turnos, política zombie, resolución de mordidas, datos reales de Manta ni persistencia. P1-02 queda en curso; SPEC-001 no está verificada.
- Siguiente paso: implementar un único resolutor de intención/movimiento para NPC y humano en P1-03.

## CAM-009 — Resolución de turno y reglas zombie

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario para construir Navira por fases, con rama y commit individuales.
- Especificación/tarea: SPEC-001, P1-03; CA-001-02/03/04/06 parciales; T-01 a T-06, T-09 y T-17 parciales. Los criterios de visibilidad y snapshot no se consideran cubiertos.
- Rama: `feat/navira-zombie-resolution`.
- Motivo: implementar un único resolutor en memoria que aplique fases zombie, valide intenciones y determine mordidas/llegadas igual en simulador y juego humano.
- Archivos: `src/navira/domain/modelo.py`, `src/navira/simulation/resolver.py`, `tests/test_resolver.py` y documentos propietarios de reglas, algoritmo, flujo, backend, plan, pendientes y pruebas.
- Resultado: caminantes alternan movimiento, corredores persiguen hasta dos tramos, hordas estáticas bloquean el nodo y sus vecinos, dormidos despiertan por radio topológico configurable, sobrevivientes resuelven intenciones a la vez y cruces opuestos comparan cada tramo por segmento. Mordida precede evacuación. Semilla RNG inyectada permite repetición.
- Supuestos: comportamiento del dormido, objetivo/desempate del corredor, inmovilidad de horda y orden mordida/llegada siguen provisionales, configurables o pendientes según P-02 a P-04/P-07. No se expone aún una proyección segura que oculte dormidos.
- Verificación: conjunto completo local: 36 pruebas correctas (8 de SDD, 10 de mapa, 7 de modelo y 11 de resolutor). Validadores documentales y `git diff --check` se ejecutan al cierre; cualquier resultado final se registra antes del commit.
- Límites: un único turno en memoria; no reloj continuo, avance a siguiente turno, eventos persistidos, snapshots/versionado, carga de escenario ni mapa real de Manta. P1-03 queda parcial y SPEC-001 no está verificada.
- Siguiente paso: P1-04 en rama separada, coordinando ciclo de turnos y publicación atómica/versionada del estado.

## CAM-010 — Coordinación de fases, eventos y snapshots locales

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para construir por fases en ramas/commits separados.
- Especificación/tarea: SPEC-001, P1-04; CA-001-03/05 y T-07/T-10/T-18 parciales. Persistencia, recuperación y publicación no están cubiertas.
- Rama: `feat/navira-turn-snapshots`.
- Motivo: separar movimiento zombie de órdenes humanas y dar identidad/versiones explícitas al estado de decisión y resultado.
- Archivos: `src/navira/simulation/coordinador.py`, `src/navira/simulation/reloj.py`, `src/navira/simulation/resolver.py`, `tests/test_coordinador.py` y documentos propietarios de ODDD, datos, flujo, módulos, pruebas, plan, SPEC-001 y estado.
- Resultado: aplicación versionada de cierres en turno objetivo; snapshots completos de decisiones y resolución; preparación separada para juego humano; ruta de avance automático; estado aleatorio privado preservado en los snapshots; apertura del siguiente turno solo desde resultado resuelto; cálculo de deadline absoluto con reloj monotónico.
- Verificación: 43 pruebas de todas las suites correctas, incluidas siete regresiones del coordinador/reloj. Los validadores `check_docs.py`, `check_sdd.py` y `git diff --check` pasan al cierre.
- Límites: el coordinador puro rechaza una versión local obsoleta, pero no evita carreras entre procesos. No existe DynamoDB/adaptador durable, compare-and-swap real, reloj continuo, WebSocket, interrupción/recuperación ni ocultamiento de dormidos. P1-04 permanece parcial y SPEC-001 no se verifica.
- Siguiente paso: persistir snapshots mediante puerto/adaptador con condición de versión y probar fallos/recuperación; luego integrar reloj de ejecución y publicación.

## CAM-011 — Puerto de snapshots y CAS local

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario para implementar Navira por fases y dejar cada cambio en su rama/commit.
- Especificación/tarea: SPEC-001, P1-04; CA-001-05 y T-18 parciales; persistencia durable y recuperación no cubiertas.
- Rama: `feat/navira-snapshot-cas`.
- Motivo: definir el límite de aplicación para guardar estado completo por versión y evitar que dos transiciones locales desde el mismo snapshot se confirmen ambas.
- Archivos: `src/navira/application/snapshots.py`, `src/navira/adapters/snapshots_memoria.py`, `tests/test_snapshots_persistidos.py` y módulos/datos/arquitectura/pruebas/SPEC/estado.
- Resultado: puerto `RepositorioSnapshots`, casos de uso de preparación, resolución y apertura del turno con CAS; el adaptador local inserta una partida una vez y reemplaza snapshot solo cuando versión esperada coincide, bajo un lock por proceso.
- Verificación: tres regresiones nuevas para ciclo completo, duplicado e intento concurrente desde la misma versión. Suites totales, validadores documentales y SDD se registran al cierre.
- Límites: lock local no coordina varios procesos/hosts, no persiste ante reinicio y no sustituye DynamoDB. P1-04 sigue parcial; SPEC-001 no está verificada.
- Siguiente paso: implementar el adaptador durable con escritura condicional y recuperación, sin llevar reglas o SDK al dominio.

## CAM-012 — Verificación HTTP del contrato base

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario; validar la base de backend antes de conectar planificación y estado.
- Especificación/tareas: SPEC-002, P0-01 verificada y P0-02 parcialmente verificada; CA-002-01 parcial y T-08 parcial. No cubre decisión de ruta.
- Rama: `feat/navira-api-contract-tests`.
- Motivo: comprobar instalación, arranque HTTP, autenticación y contrato de éxito/error de la API existente.
- Archivos: `pyproject.toml`, `tests/test_api_http.py`, README, SPEC-002, pruebas y estado.
- Resultado: dependencia opcional `.[test]` con `httpx2` para evitar la API de prueba obsoleta; regresiones para `/salud`, clave sin configurar/inválida/válida, respuesta exacta, campos extra y turno negativo.
- Verificación: instalación editable con extra de pruebas correcta; cinco pruebas ASGI correctas; smoke con Uvicorn/curl: `/salud` 200, `/paso` autenticado 200 con `siguienteNodo` igual al nodo actual, y sin credencial 401. No se mide p95.
- Límites: `/paso` aún devuelve espera determinista, no consulta mapa ni planificador. P0-02 queda parcial; SPEC-002 no está verificada. Sin despliegue.
- Siguiente paso: conectar el caso de uso al mapa/estado y definir respuestas 404/409 con T-08/T-10, manteniendo el cuerpo obligatorio del reto.

## CAM-013 — Núcleo Dijkstra dirigido

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para avanzar Navira por fases y ramas separadas.
- Especificación/tarea: SPEC-002, P2-01 parcial; CA-002-02 parcial; T-07/T-08 parciales. No valida mapa real ni endpoint.
- Rama: `feat/navira-dijkstra`.
- Motivo: construir una política base de rutas sobre el grafo independiente de HTTP y estado de partida.
- Archivos: `src/navira/routing/`, `tests/test_dijkstra.py`, documentos de algoritmos, módulo backend, pendientes, pruebas, plan, SPEC-002, README y estado.
- Resultado: Dijkstra dirigido con costo de distancia y factor positivo configurable por tipo, cierres de aristas/segmentos y filtro de nodos de peligro visibles; selección de refugio objetivo o de menor costo; desempate estable por ID de calle/refugio.
- Supuesto: costo base son metros ponderados; factores neutros 1.0. Velocidad, eficiencia oficial y penalizaciones de juego no se mezclan hasta aclarar P-01.
- Verificación: siete pruebas de grafo sintético cubren ruta más barata, factor por tipo, cierres, peligro visible, no-ruta, desempates y validación. El resultado final del conjunto y validadores queda registrado al cierre.
- Límites: P2-01 continúa parcial; no carga Manta real ni integra el planificador en `/paso`. No estima zombies futuros, mordidas o seguridad garantizada. SPEC-002 no está verificada.
- Siguiente paso: integrar rutas con snapshot vigente y definir proyección de riesgos permitidos, sin exponer dormidos.

## CAM-014 — Integración de rutas con `/paso`

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para seguir construyendo Navira por fases.
- Especificación/tarea: SPEC-002, P2-02 parcial; CA-002-01/02 parciales; T-03/T-04/T-05/T-07/T-08 parciales. No hay ronda operacional.
- Rama: `feat/navira-step-planner`.
- Motivo: hacer que el caso de uso consulte estado vigente y utilice Dijkstra sin introducir runId o estado privado en el contrato externo.
- Archivos: `src/navira/application/decidir_paso.py`, `src/navira/api/routes.py`, `src/navira/main.py`, catálogo de mapas, consulta de partida activa en adaptador de memoria, pruebas de decisión/API e índices propietarios.
- Resultado: valida partida activa, mapa, turno, fase, personaje y posición; selecciona ruta/refugio evitando nodos ocupados por zombies activos, vecindad de horda, cierres y aristas de cruce opuesto conocidas. Ignora dormidos en la recomendación. HTTP conserva el esquema y mapea entidad ausente/estado incompatible/no disponible a 404/409/503. Se puede ensamblar con `crear_app(servicio_decision)`.
- Verificación: suite completa `python -m unittest discover -s tests -p 'test_*.py' -v` (67 pruebas OK); `python3 scripts/check_docs.py` y `python3 scripts/check_sdd.py` OK; `git diff --check` OK. Los validadores comprueban estructura documental, no comportamiento.
- Límites: el app predeterminado no carga mapa/partida y mantiene espera determinista. Almacenamiento es memoria, no hay inicio de partida/configuración de escenario ni idempotencia durable. Dijkstra trata riesgos visibles actuales, no futuro y no garantiza supervivencia. P2-02 parcial; SPEC-002 no verificada.
- Siguiente paso: añadir inicializador de partida de demostración con mapa de desarrollo explícito y preparar la integración persistente, sin presentar ese mapa sintético como Manta.

## CAM-015 — Bootstrap local explícito de partida demo

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de la construcción por fases; siguiente acción concreta de CAM-014/estado actual.
- Especificación/tareas: SPEC-001, P1-04 parcial; P2-02 continúa en curso. No se declara ronda completa ni SPEC verificada.
- Rama: `feat/navira-demo-bootstrap`.
- Motivo: arrancar el planificador con un mundo explícito y verificable sin presentar datos sintéticos como mapa de Manta.
- Archivos: `src/navira/demo.py`, `src/navira/main.py`, `data/maps/demo-sintetico.json`, `tests/test_demo.py`, README y documentos propietarios de datos, backend, pruebas, plan, SPEC y estado.
- Resultado: `NAVIRA_DEMO=1` carga mapa sintético, crea un snapshot inicial en memoria, avanza al primer estado de decisiones con el coordinador y ensambla `DecidirPaso`. La ruta `S-DEMO-001` desde `D-001` propone `D-002`. Sin opt-in, el proceso mantiene espera determinista.
- Límites: un sobreviviente, sin zombies, un refugio, repositorios volátiles, semilla controlable y sin reloj continuo. No es mapa de evaluación ni una ronda de simulación completa; reiniciar el proceso reinicia el estado.
- Verificación: suite completa `PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v` (70 pruebas OK); smoke con proceso Uvicorn: `GET /salud` 200 y `POST /paso` autenticado 200 con `{"siguienteNodo":"D-002"}`. Se ejecutaron `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py` y `git diff --check` al cierre. El smoke es local y no mide carga.
- Siguiente paso: avanzar escenarios reproducibles con ciclo de turno; mantener pendiente persistencia durable, mapa real y reglas/visibilidad.

## CAM-016 — Orquestación de ronda automática versionada

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de la implementación por fases y siguiente trabajo del plan tras el bootstrap demo CAM-015.
- Especificación/tareas: SPEC-001, P1-04 parcial; criterios de fase/snapshot T-06 y T-18 parciales. No se declara SPEC verificada.
- Rama: `feat/navira-automatic-round`.
- Motivo: conectar coordinador, snapshots CAS y Dijkstra para resolver una ronda del modo simulador sin duplicar reglas.
- Archivos: `src/navira/application/simulacion_automatica.py`, `tests/test_simulacion_automatica.py`, documentos propietarios de flujo, datos, backend, pruebas, plan, SPEC y estado.
- Resultado: `EjecutarRondaAutomatica` confirma preparación, genera intenciones automáticas desde Dijkstra y confirma la resolución. Una llamada siguiente abre el turno siguiente; un reintento desde decisiones persistidas no vuelve a mover zombies. Rechaza modo juego y versiones obsoletas.
- Verificación: seis pruebas dedicadas; suite completa `PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v` (76 pruebas OK); `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py`, `compileall` y `git diff --check` correctos. Son verificaciones locales; no miden reloj ni durabilidad.
- Límites: CAS y escenario solo en memoria; no hay reloj continuo, llamada HTTP/CLI, publicación, mapa real ni evaluación oficial. Estado final del juego y métricas de ronda permanecen pendientes.
- Siguiente paso: proporcionar un ejecutor local documentado sobre el contexto demo y crear escenarios/semillas reproducibles con zombies.

## CAM-017 — Ejecutor local de rondas demo

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para construir Navira por fases; siguiente acción registrada en CAM-016.
- Especificación/tareas: SPEC-001, P1-04 parcial; P1-05 continúa pendiente. No se completa la aceptación de la SPEC.
- Rama: `feat/navira-auto-demo-cli`.
- Motivo: hacer ejecutable y reproducible desde terminal el caso de uso de ronda automática, sin introducir reloj continuo ni persistencia nueva.
- Archivos: `src/navira/demo.py`, `src/navira/simulador_demo.py`, `tests/test_simulador_demo.py`, README y documentos propietarios del flujo, módulo, pruebas, plan, SPEC-001 y estado.
- Resultado: `python -m navira.simulador_demo --turnos N --semilla S [--mapa RUTA]` crea contexto efímero, completa rondas por CAS, emite JSON por línea y se detiene al no quedar sobrevivientes activos o alcanzar N turnos. El fixture predeterminado evacúa al único personaje en cuatro rondas.
- Verificación: cuatro regresiones de `test_simulador_demo.py`; suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (80 pruebas OK); `python3 scripts/check_docs.py` (53 Markdown en `doc/`, 55 archivos comprobados), `python3 scripts/check_sdd.py`, ocho regresiones de `test_check_sdd.py`, `compileall` y `git diff --check` correctos. Smoke `PYTHONPATH=src python -m navira.simulador_demo --turnos 10 --semilla 41` produjo cuatro líneas JSON, movimientos D-001→D-002→D-003→D-004→D-005 y evacuación en el turno 3. Validación local, no mide reloj ni persistencia.
- Límites: fixture sintético sin zombies; la semilla se incluye en el reporte y alimenta el generador inicial, pero no cambia el recorrido actual. No duerme entre turnos, mide tiempo, persiste al reiniciar, publica eventos ni evalúa el escenario oficial.
- Siguiente paso: diseñar escenarios reproducibles con zombies para P1-05, después medir las tres rondas según SPEC-005.

## CAM-018 — Perfiles sintéticos de escenarios con zombies

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario; siguiente paso P1-05 documentado por CAM-017.
- Especificación/tareas: SPEC-001, CA-001-07 y P1-05 parcial; T-10. No se considera completo P1-05 ni verificada SPEC-001.
- Rama: `feat/navira-zombie-scenarios`.
- Motivo: ejercitar el mismo ejecutor con zombies y reproducir decisiones usando escenario y semilla como entradas explícitas.
- Archivos: `src/navira/demo.py`, `src/navira/simulador_demo.py`, `tests/test_simulador_demo.py`, README y documentos propietarios de SPEC-001, flujo, módulo, pruebas, plan, pendientes y estado.
- Resultado: perfiles sintéticos `libre`, `caminantes`, `mixto` y `horda`; la partida conserva su perfil, el CLI lo acepta con `--escenario`, y el JSONL reporta movimientos visibles. Zombies que siguen dormidos se omiten. Igual perfil y semilla reproducen reportes; la semilla puede variar el movimiento de caminantes.
- Verificación: seis pruebas de `test_simulador_demo.py`; suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (82 pruebas OK); `python3 scripts/check_docs.py` (53 Markdown en `doc/`, 55 archivos comprobados), `python3 scripts/check_sdd.py`, ocho regresiones de `test_check_sdd.py`, `compileall`, `git diff --check` y smoke del perfil `horda` correctos. Las pruebas muestran reproducción exacta del mismo escenario/semilla, variación posible entre semillas y ausencia de dormidos en JSONL. No se midió duración del turno ni carga oficial.
- Límites: mapa lineal sintético, un sobreviviente, ubicaciones fijas de inicio y cuatro perfiles reducidos; no son las rondas oficiales (20/80/200 sobrevivientes) ni fijan la distribución de zombies del reto. P-09 continúa abierto para tamaño/balance oficial. Sin reloj de 2 segundos, persistencia durable ni medición oficial.
- Siguiente paso: completar poblaciones/condiciones de P1-05 cuando se confirme densidad zombie y contar con mapa de evaluación; después integrar tres rondas según SPEC-005.

## CAM-019 — Cohortes sintéticas para el ejecutor

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario; extensión incremental de P1-05 después de CAM-018.
- Especificación/tareas: SPEC-001, CA-001-08 y P1-05 parcial; T-10. T-11 no se ejecuta con este cambio.
- Rama: `feat/navira-evaluation-populations`.
- Motivo: permitir recorrer los tamaños 20/80/200 del reto con el mismo núcleo local mientras se prepara el dataset real.
- Archivos: `src/navira/demo.py`, `src/navira/simulador_demo.py`, `tests/test_simulador_demo.py`, README y documentos propietarios de datos, reglas, flujo, módulo, pruebas, plan, pendientes, SPEC-001 y estado.
- Resultado: `--sobrevivientes` acepta de 1 a 200; posiciones iniciales no refugio se distribuyen reproduciblemente por semilla. Población inicial se registra por turno. Si el fixture carece de nodos suficientes, pueden coincidir personajes.
- Verificación: ocho pruebas de `test_simulador_demo.py`; suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (84 pruebas OK), incluye poblaciones 20/80/200; `python3 scripts/check_docs.py` (53 Markdown en `doc/`, 55 archivos comprobados), `python3 scripts/check_sdd.py`, ocho regresiones de `test_check_sdd.py`, `compileall` y `git diff --check` correctos. Smoke del CLI con 200 sobrevivientes produjo JSONL de un turno (12.683 bytes). No es carga HTTP ni una medición de rendimiento.
- Límites: poblaciones sobre cinco nodos sintéticos no simulan 20/80/200 ubicaciones realistas, no producen concurrencia HTTP ni verifican T-11, dos segundos, p95, disponibilidad o supervivencia de evaluación. La distribución zombie oficial P-09 sigue pendiente.
- Siguiente paso: añadir mapa representativo de Manta y ejecutar la población a través del cliente HTTP bajo las ráfagas definidas en T-11; evitar afirmar resultados oficiales antes de esas mediciones.

## CAM-020 — Cliente concurrente para medir `/paso`

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario; siguiente paso concreto CAM-019: conectar cohortes sintéticas al cliente HTTP para T-11.
- Especificación/tareas: SPEC-002, CA-002-04 parcial; T-11 parcial. No se verifica la SPEC ni la prueba de fuego.
- Rama: `feat/navira-http-load-runner`.
- Motivo: medir desde un cliente la ruta HTTP real con las cohortes sintéticas, conservar el contrato y capturar latencias/errores sin incrustar credenciales.
- Archivos: `src/navira/main.py`, `src/navira/carga_http.py`, pruebas de carga/demo, README y documentos propietarios de API, backend, pruebas, SPEC-002 y evidencia local.
- Resultado: variables optativas del bootstrap demo fijan escenario/semilla/población del servidor; `python -m navira.carga_http` prepara solicitudes reproducibles y dispara hasta 200 llamadas concurrentes por ronda, verificando status, forma y destino esperado. El cliente requiere `NAVIRA_API_KEY` del entorno. Repite solicitudes sobre snapshot fijo; no avanza turnos.
- Verificación: dos pruebas del cliente y cinco del ensamblaje demo pasan; suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (88 pruebas OK); `python3 scripts/check_docs.py` (54 Markdown en `doc/`, 56 archivos comprobados), `python3 scripts/check_sdd.py`, ocho regresiones de `test_check_sdd.py`, `compileall` y `git diff --check` correctos. Smoke mediante CLI contra Uvicorn local: 20/80/200 solicitudes concurrentes recibieron 200, sin fallos; p95 7.872/11.972/26.066 ms. Detalle y límites en [reporte](resultados/carga-local-cam020.md). No es T-11 completo ni prueba externa.
- Límites: una pasada local por cohorte, un proceso Uvicorn, mismo host, snapshot fijo, sin intervalo/150 rondas ni entorno evaluador. No es T-11 completado, disponibilidad ni promesa de rendimiento.
- Siguiente paso: finalizar verificación/commit; después hacer ejecución sostenida en el entorno objetivo con mundo/turno activos y recolectar una muestra completa.

## CAM-021 — Fixture geográfico de Manta con evidencia por amenaza

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario; solicita considerar zonas seguras de tsunami y terremoto en la ciudad real de Manta, Ecuador.
- Especificación/tareas: SPEC-001, CA-001-01/P1-01 parcial; P-13 parcialmente atendido, P-14 abierto. No se verifica SPEC-001.
- Rama: `feat/navira-manta-hazard-map`.
- Motivo: reemplazar el mapa pendiente por un fixture reproducible con red pública de Manta y destinos cuya evidencia de tsunami sea rastreable, sin atribuir seguridad sísmica no validada.
- Archivos: `scripts/exportar_mapa_manta.py`, `data/maps/manta-hackathon-v1.json`, `data/maps/manta-hackathon-v1.fuentes.json`, `tests/test_mapa_manta.py`, ADR-007 y documentos propietarios de contexto, producto, datos, reglas, mapa, plan, pendientes, SPEC-001 y estado.
- Resultado: el exportador descargó OSM en un recorte urbano declarado, simplificó la geometría y produjo 300 nodos, 599 sentidos de calle y cuatro refugios distintos. Los marcadores de Cristo Rey, Colinas de Rocafuerte, La Dolorosa y Plaza del Sol aparecen como “Zona Segura” en los mapas de evacuación por tsunami del GAD Manta; los ajustes a la red son 32,9–43,4 m. El grafo dirigido incluye un camino de cada nodo a algún refugio. Metadatos registran extracción, área, atribución/licencia ODbL y límites.
- Verificación: exportador ejecutado en vivo el 2026-10-26; suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (90 pruebas OK), incluidas dos pruebas enfocadas del mapa. `python3 scripts/check_docs.py` (56 Markdown/58 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructurales), ocho regresiones documentales, `compileall` y `git diff --check` correctos. Los validadores SDD comprueban estructura/trazabilidad, no comportamiento ni verdad externa.
- Límites: fixture de simulación, no para navegación/evacuación real; cobertura completa de barrios y acceso peatonal no verificados; los límites de velocidad faltantes son valores de juego; zonas de tsunami no validan seguridad de terremoto. P-14 requiere microzonificación y validación de suelo/estructura. La SPEC y P1-01 permanecen parciales.
- Siguiente paso: cerrar un commit individual en esta rama. Luego revisar visualmente cobertura y, por separado, buscar datos oficiales de microzonificación sísmica para Manta.

## CAM-022 — Requisito de mundo estocástico y reproducción

- Fecha: 2026-10-26, Ecuador continental.
- Origen: aclaración del usuario: el simulador debe ser aleatorio y pequeños cambios pueden alterar rutas, hordas y la evolución del mundo.
- Especificación/tareas: PRD-02/07, TRD-11, SPEC-001 CA-001-07/09, P1-05. T-24 se define para implementación futura; no está ejecutada.
- Rama: `feat/navira-stochastic-simulation`.
- Motivo: hacer explícita la variación estocástica y su efecto en cascada, conservando la capacidad de reproducir una partida concreta para depurar y comparar.
- Archivos: ADR-008; contexto, PRD, TRD, ODDD, reglas, algoritmos, datos, pendientes P-15, plan, SPEC-001, trazabilidad, pruebas, estado e índices.
- Resultado: el objetivo es una semilla nueva por defecto, muestrear estados/decisiones permitidos por reglas y guardar contexto/RNG privado para replay dentro de la misma versión. El planificador permanece estable para una solicitud sobre el mismo snapshot. Diferencias de entrada pueden divergir, sin prometer que todo cambio mínimo necesariamente cambie el resultado final.
- Verificación: revisión de documentos propietarios y código actual (`demo.py`, `resolver.py`, `coordinador.py`); `python3 scripts/check_docs.py` (57 Markdown/59 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas), ocho pruebas de `test_check_sdd.py` y `git diff --check` correctos. No se ejecutaron pruebas de producto porque esta unidad solo especifica/documenta el requisito; T-24 queda pendiente de implementar.
- Límites: el código actual solo aleatoriza parte de la ubicación de sobrevivientes y movimiento de caminantes; perfiles/ubicaciones zombie son prefijados, corredores siguen persecución y desempate por ID, horda no se mueve y la semilla por defecto es fija. Densidad oficial P-09 y movimiento de horda P-07 siguen abiertos. Este CAM registra y traza el requisito, no implementa el generador estocástico.
- Siguiente paso: implementar P1-05 en una unidad de código: semilla de entropy por defecto con semilla explícita para replay, variación inicial parametrizada y pruebas de misma entrada/reproducción y divergencia controlada T-24. Mantener fuera de ese cambio cualquier distribución oficial sin fuente confirmada.

## CAM-023 — Semilla nueva y estado inicial estocástico de demo

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario y aclaración de que cambios pequeños pueden alterar rutas, hordas y evolución; implementación de P1-05 bajo ADR-008.
- Especificación/tareas: SPEC-001, P1-05; CA-001-07/08/09 y T-24 parciales.
- Rama: `feat/navira-stochastic-simulation`; commit individual `feat: randomize Navira demo simulations`.
- Motivo: dejar de repetir un mundo fijo cuando inicia una partida nueva y conservar entrada suficiente para reproducir ejecuciones locales.
- Archivos: `src/navira/demo.py`, `src/navira/simulador_demo.py`, `src/navira/main.py`, pruebas demo/CLI, `README.md` y documentos propietarios de contrato, algoritmos, datos, flujo, pruebas, plan, SPEC e índice, trazabilidad, estado y este historial.
- Resultado: semilla de 64 bits generada desde entropía si no se indica; los inicios de sobrevivientes/zombies y la fase de caminantes se muestrean desde RNG privado; el CLI informa la semilla efectiva y permite replay al fijarla. Cada demo recibe runId distinto. Se conserva composición sintética fija; no se modifica persecución de corredor ni regla de horda.
- Verificación: suite completa con `/tmp/navira-env` (92 pruebas OK); `python3 scripts/check_docs.py` (57 Markdown/59 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho pruebas `test_check_sdd.py`, `compileall` y `git diff --check` correctos. T-24 cubre reproducción local y variación, no replay durable ni ejecución oficial.
- Límites: P1-05 sigue parcial. Distribución/cantidad oficial (P-09), movimiento de horda (P-07), eventos estocásticos, persistencia durable y carga con el mundo avanzando siguen pendientes. La divergencia puede ocurrir, no se garantiza que cada mínima perturbación cambie todo resultado.
- Siguiente paso: acordar/configurar escenarios solo con fuentes de reglas confirmadas, resolver P-09 y P-07 antes de variar composición y horda.

## CAM-024 — Replay estocástico multi-turno y estabilidad del snapshot

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario para trabajar la siguiente fase; refinamiento de T-24 tras implementar semilla nueva y muestreo inicial en CAM-023.
- Especificación/tareas: SPEC-001, P1-05; CA-001-07/09 y T-24 parciales.
- Rama: `feat/navira-stochastic-replay-validation`; commit individual `test: verify stochastic replay across turns`.
- Motivo: verificar replay de una trayectoria y posible divergencia de rutas, además de asegurar que la aleatoriedad del mundo no vuelve aleatoria una decisión repetida sobre el mismo snapshot.
- Archivos: `tests/test_simulador_demo.py`, `tests/test_demo.py`, documentos propietarios de pruebas, SPEC-001, plan, trazabilidad, estado e historial.
- Resultado: la misma configuración/semilla reproduce cinco turnos con 20 sobrevivientes; otra semilla cambia la secuencia de rutas en un caso de prueba controlado. Repetir `/paso` sobre el mismo snapshot conserva respuesta y versión.
- Verificación: suite completa con `/tmp/navira-env` (94 pruebas OK); `python3 scripts/check_docs.py` (57 Markdown/59 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho regresiones SDD, `compileall` y `git diff --check` correctos. La repetición, divergencia controlada y snapshot se verifican por pruebas locales.
- Límites: no verifica persistencia/recovery durable, múltiples versiones del algoritmo, eventos oficiales, mapa Manta ni que toda semilla distinta produzca divergencia. No cierra P1-05.
- Siguiente paso: ejecutar cohortes sintéticas reproducibles de 20/80/200 sobre el fixture Manta y documentar un reporte exploratorio; después medir integración de `/paso` con avance de mundo.

## CAM-025 — Cohortes sintéticas sobre el fixture Manta

- Fecha: 2026-10-26, Ecuador continental.
- Origen: siguiente subpaso autorizado por el usuario para continuar la construcción por fases y probar el generador estocástico sobre la ciudad real modelada en el fixture disponible.
- Especificación/tareas: SPEC-001, P1-01/P1-05 parciales; CA-001-01/08/09 y T-07/T-24 parciales. No cierra P2-03 ni T-11.
- Rama: `feat/navira-manta-simulation-cohorts`; commit individual `test: exercise stochastic cohorts on Manta map`.
- Motivo: comprobar que el mapa versionado de 300 nodos funciona con el muestreo de inicio y el resolutor de rondas, antes de llevar el motor a medición HTTP.
- Archivos: `tests/test_simulacion_mapa_manta.py`, `doc/resultados/simulacion-manta-cam025.md`, README y documentos propietarios de mapa, flujo, pruebas, plan, SPEC, índice e historial.
- Resultado: con perfil `mixto`, semilla `20261026` y hasta tres turnos, cohortes sintéticas de 20/80/200 produjeron 2/8/28 evacuados, cero mordidos y 18/72/172 activos al final. Los movimientos comprobados son vecinos dirigidos o espera. La semilla/mapa/versión están en el reporte.
- Verificación: suite completa con `/tmp/navira-env` (95 pruebas OK); `python3 scripts/check_docs.py` (58 Markdown/60 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho regresiones SDD, `compileall` y `git diff --check` correctos. El reporte no registra mediciones de latencia/carga.
- Límites: ensayo local único sobre perfiles reducidos; no son ejecuciones oficiales ni muestras independientes, no valida seguridad sísmica/cobertura cartográfica ni garantiza rutas reales. P-07, P-09, P-13 y P-14 continúan abiertos.
- Siguiente paso: ensayar `/paso` con avance del mundo por turnos en local y medición repetida, manteniendo separadas latencia HTTP y métricas de supervivencia.

## Próximas entradas

Usar [plantilla de cambio](plantillas/cambio.md). Cada entrada significativa explica qué disparó el cambio, por qué, qué áreas toca, qué se comprobó y cómo continuar. Conservar entradas anteriores; corregir datos erróneos dejando constancia, no reescribiendo la historia silenciosamente.
