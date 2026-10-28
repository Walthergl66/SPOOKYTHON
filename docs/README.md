# Índice general de la documentación

Actualizado: 2026-10-28, CAM-150. Ubicación canónica: `docs/`. La antigua carpeta `doc/` ya no existe. Cada tema tiene su carpeta; este archivo dice dónde está cada documento. El plan vigente es [plan de implementación](seguimiento/plan-implementacion.md); el anterior se conserva como referencia histórica en [referencias/](referencias/).

## Dónde está cada cosa

| Carpeta | Qué contiene | Entrada principal |
|---|---|---|
| [producto/](producto/) | Qué se construye, para quién y con qué alcance: PRD, TRD y contexto. | [PRD](producto/PRD.md) |
| [dominio/](dominio/) | Lenguaje y reglas del mundo, modos de juego, flujos por rol, datos y el fixture de Manta. | [ODDD](dominio/ODDD.md) |
| [arquitectura/](arquitectura/) | Componentes, contratos HTTP y WebSocket, módulos, algoritmos y decisiones (ADR). | [arquitectura](arquitectura/arquitectura.md) |
| [metodo/](metodo/) | Cómo trabajamos: SDD, especificaciones SPEC, trazabilidad, continuidad y plantillas. | [SDD](metodo/SDD.md) |
| [seguimiento/](seguimiento/) | Estado actual, historial de cambios CAM, pendientes y plan de tareas. | [estado actual](seguimiento/estado-actual.md) |
| [calidad/](calidad/) | Pruebas T-NN y evidencias de resultados (`resultados/`). | [pruebas](calidad/pruebas.md) |
| [operacion/](operacion/) | Infraestructura AWS, seguridad y costos. | [infraestructura](operacion/infraestructura.md) |
| [referencias/](referencias/) | Textos de origen: reto original y propuestas históricas. No son el plan vigente. | [reto original](referencias/reto-original.md) |

## Lectura de incorporación

Seguir [AGENTS.md](../AGENTS.md): primero este índice, [contexto](producto/contexto.md), [estado actual](seguimiento/estado-actual.md), [continuidad](metodo/continuidad.md), [cambios](seguimiento/cambios.md) y [pendientes](seguimiento/pendientes.md). Después revisar los documentos de las carpetas que vayas a tocar antes de la primera modificación de una tarea. Los históricos y plantillas se reconocen como tales, no como requisitos vigentes. No hay que releer todo antes de cada comando de una misma tarea.

## producto/

| Documento | Fuente principal de | Actualizar cuando |
|---|---|---|
| [PRD.md](producto/PRD.md) | Necesidades, alcance e IDs de producto | Cambien objetivos o requisitos de producto. |
| [TRD.md](producto/TRD.md) | IDs y condiciones técnicas verificables | Cambien restricciones o garantías requeridas. |
| [contexto.md](producto/contexto.md) | Objetivo, alcance y decisiones del usuario | Cambie producto o alcance. |

## dominio/

| Documento | Fuente principal de | Actualizar cuando |
|---|---|---|
| [ODDD.md](dominio/ODDD.md) | Lenguaje, límites e invariantes OO + DDD | Cambie el modelo del dominio. |
| [reglas-juego.md](dominio/reglas-juego.md) | Reglas de simulación y supuestos | Se confirme o cambie una regla. |
| [modos.md](dominio/modos.md) | Diferencias entre simulador y juego | Cambie control o experiencia. |
| [datos.md](dominio/datos.md) | Entidades, estados e identidad de versiones | Cambie persistencia o proyección. |
| [mapa-manta.md](dominio/mapa-manta.md) | Procedencia, alcance y límites del fixture geográfico de Manta | Cambien las fuentes, extensión o metodología del dataset. |
| [flujos/roles.md](dominio/flujos/roles.md) | Actores, permisos y responsabilidades | Aparezca un actor o permiso. |
| [flujos/simulador.md](dominio/flujos/simulador.md) | Ciclo del turno automático | Cambie secuencia o reloj. |
| [flujos/jugador.md](dominio/flujos/jugador.md) | Entrada, órdenes y salida del jugador | Cambie la interacción humana. |
| [flujos/espectador.md](dominio/flujos/espectador.md) | Observación y reconexión | Cambie el panel de lectura. |
| [flujos/operador.md](dominio/flujos/operador.md) | Inicio, eventos y cierre de partidas | Cambien controles administrativos. |

## arquitectura/

