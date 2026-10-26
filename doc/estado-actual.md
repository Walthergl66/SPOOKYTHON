# Estado actual y punto de reanudación

Última actualización: 2026-10-26. Último cambio: **CAM-021**, en [cambios.md](cambios.md).

## Hechos verificados

- Nombre oficial elegido por el usuario: **Navira**. Documentación vigente y paquete backend previsto `src/navira/` actualizados; decisión ADR-006. El directorio local sigue siendo `SPOOKYTHON`.

- Existe documentación modular en `doc/`, README raíz y protocolo de incorporación en `AGENTS.md`.
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
| Simulador | Resolución y ronda automática por caso de uso con CAS en memoria | DynamoDB, bucle de reloj, publicación, escenarios oficiales y ejecución continua pendientes. |
| Grafo de Manta | Fixture de 300 nodos y cuatro zonas seguras de tsunami generado | Validar cobertura representativa de barrios/rutas peatonales y evaluar amenazas sísmicas con fuentes competentes; el fixture no es para navegación real. |
| Frontend y juego | Pendiente | Compilación y recorrido de usuario. |
| Infraestructura AWS | Pendiente | Recursos, URL y comprobación de salud. |
| Budget con alerta | No verificado | Captura y configuración real. |
| Rendimiento/supervivencia | Sin medir | Reportes de las tres rondas. |
| Repositorio remoto y commits | No verificado | URL y comprobación del historial. |

El repositorio local tiene un remoto Git configurado. CAM-006 a CAM-020 conservan cambios en ramas y commits locales. No se han publicado las ramas al remoto; el despliegue AWS sigue pendiente.

## Próxima acción concreta

Siguiente: revisión visual y de cobertura del fixture de Manta en el panel cuando exista el frontend; completar barrios/rutas peatonales si el análisis detecta vacíos. En paralelo, buscar datos oficiales/locales de microzonificación y evaluación de sitios para terremotos (P-14); no etiquetar los refugios del dataset como sísmicamente seguros hasta entonces. Después integrar el fixture a escenarios y ejecutar carga con un mundo que avance. P-09 sigue pendiente; no hay bucle continuo ni reporte oficial de evaluación. P1-04 requiere persistencia durable/CAS entre hosts; P1-03 sigue parcial por visibilidad/reglas. No declarar integración operacional ni rendimiento hasta ejecutar las rondas oficiales. Configurar Budget cuando se disponga de acceso AWS autorizado.

Comandos documentales: `python3 scripts/check_docs.py` (56 Markdown/58 archivos), `python3 scripts/check_sdd.py` (estructura válida, seis SPEC), ocho regresiones de `test_check_sdd.py`; suite completa en `/tmp/navira-env`: 90 pruebas OK; `compileall` y `git diff --check` correctos tras CAM-021. `python -m pip install -e .` y smoke de Uvicorn local demo completados; el smoke de carga CAM-020 no es una medición del entorno externo ni prueba persistencia.

## Dependencias externas

Confirmación de región y reglas pendientes; acceso AWS y repositorio remoto no comprobados. Estas dependencias no impiden empezar el núcleo local. No pedir secretos en el chat ni guardarlos en Markdown.

## Trabajo en curso y transferencia

La base API quedó en CAM-006; grafo genérico en CAM-007; entidades/intenciones en CAM-008; resolución en CAM-009; coordinación en CAM-010; puerto CAS en CAM-011; smoke HTTP en CAM-012; Dijkstra genérico en CAM-013; integración HTTP de planificación en CAM-014; bootstrap local explícito en CAM-015; ronda automática por caso de uso en CAM-016; ejecutor CLI en CAM-017; escenarios zombie sintéticos en CAM-018; cohortes sintéticas en CAM-019; cliente de carga en CAM-020; fixture geográfico parcial de Manta y evidencia por amenaza en CAM-021. Rama de trabajo: `feat/navira-manta-hazard-map`. P0-01 está verificado; P0-02, P1-01/02/03/04/05 y P2-01/02 siguen parciales o en curso. SPEC-001/002 no están verificadas.
