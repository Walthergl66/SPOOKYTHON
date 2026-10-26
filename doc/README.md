# Índice y autoridad de la documentación

Actualizado: 2026-10-26. Documentación canónica: `doc/`, en singular. La antigua ruta `docs/PLAN_IMPLEMENTACION.md` ya no existe en el árbol comprobado; el plan vigente está aquí y el anterior se conserva como referencia histórica.

## Lectura de incorporación

Seguir [AGENTS.md](../AGENTS.md): primero este índice, [contexto](contexto.md), [estado actual](estado-actual.md), [continuidad](continuidad.md), [cambios](cambios.md) y [pendientes](pendientes.md). Después revisar todos los demás `.md` de `doc/`, incluidos subdirectorios, antes de la primera modificación de una tarea. Los históricos y plantillas se reconocen como tales, no como requisitos vigentes. No hay que releer todo antes de cada comando de una misma tarea.

## Mapa de documentos y responsables conceptuales

| Documento | Fuente principal de | Actualizar cuando |
|---|---|---|
| [PRD.md](PRD.md) | Necesidades, alcance e IDs de producto | Cambien objetivos o requisitos de producto. |
| [TRD.md](TRD.md) | IDs y condiciones técnicas verificables | Cambien restricciones o garantías requeridas. |
| [ODDD.md](ODDD.md) | Lenguaje, límites e invariantes OO + DDD | Cambie el modelo del dominio. |
| [SDD.md](SDD.md) | Ciclo Specify/Plan/Implement/Verify/Document | Cambie el procedimiento de desarrollo. |
| [especificaciones/README.md](especificaciones/README.md) | Funcionalidades con criterios CA, tareas y pruebas | Se añada o cambie una funcionalidad. |
| [trazabilidad.md](trazabilidad.md) | Vínculos PRD/TRD → SPEC → tareas/pruebas | Cambien requisitos o referencias. |
| [contexto.md](contexto.md) | Objetivo, alcance y decisiones del usuario | Cambie producto o alcance. |
| [estado-actual.md](estado-actual.md) | Evidencia de lo existente y siguiente acción | Se complete o interrumpa trabajo. |
| [arquitectura.md](arquitectura.md) | Componentes, límites y dependencias | Cambien estructura o comunicaciones. |
| [reglas-juego.md](reglas-juego.md) | Reglas de simulación y supuestos | Se confirme o cambie una regla. |
| [decisiones/0008-simulacion-estocastica-reproducible.md](decisiones/0008-simulacion-estocastica-reproducible.md) | Aleatoriedad del mundo, reproducción y privacidad del generador | Cambien condiciones de estocasticidad o replay. |
| [decisiones/0009-panel-ws-snapshots-completos.md](decisiones/0009-panel-ws-snapshots-completos.md) | Snapshots completos del WebSocket de observación | Cambie el transporte, cursor o recuperación del panel. |
| [decisiones/0010-busqueda-temporal-acotada.md](decisiones/0010-busqueda-temporal-acotada.md) | Prioridad, límite y uso de la ruta temporal experimental | Cambie horizonte, función de costo o integración en política. |
| [decisiones/0011-pronostico-visible-por-escenarios.md](decisiones/0011-pronostico-visible-por-escenarios.md) | Frontera de información y supuestos del pronóstico observable | Cambie inputs, probabilidades/ocupación o reglas modeladas por pronóstico. |
| [decisiones/0012-seleccion-politica-baseline.md](decisiones/0012-seleccion-politica-baseline.md) | Política de rutas activa y evidencia que condiciona su selección | Cambie baseline, evidencia comparativa o criterios para integración temporal. |
| [decisiones/0013-sesion-y-aparicion-humana-local.md](decisiones/0013-sesion-y-aparicion-humana-local.md) | Propiedad de jugador, cookie y ciclo de aparición humana | Cambie sesiones, aparición o límites de seguridad del modo juego. |
| [decisiones/0014-expiracion-local-de-sesion-humana.md](decisiones/0014-expiracion-local-de-sesion-humana.md) | TTL local de sesión humana y propiedad retenida al vencer | Cambie la política de sesión, recuperación o cupo humano. |
| [modos.md](modos.md) | Diferencias entre simulador y juego | Cambie control o experiencia. |
| [flujos/roles.md](flujos/roles.md) | Actores, permisos y responsabilidades | Aparezca un actor o permiso. |
| [flujos/simulador.md](flujos/simulador.md) | Ciclo del turno automático | Cambie secuencia o reloj. |
| [flujos/jugador.md](flujos/jugador.md) | Entrada, órdenes y salida del jugador | Cambie la interacción humana. |
| [flujos/espectador.md](flujos/espectador.md) | Observación y reconexión | Cambie el panel de lectura. |
| [flujos/operador.md](flujos/operador.md) | Inicio, eventos y cierre de partidas | Cambien controles administrativos. |
| [modulos/backend.md](modulos/backend.md) | Ubicación de responsabilidades backend | Se cree o mueva un caso de uso. |
| [modulos/frontend.md](modulos/frontend.md) | Módulos y estados de interfaz | Se cree o mueva una pantalla. Estado del scaffold en `frontend/`; no sustituye los contratos del panel. |
| [especificaciones/SPEC-007-panel-operador-local.md](especificaciones/SPEC-007-panel-operador-local.md) | Criterios del tablero y control local de demo | Cambie el flujo local de operación; no autoriza control administrativo público. |
| [especificaciones/SPEC-008-mapa-cartografico-3d.md](especificaciones/SPEC-008-mapa-cartografico-3d.md) | Criterios del mapa vectorial y vista 3D | Cambie el renderer/cartografía del panel; no convierte el proveedor en motor de simulación. |
| [decisiones/0016-mapa-maplibre-openfreemap.md](decisiones/0016-mapa-maplibre-openfreemap.md) | Renderer MapLibre, proveedor vectorial OpenFreeMap y límites 3D | Cambie el proveedor, estilo, credenciales o forma de renderizar geometría. |
| [contratos/api.md](contratos/api.md) | Contrato HTTP y autenticación | Cambien rutas, cuerpos o errores. Estado y ejemplos de las proyecciones del panel incluyen CAM-031. |
| [contratos/eventos.md](contratos/eventos.md) | Contrato WebSocket y orden de mensajes | Cambien eventos o recuperación. El canal de snapshots del panel se implementa localmente en CAM-032. |
| [datos.md](datos.md) | Entidades, estados e identidad de versiones | Cambie persistencia o proyección. |
| [mapa-manta.md](mapa-manta.md) | Procedencia, alcance y límites del fixture geográfico de Manta | Cambien las fuentes, extensión o metodología del dataset. |
| [algoritmos.md](algoritmos.md) | Planificación y predicción | Cambie la política de rutas. |
| [infraestructura.md](infraestructura.md) | Despliegue y operación AWS | Cambie un recurso o procedimiento. |
| [seguridad.md](seguridad.md) | Autenticación y límites de confianza | Cambien accesos o secretos. |
| [pruebas.md](pruebas.md) | Verificación y métricas | Cambie comportamiento o aceptación. |
| [resultados/carga-local-cam020.md](resultados/carga-local-cam020.md) | Evidencia de ráfagas HTTP locales | Se ejecute una medición local reproducible; no sustituye resultados oficiales. |
| [resultados/simulacion-manta-cam025.md](resultados/simulacion-manta-cam025.md) | Ejecución exploratoria de cohortes sintéticas en el grafo Manta | Cambien configuración/resultados del ensayo; no equivale a evaluación oficial ni seguridad real. |
| [resultados/evaluacion-multi-turno-cam028.md](resultados/evaluacion-multi-turno-cam028.md) | Medición HTTP loopback con avance de turnos y cohortes 20/80/200 | Nueva ejecución multi-turno; evidencia local exploratoria, no sustituye T-11 ni AWS. |
| [resultados/evaluacion-cadencia-cam029.md](resultados/evaluacion-cadencia-cam029.md) | Cadencia objetivo de 2 s para evaluaciones HTTP multi-turno locales | Nueva medición temporizada; evidencia exploratoria, no sustituye T-11 ni AWS. |
| [resultados/evaluacion-p501-cam044.md](resultados/evaluacion-p501-cam044.md) | Medición extendida local por HTTP loopback para cohortes 20/80/200 | Nueva ejecución P5-01; las partidas terminaron antes de 150 turnos, no acredita T-11 ni AWS. |
| [resultados/panel-operador-local-cam050.md](resultados/panel-operador-local-cam050.md) | Evidencia de inicio/pausa manual del panel local y verificaciones de CAM-050 | Cambien el control local o se repita la inspección del tablero; no acredita despliegue productivo ni uso de emergencia. |
| [resultados/mapa-cartografico-3d-cam051.md](resultados/mapa-cartografico-3d-cam051.md) | Evidencia de carga de cartografía, atribución, edificios y alternancia 2D/3D de CAM-051 | Cambien el renderer/proveedor o se repita la inspección; no acredita cobertura completa, SLA ni uso de emergencia. |
| [resultados/movimiento-mapa-cam052.md](resultados/movimiento-mapa-cam052.md) | Evidencia de fichas animadas, cámara encuadrada y sincronización de un nuevo run en CAM-052 | Cambie la transición de actores o el cambio de partida; no acredita reglas oficiales, precisión vial ni uso de emergencia. |
| [resultados/limites-mapa-cam053.md](resultados/limites-mapa-cam053.md) | Evidencia de cámara, pan y máscara exterior limitados al recorte cartográfico de Manta en CAM-053 | Cambie la extensión del fixture o el comportamiento de cámara; no acredita límite administrativo ni cobertura municipal completa. |
| [resultados/busqueda-temporal-cam033.md](resultados/busqueda-temporal-cam033.md) | Tiempo de búsqueda temporal por llamada para cohortes sintéticas 20/80/200 | Nueva versión de algoritmo o ejecución comparativa; no es medición HTTP ni T-22. |
| [resultados/comparacion-rutas-cam035.md](resultados/comparacion-rutas-cam035.md) | Comparación emparejada Dijkstra/temporal en tres turnos locales | Cambien política, semilla, mapa, perfiles o método comparativo. No reemplaza T-22/T-11. |
| [costos.md](costos.md) | Estimación y gasto real | Cambie infraestructura o consumo. |
| [plan-implementacion.md](plan-implementacion.md) | Tareas, dependencias y criterios de salida | Se ajuste o complete una fase. |
| [pendientes.md](pendientes.md) | Dudas, riesgos y confirmaciones | Se descubra o resuelva una incertidumbre. |
| [decisiones/README.md](decisiones/README.md) | Registro e índice de ADR | Cambie una decisión duradera. |
| [cambios.md](cambios.md) | Historial del qué, por qué y validación | Se cierre un cambio significativo. |
| [continuidad.md](continuidad.md) | Protocolo de inicio, cierre y transferencia | Cambie la forma de colaborar. |
| [plantillas/cambio.md](plantillas/cambio.md) | Formato de cambio | Se necesiten campos nuevos. |
| [plantillas/decision.md](plantillas/decision.md) | Formato de ADR | Se necesiten campos nuevos. |
| [plantillas/transferencia.md](plantillas/transferencia.md) | Formato de transferencia | Cambie el protocolo de continuidad. |
| [plantillas/especificacion.md](plantillas/especificacion.md) | Formato de SPEC y criterios CA | Cambie la estructura de especificaciones. |
| [plantillas/plan-cambio.md](plantillas/plan-cambio.md) | Plan proporcional dentro de una tarea/SPEC | Cambie la planificación de cambios. |
| [referencias/reto-original.md](referencias/reto-original.md) | Texto del reto proporcionado por el usuario | Conservar como fuente; añadir aclaraciones aparte. |
| [referencias/plan-previo.md](referencias/plan-previo.md) | Propuesta histórica anterior | No modificar como documento vigente. |
| [referencias/propuesta-sdd.md](referencias/propuesta-sdd.md) | Propuesta aportada por el usuario | Conservar como referencia; adaptación vigente en SDD. |
| [resultados/verificacion-sdd.md](resultados/verificacion-sdd.md) | Evidencia de incorporación metodológica | Conservar resultados de CAM-004; nuevas ejecuciones se registran sin alterar resultados históricos. |