| Documento | Fuente principal de | Actualizar cuando |
|---|---|---|
| [arquitectura.md](arquitectura/arquitectura.md) | Componentes, límites y dependencias | Cambien estructura o comunicaciones. |
| [algoritmos.md](arquitectura/algoritmos.md) | Planificación y predicción, incluida coordinación por snapshot CAM-061 y reducción de trabajo del pronóstico CAM-086 | Cambie la política o rendimiento del pronóstico. |
| [contratos/api.md](arquitectura/contratos/api.md) | Contrato HTTP y autenticación | Cambien rutas, cuerpos o errores. Estado y ejemplos de las proyecciones del panel incluyen CAM-031. |
| [contratos/eventos.md](arquitectura/contratos/eventos.md) | Contrato WebSocket y orden de mensajes | Cambien eventos o recuperación. El canal de snapshots del panel se implementa localmente en CAM-032. |
| [modulos/backend.md](arquitectura/modulos/backend.md) | Ubicación de responsabilidades backend | Se cree o mueva un caso de uso. |
| [modulos/frontend.md](arquitectura/modulos/frontend.md) | Módulos y estados de interfaz | Se cree o mueva una pantalla. Estado del scaffold en `frontend/`; no sustituye los contratos del panel. |
| [decisiones/README.md](arquitectura/decisiones/README.md) | Registro e índice de ADR | Cambie una decisión duradera. |
| [ADR-001](arquitectura/decisiones/0001-arquitectura-base.md) | Núcleo modular Python, API FastAPI y stack AWS inicial | Cambie el stack, la topología o la separación de capas. |
| [ADR-002](arquitectura/decisiones/0002-dos-modos.md) | Simulador y juego comparten mundo y reglas | Cambie la relación entre modos o sus reglas compartidas. |
| [ADR-003](arquitectura/decisiones/0003-estado-y-turnos.md) | Versiones por partida/turno/fase y coordinador único | Cambie el versionado de estado o la autoridad del coordinador. |
| [ADR-004](arquitectura/decisiones/0004-documentacion-y-continuidad.md) | `docs/` canónico y protocolo de incorporación | Cambie la ubicación de la documentación o el protocolo de continuidad. |
| [ADR-005](arquitectura/decisiones/0005-prd-trd-oddd-sdd.md) | PRD/TRD, modelo OO + DDD y SDD trazable | Cambie el método documental. |
| [ADR-006](arquitectura/decisiones/0006-nombre-navira.md) | Nombre oficial Navira | Cambie el nombre del producto. |
| [ADR-007](arquitectura/decisiones/0007-mapa-manta-y-evidencia-de-amenazas.md) | Fuentes de mapa y límites de seguridad por amenaza | Cambien fuentes del mapa o límites de amenaza. |
| [ADR-008](arquitectura/decisiones/0008-simulacion-estocastica-reproducible.md) | Aleatoriedad del mundo, reproducción y privacidad del generador | Cambien condiciones de estocasticidad o replay. |
| [ADR-009](arquitectura/decisiones/0009-panel-ws-snapshots-completos.md) | Snapshots completos del WebSocket de observación | Cambie el transporte, cursor o recuperación del panel. |
| [ADR-010](arquitectura/decisiones/0010-busqueda-temporal-acotada.md) | Prioridad, límite y uso de la ruta temporal experimental | Cambie horizonte, función de costo o integración en política. |
| [ADR-011](arquitectura/decisiones/0011-pronostico-visible-por-escenarios.md) | Frontera de información y supuestos del pronóstico observable | Cambie inputs, probabilidades/ocupación o reglas modeladas por pronóstico. |
| [ADR-012](arquitectura/decisiones/0012-seleccion-politica-baseline.md) | Política de rutas activa y evidencia que condiciona su selección | Cambie baseline, evidencia comparativa o criterios para integración temporal. |
| [ADR-013](arquitectura/decisiones/0013-sesion-y-aparicion-humana-local.md) | Propiedad de jugador, cookie y ciclo de aparición humana | Cambie sesiones, aparición o límites de seguridad del modo juego. |
| [ADR-014](arquitectura/decisiones/0014-expiracion-local-de-sesion-humana.md) | TTL local de sesión humana y propiedad retenida al vencer | Cambie la política de sesión, recuperación o cupo humano. |
| [ADR-015](arquitectura/decisiones/0015-control-local-de-demo.md) | Control local del simulador solo en loopback con opt-in | Cambie el control local o su superficie. |
| [ADR-016](arquitectura/decisiones/0016-mapa-maplibre-openfreemap.md) | Renderer MapLibre, proveedor vectorial OpenFreeMap y límites 3D | Cambie el proveedor, estilo, credenciales o forma de renderizar geometría. |
| [ADR-017](arquitectura/decisiones/0017-perfiles-sinteticos-de-amenazas.md) | Intensidad sintética distribuida por sectores e incidentes viales de demo | Cambien densidades configurables, composición o calendario de cierres de demo. |
| [ADR-018](arquitectura/decisiones/0018-politica-riesgo-prioritario.md) | Política temporal que prioriza exposición observable, respaldo Dijkstra y criterio mordidos/evacuados | Cambie orden de objetivos, horizonte, modelo de riesgo o respaldo de ruta. |
| [ADR-019](arquitectura/decisiones/0019-cruces-y-ruta-consistente.md) | Exposición de cruces opuestos, escape inmediato y coincidencia de ruta por snapshot | Cambie el modelo de cruces o la consistencia entre ruta mostrada y acción. |
| [ADR-020](arquitectura/decisiones/0020-planificacion-coordinada-por-snapshot.md) | Asignación conjunta y penalización suave de congestión por snapshot | Cambie la política coordinada o su objetivo/costo. |
| [ADR-021](arquitectura/decisiones/0021-dificultad-inicial-demo.md) | Intensidad media inicial para la demo y controles de dificultad | Cambie el valor inicial o el criterio de selección de intensidad. |
| [ADR-022](arquitectura/decisiones/0022-organizacion-documental-por-temas.md) | Organización de docs/ por temas con índice general | Cambie la estructura de carpetas o la ubicación de un documento. |
| [ADR-023](arquitectura/decisiones/0023-configuracion-de-agentes.md) | Configuración de agentes en `.claude/` y guías por área en `.agents/` | Cambie reglas, skills, comandos o guías de agentes. |
| [ADR-024](arquitectura/decisiones/0024-backend-y-frontend-por-carpeta.md) | Backend en `backend/`, frontend en `frontend/` y raíz general | Cambie la ubicación de backend, frontend o los README de cada área. |
| [ADR-025](arquitectura/decisiones/0025-agentes-de-proyecto-y-clean-architecture.md) | Subagentes de proyecto y Clean Architecture como destino | Cambie la guía de capas o los subagentes de proyecto. |
| [ADR-026](arquitectura/decisiones/0026-aplanado-backend-y-setuptools.md) | Aplanado de `backend/src` y setuptools (sustituida por ADR-027) | Consulte el antecedente del aplanado. |
| [ADR-027](arquitectura/decisiones/0027-reversion-del-aplanado-de-backend.md) | Reversión del aplanado: `backend/src/navira/` y hatchling | Cambie la estructura del paquete o el sistema de build del backend. |
| [ADR-028](arquitectura/decisiones/0028-configuracion-de-seguridad-inyectada.md) | Configuración de seguridad leída una vez e inyectada | Cambie cómo `api/` obtiene la clave o los flags de seguridad. |
| [ADR-029](arquitectura/decisiones/0029-cobertura-y-rutas-mapa-ampliado.md) | Alcance rectangular del cantón Manta, fixture OSM ampliado y campo inverso por snapshot | Extensión y planificación CAM-073; cobertura municipal y SLA siguen pendientes. |
| [ADR-030](arquitectura/decisiones/0030-ventana-urbana-zona-jugable.md) | Ventana urbana como límite topológico jugable y del selector de refugios | CAM-077; caja no certificada como frontera municipal. |
| [ADR-031](arquitectura/decisiones/0031-perimetro-refugios-manta.md) | Perímetro zombie de una cuadra alrededor de refugios | CAM-078/T-40; calibración geográfica pendiente. |
| [ADR-032](arquitectura/decisiones/0032-incidentes-viales-siempre-activos-en-demo.md) | Incidentes viales siempre activos, sin control en el menú de demo | CAM-081/T-43; campo HTTP legado ignorado. |
| [ADR-033](arquitectura/decisiones/0033-alerta-y-cierres-aleatorios.md) | Incidentes viales 1–10, cierre y alerta cartográfica al aplicarse | CAM-082/T-44; no se revelan eventos futuros. |
| [ADR-034](arquitectura/decisiones/0034-rutas-estables-y-replanificacion-cercana.md) | Conservar ruta confirmada y replantear ante amenaza cercana o invalidez | CAM-084; radio inicial de tres saltos y T-46 pendientes de validación conductual. |
| [ADR-035](arquitectura/decisiones/0035-flujo-evaluacion-reto.md) | Flujo de evaluación separado de demo libre, sobre el modo automático compartido | CAM-088; presets locales probados, campaña completa y despliegue pendientes. |
| [ADR-036](arquitectura/decisiones/0036-ruta-individual-bajo-demanda.md) | Consultar bajo demanda la ruta del habitante seleccionado fuera de la fase de decisiones | CAM-093; evitar calcular rutas de toda la población en cada fase. |
| [ADR-037](arquitectura/decisiones/0037-spawn-reto-cuatro-sectores.md) | Muestrear sobrevivientes del Reto en cuatro zonas sectoriales aproximadas y mantener libre el spawn del Simulador | Cambie el origen geográfico inicial del Reto o aparezca una geometría oficial. |
| [ADR-038](arquitectura/decisiones/0038-foco-amenazas-reto.md) | Concentración provisional de amenazas/eventos del Reto en un núcleo urbano de Manta | Cambie la distribución espacial de amenazas del Reto o se confirme un modelo oficial. |
| [ADR-039](arquitectura/decisiones/0039-reinicio-ronda-reto.md) | Reinicio de la ronda Reto actual con mundo nuevo | Cambie el ciclo de vida o el contrato de reinicio Reto. |
| [ADR-040](arquitectura/decisiones/0040-reemplazo-reto-pausado.md) | Reemplazo de un run Reto pausado por otro preset | Cambie cuándo una partida local puede sustituirse por otro preset Reto. |
| [ADR-042](arquitectura/decisiones/0042-juego-operador-mundo-interactivo.md) | «Jugar» como modo de operador que interviene un mundo automático vivo | Cambie la experiencia de Jugar o sus límites de intervención local. |
| [ADR-043](arquitectura/decisiones/0043-filtros-de-riesgo-y-rutas-comprometidas.md) | Filtros compartidos para incidentes, hordas, zombies próximos y rutas comprometidas | Cambie las reglas de transitabilidad o la política de riesgo alrededor de amenazas. |
| [ADR-044](arquitectura/decisiones/0044-reemplazo-explicito-al-cambiar-de-modo.md) | Inicio explícito desde el modo destino reemplaza el run local con un mundo nuevo | Cambie el ciclo de vida o transición de runs entre Reto, Simulador y Jugar. |
| [ADR-045](arquitectura/decisiones/0045-evaluacion-aws-privada.md) | Staging privado y evaluación AWS efímera sin controles locales expuestos | Cambie la topología, permisos o método de evaluación en AWS. |
| [ADR-046](arquitectura/decisiones/0046-demo-publica-multisesion.md) | Demo temporal abierta con mundos aislados por cookie anónima | Cambie el modo público, sus límites o topología temporal. |
| [ADR-047](arquitectura/decisiones/0047-despliegue-lightsail-desde-github-actions.md) | Despliegue de `master` en Lightsail mediante GitHub Actions y SSH | Cambie la cadena de build, conectividad, rollback o destino. |
| [ADR-050](arquitectura/decisiones/0050-despliegue-lightsail-oidc-firewall-temporal.md) | CD con OIDC y acceso SSH temporal acotado al runner | Cambie identidad AWS, permisos o firewall temporal de Actions. |
| [ADR-051](arquitectura/decisiones/0051-replanificacion-a-refugio-alternativo.md) | Elegir un refugio alcanzable cuando el objetivo asignado pierde toda ruta legal | Cambie la política de destino alternativo del planificador. |
| [ADR-052](arquitectura/decisiones/0052-perfiles-narrativos-aislados.md) | Perfiles narrativos ficticios estables, sin alterar el RNG del mundo | Cambie catálogo, asignación o alcance narrativo. |
| [ADR-053](arquitectura/decisiones/0053-sectores-por-poligonos-geomanta.md) | Asignar barrio/parroquia de refugios por polígonos GeoManta, con snapshot local | Cambie fuente, método espacial o cobertura de etiquetas territoriales. |
| [ADR-048](arquitectura/decisiones/0048-puente-r2-como-condicion-inicial.md) | Aplicar el puente colapsado de R2 al inicio antes de la primera decisión | Cambie el calendario/semántica inicial del puente del Reto. |
| [guia-clean-architecture.md](arquitectura/guia-clean-architecture.md) | Regla de dependencia, capas objetivo, línea base y pasos de migración de backend y frontend | Cambie una capa, un puerto o un paso de migración. |

