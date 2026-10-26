# Estado actual y punto de reanudación

Última actualización: 2026-10-26. Último cambio en preparación: **CAM-041**, en [cambios.md](cambios.md).

## Hechos verificados

- Nombre oficial elegido por el usuario: **Navira**. Documentación vigente y paquete backend previsto `src/navira/` actualizados; decisión ADR-006. El directorio local sigue siendo `SPOOKYTHON`.

- Existe documentación modular en `doc/`, README raíz y protocolo de incorporación en `AGENTS.md`.
- P0-04: existe scaffold React + TypeScript + Vite en `frontend/`, selector local de simulador/juego y `.github/workflows/ci.yml`; build/suite Python pasan localmente. El workflow aún no se ha ejecutado en GitHub Actions.
- P4-01 verificado en CAM-031: `GET /panel/estado` y `GET /panel/mapa` proyectan snapshots/mapa versionados; ocultan dormidos y estado aleatorio privado. El frontend valida respuesta/versiones, dibuja calles, refugios, sobrevivientes, zombies visibles, movimientos confirmados, cierres/hordas, métricas y ruta prevista Dijkstra seleccionable.
- P4-02 verificado localmente en CAM-032: `WS /ws/panel` envía snapshot completo al conectar/cambiar versión y heartbeat; backend cubierto por prueba de reconexión, secuencia posterior y cambio de partida. El frontend implementa estados de conexión viva/desactualizada/reconexión y backoff; no hay outbox, replay durable ni multi-worker.
- P3-01 verificado como núcleo aislado en CAM-033: búsqueda temporal acotada con espera, cierres y exposición futura inyectada; la política HTTP no la consume. La medición serial no valida T-11 ni servicio HTTP.
- P3-02 parcial en CAM-034: pronóstico por escenarios de amenazas activas, con entradas observables mínimas, mezcla de fase privada desconocida y supuestos declarados para corredor/horda. No se conecta a `/paso`; las reglas oficiales siguen pendientes.
- P3-03 evaluado parcialmente en CAM-035: temporal sumó 15 evacuados en 27 pares sintéticos de tres turnos, sin cambiar las mordidas observadas. La prueba se repitió con resultados deterministas. Dijkstra sigue activa porque no hay comparación HTTP concurrente, ronda larga ni reglas confirmadas.
- P4B-01 implementa parcialmente en CAM-036 un caso de uso de sesión humana propietaria, cookie opaca y aparición aleatoria con CAS. CAM-039/040 conecta aparición pendiente antes del movimiento zombie. Las sesiones siguen en memoria y no expiran.
- P4B-02 implementa parcialmente en CAM-037 el endpoint `POST /juego/accion`, autorización e idempotencia local. CAM-040 consume la última orden, rechaza fuera del deadline de 1,7 s y serializa registro/resolución con puerta monotónica de un proceso.
- P4B-03 inicia en CAM-038 controles web; CAM-040 añade proxy Vite para `/juego`; CAM-041 muestra restante de ventana calculado por servidor y deshabilita controles al llegar a cero. Radio, T-19 accesibilidad integral y resultado completo siguen pendientes.
- P5-04 parcial en CAM-039..041: `NAVIRA_GAME_DEMO=1` ensambla modo sintético y runner local de dos segundos. Pruebas del coordinador y smoke ASGI confirman orden común con NPC, aparición en fase correcta, cierre temporal, cuenta atrás informativa y sesión única. No es cadencia sostenida ni juego productivo; no hay persistencia/recuperación tras reinicio, expiración de sesión, TLS o coordinación multi-proceso.
- El plan anterior se conserva como referencia histórica. La ubicación antigua `docs/PLAN_IMPLEMENTACION.md` ya no existe en el árbol comprobado; la fuente vigente es `doc/plan-implementacion.md`.
- Están documentados dos modos y los límites de la primera versión.
- Se conserva una copia local del reto proporcionado por el usuario.
- Existe `scripts/check_docs.py`, una utilidad de documentación con biblioteca estándar de Python; no es código de la aplicación.
- Existen PRD, TRD, ODDD (OO + DDD confirmado por el usuario), SDD, seis SPEC y matriz de trazabilidad. SPEC-006 verifica incorporación metodológica; SPEC-001 y SPEC-002 tienen implementación parcial sin verificación completa.
- Existe `scripts/check_sdd.py` con ocho pruebas de regresión en `tests/test_check_sdd.py`; son utilidades/pruebas documentales, no la aplicación.
- En `feat/navira-backend-base` existe la base FastAPI en `src/navira/`, `/salud`, `/paso` con autenticación y esquemas, y fixtures de contrato/mapa. El endpoint usa temporalmente una política de espera determinista; todavía no hay cálculo de rutas.
- En `feat/navira-map-graph` existe `src/navira/domain/mapa.py`: modelo de nodo/calle/refugio, carga JSON, adyacencia dirigida y validación de cierres por arista/segmento. Diez pruebas de dominio pasan. El fixture es sintético y no representa Manta.
- En `feat/navira-world-model` existe `src/navira/domain/modelo.py`: partida con modo/turno/fase fijos, sobrevivientes, zombies e intención ligada a su partida y fase. Siete pruebas pasan; todavía no hay resolutor de movimiento.
- En `feat/navira-zombie-resolution` existe `src/navira/simulation/resolver.py`: resolución en memoria de una fase completa con movimiento zombie, intenciones humanas/automáticas, mordidas y evacuación. Las once pruebas del resolutor y 36 pruebas totales pasan. Reglas aún provisionales; no integra reloj, persistencia, snapshots ni visibilidad del estado dormido.
- En `feat/navira-snapshot-cas` la aplicación define `RepositorioSnapshots` y casos de uso para confirmar preparación/resolución con CAS; `AlmacenSnapshotsMemoria` usa lock para que un solo hilo confirme cada versión. El total local es 46 pruebas. El adaptador sigue siendo no durable y limitado a un proceso.
- En `feat/navira-api-contract-tests` se instalaron dependencias de prueba opcionales; cinco pruebas ASGI validan `/salud`, API key y esquema de `/paso`. Uvicorn local respondió 200 en salud y solicitud válida, 401 sin credencial. `/paso` sigue siendo espera determinista. La suite total actual tiene 51 pruebas.
- En `feat/navira-dijkstra` existe `src/navira/routing/dijkstra.py`: búsqueda dirigida por costo en metros ponderados por factor configurable de tipo; closures de arista/segmento y nodos de peligro visibles; selección de refugio y desempates estables. Siete pruebas cubren el núcleo genérico; `/paso` todavía no lo consume.
- En `feat/navira-step-planner` `DecidirPaso` consulta snapshot activo y catálogo de mapas inyectados, valida identidad/turno/fase y usa Dijkstra evitando zombies activos, horda, cierres y cruces opuestos conocidos; no consulta dormidos. La ruta HTTP mapea 404/409/503. Pruebas integradas pasan.
- En `feat/navira-demo-bootstrap` el opt-in `NAVIRA_DEMO=1` carga `data/maps/demo-sintetico.json`, crea una partida efímera en memoria, abre la fase de decisiones con el coordinador y ensambla `DecidirPaso`. La API recomienda `D-002` desde `D-001`; mapa no oficial, sin zombies ni reloj continuo. Sin opt-in, la app conserva espera.
- En `feat/navira-automatic-round` `EjecutarRondaAutomatica` encadena preparación zombie, recomendaciones Dijkstra y resolución sobre snapshot activo de modo simulador, confirmando fases por CAS y reanudando desde decisiones persistidas. Pruebas cubren turno completo, siguiente turno, reanudación, versión vieja y orden de zombie. El servicio aún no se ofrece como bucle o transporte.
- En `feat/navira-auto-demo-cli` `python -m navira.simulador_demo --turnos N --semilla S` ejecuta rondas automáticas sobre el mapa sintético en memoria y emite una línea JSON por turno; se detiene cuando ya no hay personajes activos. `crear_contexto_demo()` comparte el ensamblaje con el bootstrap de API. El fixture no tiene zombies y la semilla no cambia su recorrido actual. CAM-017 registra cuatro pruebas específicas y la suite completa de 80.
- En `feat/navira-zombie-scenarios` el ejecutor acepta los perfiles sintéticos `libre`, `caminantes`, `mixto` y `horda`. `--escenario` junto con `--semilla` seleccionan el inicio y el estado RNG; mismo par reproduce reportes. JSONL omite ubicaciones de zombies que siguen dormidos. Esto inicia P1-05, pero no equivale a poblaciones oficiales ni escenarios de 20/80/200 sobrevivientes. CAM-018 tiene seis pruebas específicas; suite completa de 82.
- En `feat/navira-evaluation-populations` `--sobrevivientes` admite de 1 a 200 y posiciones iniciales reproducibles por semilla fuera de los refugios. Pruebas verifican cohortes sintéticas de 20, 80 y 200. Por el fixture de cinco nodos, las posiciones pueden coincidir; no es prueba HTTP/carga T-11 ni evaluación real. CAM-019 cuenta con ocho pruebas específicas y suite completa de 84.
- En `feat/navira-http-load-runner` el bootstrap demo admite variables para escenario, semilla y población; `python -m navira.carga_http` envía ráfagas concurrentes a `/paso` y resume respuestas/percentiles. Uvicorn local respondió correctamente en una ráfaga de 20, 80 y 200; evidencia en `doc/resultados/carga-local-cam020.md`. No equivale a T-11: una sola pasada, mismo host y snapshot sin avanzar. Suite completa 88; comprobador documental ve 54 Markdown/56 archivos.
- En `feat/navira-manta-hazard-map` se añadió `scripts/exportar_mapa_manta.py` y el fixture versionado `data/maps/manta-hackathon-v1.json`: 300 nodos, 599 sentidos dirigidos y cuatro refugios distintos tomados de puntos “Zona Segura” de tsunami publicados por el GAD Manta. Cada nodo exportado puede alcanzar uno de los refugios por calles dirigidas. Sidecar registra OpenStreetMap/ODbL, extracción y snaps de 32,9–43,4 m. Dos pruebas de integridad validan el artefacto y que el estado sísmico se mantenga como no evaluado. CAM-021; rama de fase preparada para commit individual.
- CAM-022 documentó el requisito de mundo estocástico y replay. CAM-023 implementa parcialmente ese requisito en demo: sin semilla crea una de 64 bits desde entropía, muestrea posiciones de sobrevivientes/zombies y fase inicial de caminantes; CLI registra semilla efectiva y semillas explícitas reproducen JSONL dentro de esta versión. No cambia la composición fija de perfiles, la persecución determinista del corredor ni la inmovilidad provisional de horda.
- CAM-024 extiende la evidencia T-24: replay exacto de cinco turnos con 20 sobrevivientes bajo semilla explícita, divergencia de rutas con otra semilla y decisión/versión estable al repetir `/paso` sobre el mismo snapshot. Es evidencia local sobre el mapa sintético, no sobre recuperación durable ni rondas oficiales.
- CAM-025 ejecutó el simulador por tres turnos sobre el fixture vial de Manta para cohortes sintéticas de 20/80/200 con semilla `20261026`. Se comprobaron caminos dirigidos y el reporte básico; el resultado está en [simulación Manta](resultados/simulacion-manta-cam025.md). No se midió HTTP ni rendimiento y no son rondas oficiales.