## Estados y resolución de discrepancias

- **Requisito del reto:** consta en el texto proporcionado. Una aclaración posterior debe tener fecha y fuente.
- **Decisión del usuario:** instrucción explícita; registrar su efecto sobre alcance y diseño.
- **Decisión de diseño:** adoptada para implementar, sin afirmar que ya exista código.
- **Supuesto pendiente:** interpretación provisional identificada en `pendientes.md`.
- **Implementado:** existe código; **verificado:** además hay evidencia de ejecución. No son sinónimos.
- **Histórico:** explica cómo se llegó al estado vigente; no lo reemplaza.

Las instrucciones actuales del usuario y las reglas superiores de la sesión prevalecen sobre estos documentos. Para describir implementación real se comprueba el repositorio y la evidencia. Si código y contrato difieren, registrar la discrepancia y resolverla; no declarar correcto el código solo por existir. No sobrescribir un requisito del reto con una suposición sin dejar trazabilidad.

PRD identifica producto, TRD condiciones técnicas y SPEC aceptación por funcionalidad; arquitectura y ODDD definen diseño e invariantes. La jerarquía y resolución de conflictos se detallan en [SDD](SDD.md). Mantener IDs estables y enlaces a fuentes propietarias; ningún archivo nuevo permite alterar requisitos silenciosamente.

Cada asunto tiene una fuente principal en la tabla; los demás documentos enlazan a ella. Al añadir un `.md`, incorporarlo al índice y relacionarlo con el registro de cambio correspondiente. No incluir secretos, credenciales, datos de facturación privados o transcripciones completas de chats en los registros.

## Comprobación documental

Ejecutar `python3 scripts/check_docs.py` desde la raíz. Comprueba enlaces locales y accesibilidad de todos los Markdown desde este índice, incluidos los ADR enlazados en su propio índice. No valida URLs externas, renderizado, anclas ni requisitos de la app. Añadir documentos aquí o en un subíndice pertinente antes de cerrar un cambio.

Ejecutar además `python3 scripts/check_sdd.py` para estructura y trazabilidad SDD; sus regresiones se ejecutan con `python3 -m unittest discover -s tests -p 'test_check_sdd.py'`. Límites y comandos enfocados: [SDD](SDD.md).