## metodo/

| Documento | Fuente principal de | Actualizar cuando |
|---|---|---|
| [SDD.md](metodo/SDD.md) | Ciclo Specify/Plan/Implement/Verify/Document | Cambie el procedimiento de desarrollo. |
| [trazabilidad.md](metodo/trazabilidad.md) | Vínculos PRD/TRD → SPEC → tareas/pruebas | Cambien requisitos o referencias. |
| [continuidad.md](metodo/continuidad.md) | Protocolo de inicio, cierre y transferencia | Cambie la forma de colaborar. |
| [especificaciones/README.md](metodo/especificaciones/README.md) | Funcionalidades con criterios CA, tareas y pruebas | Se añada o cambie una funcionalidad. |
| [SPEC-001](metodo/especificaciones/SPEC-001-mundo-simulacion.md) | Mundo y simulación | Cambie reglas del mundo o simulación. |
| [SPEC-002](metodo/especificaciones/SPEC-002-motor-paso.md) | Motor y siguiente paso (`/paso`) | Cambie el contrato o la política de `/paso`. |
| [SPEC-003](metodo/especificaciones/SPEC-003-panel-vivo.md) | Panel de observación en vivo | Cambie el panel o su transporte. |
| [SPEC-004](metodo/especificaciones/SPEC-004-juego-humano.md) | Personaje humano | Cambie el modo juego. |
| [SPEC-005](metodo/especificaciones/SPEC-005-aws-evaluacion.md) | AWS, evaluación y entrega | Cambie la infraestructura o la entrega. |
| [SPEC-006](metodo/especificaciones/SPEC-006-metodologia.md) | PRD, TRD, ODDD y SDD | Cambie el método documental. |
| [SPEC-007](metodo/especificaciones/SPEC-007-panel-operador-local.md) | Criterios del tablero y control local de demo, incluida pausa confirmada por servidor (CAM-134/T-60) | Cambie el flujo local de operación; no autoriza control administrativo público. |
| [SPEC-008](metodo/especificaciones/SPEC-008-mapa-cartografico-3d.md) | Criterios del mapa vectorial, vista 3D, precarga y etiquetas de calles por zoom (CAM-134/T-59, CAM-142/T-64) | Cambie el renderer/cartografía del panel; no convierte el proveedor en motor de simulación. |
| [SPEC-009](metodo/especificaciones/SPEC-009-modo-reto.md) | Presets de la prueba de fuego, separados de demo libre y juego | Cambien las rondas, sus presets o la campaña de evaluación. |
| [SPEC-010](metodo/especificaciones/SPEC-010-juego-operador.md) | Paleta de operador, nueva partida e intervención del mapa en un mundo vivo | Cambien herramientas, ciclo de partida, validaciones o colocación local de entidades/eventos. |
| [SPEC-011](metodo/especificaciones/SPEC-011-demo-publica-multisesion.md) | Demo pública multisesión para Reto, Simulador y Jugar | Cambien aislamiento por navegador, límites, expiración o topología pública temporal. |
| [plantillas/cambio.md](metodo/plantillas/cambio.md) | Formato de cambio | Se necesiten campos nuevos. |
| [plantillas/decision.md](metodo/plantillas/decision.md) | Formato de ADR | Se necesiten campos nuevos. |
| [plantillas/transferencia.md](metodo/plantillas/transferencia.md) | Formato de transferencia | Cambie el protocolo de continuidad. |
| [plantillas/especificacion.md](metodo/plantillas/especificacion.md) | Formato de SPEC y criterios CA | Cambie la estructura de especificaciones. |
| [plantillas/plan-cambio.md](metodo/plantillas/plan-cambio.md) | Plan proporcional dentro de una tarea/SPEC | Cambie la planificación de cambios. |

