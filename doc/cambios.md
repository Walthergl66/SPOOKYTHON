# Historial de cambios y contexto

Registro acumulativo. No reemplaza commits; al existir un repositorio operativo, enlazar revisión real sin inventarla. Las dos primeras entradas se reconstruyen de esta conversación, no de un historial Git comprobado.

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

## Próximas entradas

Usar [plantilla de cambio](plantillas/cambio.md). Cada entrada significativa explica qué disparó el cambio, por qué, qué áreas toca, qué se comprobó y cómo continuar. Conservar entradas anteriores; corregir datos erróneos dejando constancia, no reescribiendo la historia silenciosamente.