## Verificación histórica de CAM-003

- `python3 scripts/check_docs.py`: correcto, 35 Markdown en `doc/` y 38 archivos Markdown comprobados; sin enlaces locales inexistentes ni documentos inaccesibles desde el índice.
- Copia del reto: comparada íntegramente con el adjunto del usuario; coincide.
- Sintaxis del comprobador: validada con `ast.parse`.
- Alcance: no se comprobaron URLs externas, renderizado, aplicación, despliegue ni costos reales.

## Verificación de CAM-004

Comprobación documental y SDD correctas: 52 Markdown en `doc/`, 54 archivos comprobados, seis SPEC y 22 requisitos identificados. SPEC-006 verificada; las otras cinco continúan listas, sin código. Ocho regresiones ejecutadas correctamente y comando enfocado a SPEC-004 comprobado. Propuesta SDD preservada íntegramente. Revisión, comandos, conteo por pasada y límites en [evidencia](resultados/verificacion-sdd.md).

## Verificación de CAM-005

`python3 scripts/check_docs.py` correcto: 53 Markdown en `doc/` y 55 archivos comprobados. `python3 scripts/check_sdd.py` correcto: seis especificaciones mantienen su trazabilidad y estado. Búsqueda de nombres revisada: la denominación anterior solo permanece en antecedentes explícitos y referencia histórica. No cambian scripts ni comportamiento funcional, por lo que no se añaden pruebas de aplicación.