## seguimiento/

| Documento | Fuente principal de | Actualizar cuando |
|---|---|---|
| [estado-actual.md](seguimiento/estado-actual.md) | Evidencia de lo existente y siguiente acción | Se complete o interrumpa trabajo. |
| [cambios.md](seguimiento/cambios.md) | Historial del qué, por qué y validación | Se cierre un cambio significativo. |
| [pendientes.md](seguimiento/pendientes.md) | Dudas, riesgos y confirmaciones | Se descubra o resuelva una incertidumbre. |
| [plan-implementacion.md](seguimiento/plan-implementacion.md) | Tareas, dependencias y criterios de salida | Se ajuste o complete una fase. |

## calidad/

| Documento | Fuente principal de | Actualizar cuando |
|---|---|---|
| [pruebas.md](calidad/pruebas.md) | Verificación y métricas | Cambie comportamiento o aceptación. |
| [resultados/carga-local-cam020.md](calidad/resultados/carga-local-cam020.md) | Evidencia de ráfagas HTTP locales | Se ejecute una medición local reproducible; no sustituye resultados oficiales. |
| [resultados/busqueda-temporal-cam033.md](calidad/resultados/busqueda-temporal-cam033.md) | Tiempo de búsqueda temporal por llamada para cohortes sintéticas 20/80/200 | Nueva versión de algoritmo o ejecución comparativa; no es medición HTTP ni T-22. |
| [resultados/comparacion-rutas-cam035.md](calidad/resultados/comparacion-rutas-cam035.md) | Comparación emparejada Dijkstra/temporal en tres turnos locales | Cambien política, semilla, mapa, perfiles o método comparativo. No reemplaza T-22/T-11. |
| [resultados/simulacion-manta-cam025.md](calidad/resultados/simulacion-manta-cam025.md) | Ejecución exploratoria de cohortes sintéticas en el grafo Manta | Cambien configuración/resultados del ensayo; no equivale a evaluación oficial ni seguridad real. |
| [resultados/evaluacion-multi-turno-cam028.md](calidad/resultados/evaluacion-multi-turno-cam028.md) | Medición HTTP loopback con avance de turnos y cohortes 20/80/200 | Nueva ejecución multi-turno; evidencia local exploratoria, no sustituye T-11 ni AWS. |
| [resultados/evaluacion-cadencia-cam029.md](calidad/resultados/evaluacion-cadencia-cam029.md) | Cadencia objetivo de 2 s para evaluaciones HTTP multi-turno locales | Nueva medición temporizada; evidencia exploratoria, no sustituye T-11 ni AWS. |
| [resultados/evaluacion-p501-cam044.md](calidad/resultados/evaluacion-p501-cam044.md) | Medición extendida local por HTTP loopback para cohortes 20/80/200 | Nueva ejecución P5-01; las partidas terminaron antes de 150 turnos, no acredita T-11 ni AWS. |
| [resultados/duracion-ronda-cam087.md](calidad/resultados/duracion-ronda-cam087.md) | Ventana de duración local completa con slots ociosos explícitos tras fin temprano; no equivale a carga sostenida | Cambie el evaluador o se ejecute T-11; escenarios/repeticiones y AWS siguen pendientes. |
| [resultados/panel-operador-local-cam050.md](calidad/resultados/panel-operador-local-cam050.md) | Evidencia de inicio/pausa manual del panel local y verificaciones de CAM-050 | Cambien el control local o se repita la inspección del tablero; no acredita despliegue productivo ni uso de emergencia. |
| [resultados/ficha-habitante-cam085.md](calidad/resultados/ficha-habitante-cam085.md) | Reubicación al panel izquierdo de la ficha del habitante seleccionado y su ruta | Cambie ubicación o contenido de esta ficha; evidencia de pruebas/build, no inspección visual. |
| [resultados/mapa-cartografico-3d-cam051.md](calidad/resultados/mapa-cartografico-3d-cam051.md) | Evidencia de carga de cartografía, atribución, edificios y alternancia 2D/3D de CAM-051 | Cambien el renderer/proveedor o se repita la inspección; no acredita cobertura completa, SLA ni uso de emergencia. |
| [resultados/movimiento-mapa-cam052.md](calidad/resultados/movimiento-mapa-cam052.md) | Evidencia de fichas animadas, cámara encuadrada y sincronización de un nuevo run en CAM-052 | Cambie la transición de actores o el cambio de partida; no acredita reglas oficiales, precisión vial ni uso de emergencia. |
| [resultados/limites-mapa-cam053.md](calidad/resultados/limites-mapa-cam053.md) | Evidencia de cámara, pan y máscara exterior limitados al recorte cartográfico de Manta en CAM-053 | Cambie la extensión del fixture o el comportamiento de cámara; no acredita límite administrativo ni cobertura municipal completa. |
| [resultados/ampliacion-mapa-cam054.md](calidad/resultados/ampliacion-mapa-cam054.md) | Evidencia del aumento de margen alrededor del área cartográfica de Manta en CAM-054 | Cambie el margen o la ventana de visualización; no acredita límite administrativo ni cobertura municipal completa. |
| [resultados/ampliacion-50km-mapa-cam055.md](calidad/resultados/ampliacion-50km-mapa-cam055.md) | Evidencia del viewport ampliado aproximadamente 50 km por lado en CAM-055 | Cambie el margen o la ventana de visualización; no amplía el grafo ni acredita límite administrativo o cobertura municipal completa. |
| [resultados/reduccion-15km-mapa-cam056.md](calidad/resultados/reduccion-15km-mapa-cam056.md) | Evidencia del viewport reducido a unos 15 km por lado en CAM-056 | Cambie el margen o la ventana de visualización; no amplía el grafo ni acredita límite administrativo o cobertura municipal completa. |
| [resultados/cobertura-manta-cam073.md](calidad/resultados/cobertura-manta-cam073.md) | Cobertura jugable del fixture ampliado CAM-073, origen/versiones/conteos, pruebas, muestra de sectores, render local y límites de cobertura/payload. | Nueva extracción o cambio de extensión y metodología. |
| [resultados/margen-navegacion-5km-cam074.md](calidad/resultados/margen-navegacion-5km-cam074.md) | Margen de navegación de 5 km por lado para el mapa completo de Manta; no modifica el grafo jugable. | Cambie el margen visual o la conversión de coordenadas. |
| [resultados/mar-visible-cam075.md](calidad/resultados/mar-visible-cam075.md) | Contraste del agua y máscara cartográfica fuera del margen CAM-074; verificado en navegador local. | Cambie estilo de agua, máscara o margen; no acredita SLA ni exactitud cartográfica. |
| [resultados/ventana-urbana-cam076.md](calidad/resultados/ventana-urbana-cam076.md) | Antecedente de la ventana urbana visual, convertida en límite jugable por CAM-077. | Cambie la ventana o verificación visual; consulte también CAM-077. |
| [resultados/limite-jugable-cam077.md](calidad/resultados/limite-jugable-cam077.md) | Recorte topológico del mundo Manta y restricción del selector de refugios. | Cambie el límite, la proyección o la selección. |
| [resultados/perimetro-refugios-cam078.md](calidad/resultados/perimetro-refugios-cam078.md) | Protección topológica de una cuadra alrededor de refugios Manta frente a generación y movimiento zombie. | Cambie el búfer, su alcance o la evidencia de verificación. |
| [resultados/fluidez-turnos-cam079.md](calidad/resultados/fluidez-turnos-cam079.md) | Evidencia de velocidad local 4× e interpolación continua de movimientos confirmados CAM-079. | Cambie la cadencia, la política de animación o se ejecute una medición visual/de carga. |
| [resultados/fluidez-pronostico-cam086.md](calidad/resultados/fluidez-pronostico-cam086.md) | Optimización del pronóstico de amenazas mediante agregación lineal y caché del grafo; registra pruebas y límites de medición en CAM-086. | Cambie el algoritmo de pronóstico o se mida cadencia comparable bajo carga. |
| [resultados/optimizacion-rutas-cam132.md](calidad/resultados/optimizacion-rutas-cam132.md) | Perfil de Dijkstra repetido, optimización del plan de rutas por cohorte y medición local p95 CAM-132. | Cambie la agrupación de rutas o se repita T-11; la muestra local no demuestra latencia pública ni p95 sostenido. |
| [resultados/optimizacion-validacion-paso-cam133.md](calidad/resultados/optimizacion-validacion-paso-cam133.md) | Quita la validación lineal de toda la cohorte de cada solicitud `/paso` y registra muestras posteriores. | Cambie la validación de snapshots o se repita T-11; la evidencia local no acredita el objetivo sostenido ni latencia pública. |
| [resultados/incidentes-siempre-activos-cam081.md](calidad/resultados/incidentes-siempre-activos-cam081.md) | Campo legado ignorado y ausencia del selector de incidentes en la demo local. | Cambie el comportamiento o los controles de incidentes. |
| [resultados/alerta-incidentes-cam082.md](calidad/resultados/alerta-incidentes-cam082.md) | Sorteo de 1–10 cierres, alerta cartográfica y recálculo de rutas tras aplicar. | Cambie el generador, la proyección o el marcador; no representa choques reales ni uso de emergencia. |
| [resultados/generador-amenazas-cam057.md](calidad/resultados/generador-amenazas-cam057.md) | Verificación del generador sintético de amenazas y cierres viales CAM-057 | Repetir pruebas de densidad espacial, semilla, privacidad de dormidos y aplicación de incidentes; no acredita parámetros oficiales. |
| [resultados/politica-riesgo-cam058.md](calidad/resultados/politica-riesgo-cam058.md) | Integración local y comparación emparejada riesgo-primero CAM-058 | Cambien la política o se repita la evaluación; no acredita T-11 ni mejora por semilla o uso de emergencia. |
| [resultados/ruta-cruces-cam059.md](calidad/resultados/ruta-cruces-cam059.md) | Diagnóstico 20/20 mordidos, exposición de cruces futuros y consistencia de ruta CAM-059 | Cambien el modelo de cruces o se repita evaluación; evidencia parcial no acredita menor mortalidad universal. |
| [resultados/coordinacion-rutas-cam061.md](calidad/resultados/coordinacion-rutas-cam061.md) | Comparación exploratoria de la política coordinada contra Dijkstra en tres pares CAM-061 | Cambien la política, muestra o evaluación; no acredita efecto causal separado ni mejora universal. |
| [resultados/horizonte-riesgo-cam062.md](calidad/resultados/horizonte-riesgo-cam062.md) | Evidencia funcional de puntaje de exposición limitado al horizonte y comparación exploratoria CAM-062 | Cambie el límite del pronóstico o se repita la evaluación; seis pares sintéticos no demuestran efecto causal ni mejora universal. |
| [resultados/default-media-cam063.md](calidad/resultados/default-media-cam063.md) | Comparación emparejada de intensidad media frente a alta que motiva el default de demo CAM-063 | Cambie generador/configuración o se repita evaluación; muestra de tres semillas y un escenario. |
| [resultados/reto-foco-reinicio-cam095.md](calidad/resultados/reto-foco-reinicio-cam095.md) | Verificación local de la concentración central por tipo y reinicio del preset Reto | Cambie radio/cuota o ciclo de reinicio; no acredita densidad oficial, T-11 o AWS. |
| [resultados/control-reto-pausa-cam096.md](calidad/resultados/control-reto-pausa-cam096.md) | Evidencia CAM-096: pausa y continuación de la ronda Reto | Cambien controles compartidos o se repita la verificación. |
| [resultados/reto-nueva-simulacion-pausada-cam097.md](calidad/resultados/reto-nueva-simulacion-pausada-cam097.md) | Evidencia CAM-097: iniciar un preset nuevo desde Reto pausado | Cambie el comportamiento de sustitución o se repita su prueba. |
| [resultados/campana-reto-cam098.md](calidad/resultados/campana-reto-cam098.md) | Campaña local secuencial R1/R2/R3 con ventana de cinco minutos y medición HTTP loopback; distingue actividad de slots ociosos | Nueva versión del evaluador o campaña; no equivale a AWS ni demuestra 150 turnos activos. |
| [resultados/repeticiones-reto-cam099.md](calidad/resultados/repeticiones-reto-cam099.md) | Tres campañas locales R1/R2/R3 con semillas distintas; nueve rondas, carga y variación de resultados | Nueva repetición comparable o ejecución AWS; no sustituye prueba oficial. |
| [resultados/campana-aws-cam125.md](calidad/resultados/campana-aws-cam125.md) | Una campaña completa R1/R2/R3 en ECS Fargate, Ohio; identifica digest, métricas loopback, eventos y límites | Nueva ejecución AWS o cambio de imagen; no acredita endpoint público, ALB ni evaluación oficial. |
| [resultados/verificacion-sdd.md](calidad/resultados/verificacion-sdd.md) | Evidencia de incorporación metodológica | Conservar resultados de CAM-004; nuevas ejecuciones se registran sin alterar resultados históricos. |

