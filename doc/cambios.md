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

## Próximas entradas

Usar [plantilla de cambio](plantillas/cambio.md). Cada entrada significativa explica qué disparó el cambio, por qué, qué áreas toca, qué se comprobó y cómo continuar. Conservar entradas anteriores; corregir datos erróneos dejando constancia, no reescribiendo la historia silenciosamente.