## Lo que todavía no existe o no está verificado

| Área | Estado | Evidencia pendiente |
|---|---|---|
| Backend y `/paso` | Contrato y política Dijkstra; inicio demo local explícito | Configurar mundo real, persistencia, idempotencia y medir latencia bajo carga. |
| Simulador | Demo con semilla nueva opcional, estado inicial aleatorio y replay local explícito; resolución/ronda con RNG privado y CAS en memoria | Distribución oficial parametrizada, composición/eventos, movimiento de horda, replay durable/versionado entre despliegues, DynamoDB, reloj/publicación y escenarios oficiales pendientes. |
| Grafo de Manta | Fixture de 300 nodos y cuatro zonas seguras de tsunami generado | Validar cobertura representativa de barrios/rutas peatonales y evaluar amenazas sísmicas con fuentes competentes; el fixture no es para navegación real. |
| Frontend y juego | P4-01/P4-02 verificados localmente; P4B-01..03 y P5-04 parciales en CAM-036..041; modo juego sintético local opt-in muestra un timer informativo | Radio, recuperación durable tras reinicio, expiración de sesión, TLS, T-14/T-15/T-19 integral y verificación de cadencia sostenida. |
| Infraestructura AWS | Pendiente | Recursos, URL y comprobación de salud. |
| Budget con alerta | No verificado | Captura y configuración real. |
| Rendimiento/supervivencia | Evaluación HTTP local de tres turnos a cadencia de 2 s CAM-029; no oficial | 150 turnos/5 minutos por ronda, parámetros oficiales y medición desde el entorno real. |
| Repositorio remoto y commits | Al inicio de CAM-039 `origin/master` coincidía con HEAD `7bd4cb2`; los commits previos ya están publicados | Publicar este y siguientes commits cuando se completen. |