## operacion/

| Documento | Fuente principal de | Actualizar cuando |
|---|---|---|
| [infraestructura.md](operacion/infraestructura.md) | Despliegue y operación AWS | Cambie un recurso o procedimiento. |
| [guia-paso-a-paso-despliegue.md](operacion/guia-paso-a-paso-despliegue.md) | Guía interactiva de preparación para despliegue | Cambien sus pasos o requisitos previos. |
| [seguridad.md](operacion/seguridad.md) | Autenticación y límites de confianza | Cambien accesos o secretos. |
| [costos.md](operacion/costos.md) | Estimación y gasto real | Cambie infraestructura o consumo. |

## referencias/

Textos de origen. Se conservan tal cual; no son el plan vigente.

| Documento | Fuente principal de | Actualizar cuando |
|---|---|---|
| [reto-original.md](referencias/reto-original.md) | Texto del reto proporcionado por el usuario | Conservar como fuente; añadir aclaraciones aparte. |
| [plan-previo.md](referencias/plan-previo.md) | Propuesta histórica anterior | No modificar como documento vigente. |
| [propuesta-sdd.md](referencias/propuesta-sdd.md) | Propuesta aportada por el usuario | Conservar como referencia; adaptación vigente en SDD. |

## Estados y resolución de discrepancias

- **Requisito del reto:** consta en el texto proporcionado. Una aclaración posterior debe tener fecha y fuente.
- **Decisión del usuario:** instrucción explícita; registrar su efecto sobre alcance y diseño.
- **Decisión de diseño:** adoptada para implementar, sin afirmar que ya exista código.
- **Supuesto pendiente:** interpretación provisional identificada en [pendientes](seguimiento/pendientes.md).
- **Implementado:** existe código; **verificado:** además hay evidencia de ejecución. No son sinónimos.
- **Histórico:** explica cómo se llegó al estado vigente; no lo reemplaza.

Las instrucciones actuales del usuario y las reglas superiores de la sesión prevalecen sobre estos documentos. Para describir implementación real se comprueba el repositorio y la evidencia. Si código y contrato difieren, registrar la discrepancia y resolverla; no declarar correcto el código solo por existir. No sobrescribir un requisito del reto con una suposición sin dejar trazabilidad.

PRD identifica producto, TRD condiciones técnicas y SPEC aceptación por funcionalidad; arquitectura y ODDD definen diseño e invariantes. La jerarquía y resolución de conflictos se detallan en [SDD](metodo/SDD.md). Mantener IDs estables y enlaces a fuentes propietarias; ningún archivo nuevo permite alterar requisitos silenciosamente.

## Cómo añadir un documento

Colocarlo en la carpeta de su tema, enlazarlo en la tabla de esta sección y, si la carpeta tiene índice propio (`arquitectura/decisiones/` o `metodo/especificaciones/`), también allí. Registrar el cambio con un ID `CAM-NNN` en [cambios](seguimiento/cambios.md). No incluir secretos, credenciales, datos de facturación privados o transcripciones completas de chats en los registros.

## Comprobación documental

Ejecutar `python3 backend/scripts/check_docs.py` desde la raíz. Comprueba enlaces locales y accesibilidad de todos los Markdown desde este índice, incluidos los ADR enlazados en su propio índice. No valida URLs externas, renderizado, anclas ni requisitos de la app.

Ejecutar además `python3 backend/scripts/check_sdd.py` para estructura y trazabilidad SDD; sus regresiones se ejecutan con `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`. Límites y comandos enfocados: [SDD](metodo/SDD.md).