El checkout está en `master`; al inicio de CAM-039 `origin/master` coincidía con HEAD `7bd4cb2`, por lo que los commits previos ya estaban publicados. Intentos anteriores de push fallaron por credenciales/HTTP 403, pero no describen el estado remoto actual. AWS sigue pendiente.

## Próxima acción concreta

CAM-035 completa la primera comparación emparejada local para P3-03, pero no el gate HTTP/T-22 integral; Dijkstra continúa activa. CAM-041 deja un timer local informativo, pero no cierra P5-04. Siguiente paso: completar radio y recorrido con teclado, probar desconexión/reconexión y revisar sesión expirable; después abordar P5-02/TLS y persistencia antes de cualquier juego desplegado. P2-03/T-11, AWS y reglas oficiales siguen pendientes por evidencia/recursos externos. No afirmar CI remoto, despliegue o seguridad sísmica.

Verificación de CAM-023/024/025: `python3 scripts/check_docs.py` (58 Markdown/60 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho regresiones de `test_check_sdd.py`, suite completa en `/tmp/navira-env` (95 pruebas OK), `compileall` y `git diff --check` correctos. `python -m pip install -e .` y smoke de Uvicorn local demo se completaron en cambios previos; el smoke de carga CAM-020 no es una medición del entorno externo ni prueba persistencia.

Verificación de CAM-028: suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (98 pruebas OK), `python3 scripts/check_docs.py` (59 Markdown/61 archivos), `python3 scripts/check_sdd.py` (seis SPEC), `compileall` y `git diff --check` correctos. Matriz local de cinco turnos por cohorte con Uvicorn loopback; cifras y limitaciones en [reporte CAM-028](resultados/evaluacion-multi-turno-cam028.md). No equivale a medición remota ni reloj de dos segundos.

Verificación de CAM-029: suite completa (100 pruebas), `python3 scripts/check_docs.py` (60 Markdown/62 archivos), `python3 scripts/check_sdd.py`, `compileall` y `git diff --check` correctos. La matriz CLI 20/80/200 se ejecutó a 2 s por tres turnos; cifras y límites en [reporte CAM-029](resultados/evaluacion-cadencia-cam029.md). Commit individual local creado; consola no pudo autenticar y GitHub rechazó la escritura del árbol remoto, por lo que `origin/master` no se actualizó.

Verificación CAM-030: `frontend/npm ci` (24 paquetes, cero vulnerabilidades reportadas), `frontend/npm run build` correcto con Vite 8.3.5 y TypeScript 7.0.2; suite backend (`PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py'`) 100 pruebas correctas; validadores doc y SDD correctos con 60 Markdown; pantalla inspeccionada en navegador local a ancho móvil. `npm run build` falló primero por declaración de CSS ausente, corregida en `vite-env.d.ts`; no quedan errores. El workflow no se ha ejecutado en remoto. El backend/frontend no están integrados.


Verificación CAM-032: ver [entrada de cambio](cambios.md#cam-032-websocket-de-snapshots-completos-y-recuperación-del-panel). El almacenamiento y transporte siguen siendo locales/en memoria; `origin/master` no se ha actualizado.

Verificación de CAM-033: suite completa (120 pruebas OK), incluidos ocho casos de `test_ruta_temporal.py`; `python3 scripts/check_docs.py` (63 Markdown/65 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho regresiones del validador, `compileall`, `git diff --check` y `frontend/npm run build` correctos. Evidencia de una pasada serial para cohortes sintéticas 20/80/200 en [reporte](resultados/busqueda-temporal-cam033.md). No representa comparación T-22 ni medición HTTP.

Verificación de CAM-034: suite completa (125 pruebas OK), incluidas cinco de `test_prediccion_rutas.py`; `python3 scripts/check_docs.py` (64 Markdown/66 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho regresiones del validador, `compileall`, `git diff --check` y `frontend/npm run build` correctos. El modelo solo transforma observaciones construidas por el consumidor; la integración debe garantizar que provengan de la proyección pública y nunca de dormidos/estado privado.

Verificación de CAM-035: suite completa (127 pruebas OK); `python3 scripts/check_docs.py` (66 Markdown/68 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho pruebas del validador, `compileall`, `git diff --check` y `frontend/npm run build` correctos. Matriz de 27 pares ejecutada dos veces; evacuados/mordidos/activos, fallbacks y deltas coincidieron entre repeticiones. El tiempo de recomendación es local y no HTTP.

Verificación de CAM-036: suite completa (134 pruebas OK), incluidas siete pruebas de `test_juego_sesion.py`; `python3 scripts/check_docs.py` (67 Markdown/69 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas), ocho pruebas del validador SDD, `compileall`, `git diff --check` y `frontend/npm run build` correctos. El endpoint requiere inyección explícita; hook de ciclo, órdenes, persistencia y expiración no cubiertos.

Verificación de CAM-037: suite completa (144 pruebas OK), incluidas 10 pruebas de `test_ordenes_juego.py`; `python3 scripts/check_docs.py` (67 Markdown/69 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas), ocho pruebas del validador SDD, `compileall`, `git diff --check` y `frontend/npm run build` correctos. `POST /juego/accion` requiere inyección explícita; repositorio volátil, sin integración con el ciclo ni deadline monotónico.

Verificación de CAM-038: suite backend completa (144 pruebas OK); `python3 scripts/check_docs.py` (67 Markdown/69 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas), ocho pruebas del validador SDD, `compileall`, `git diff --check` y `frontend/npm run build` correctos. Smoke de navegador vio panel en vivo del simulador; no se probó juego humano por falta de backend de juego ensamblado.

## Dependencias externas

Confirmación de región y reglas pendientes; acceso AWS y repositorio remoto no comprobados. Estas dependencias no impiden empezar el núcleo local. No pedir secretos en el chat ni guardarlos en Markdown.

## Trabajo en curso y transferencia

La base API quedó en CAM-006; grafo genérico en CAM-007; entidades/intenciones en CAM-008; resolución en CAM-009; coordinación en CAM-010; puerto CAS en CAM-011; smoke HTTP en CAM-012; Dijkstra genérico en CAM-013; integración HTTP de planificación en CAM-014; bootstrap local explícito en CAM-015; ronda automática por caso de uso en CAM-016; ejecutor CLI en CAM-017; escenarios zombie sintéticos en CAM-018; cohortes sintéticas en CAM-019; cliente de carga en CAM-020; fixture geográfico parcial de Manta y evidencia por amenaza en CAM-021; requisito de simulación estocástica/replay en CAM-022; generador base en CAM-023, replay multi-turno en CAM-024; cohortes sintéticas Manta en CAM-025; evaluación HTTP multi-turno exploratoria en CAM-028 y cadencia temporizada local en CAM-029. Rama local de trabajo: `master`. P0-01 está verificado; P0-02, P1-01/02/03/04/05 y P2-01/02 siguen parciales o en curso. SPEC-001/002 no están verificadas.

## Transferencia CAM-026

El historial local se consolidó primero en `main`, pero el usuario indicó después continuar en `master`; ver CAM-027. El contenido se avanzó en fast-forward a `master`, conservando todos los commits individuales. El remoto `origin/master` se mantiene intacto hasta que sea posible publicar. Las ramas locales `feat/navira-*` y `main` se eliminaron después de verificar que `master` contiene sus commits.
