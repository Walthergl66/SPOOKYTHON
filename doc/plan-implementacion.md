# Plan de implementación vigente

Estado: implementación secuencial en `master`, con commits individuales por fase según instrucción del usuario. P5-04 tiene integración local parcial (CAM-039..046); siguen persistencia/reinicio, recorrido integral accesible y seguridad productiva. Última revisión: 2026-10-26. Fuentes: [contexto](contexto.md), [reto](referencias/reto-original.md) y [decisiones](decisiones/README.md). El [plan previo](referencias/plan-previo.md) es histórico; los documentos especializados actuales son la fuente de cada contrato o regla.

Nombre vigente: **Navira**. Al crear el backend usar la raíz propuesta `src/navira/`; la ruta del plan histórico no es una instrucción actual de nomenclatura. Las tareas funcionales y sus IDs se mantienen.

## Orden y dependencias

```mermaid
flowchart LR
    P0[Base y contratos] --> P1[Grafo y simulador]
    P1 --> P2[Ronda completa con Dijkstra]
    P2 --> P3[Predicción medible]
    P0 --> P4[Panel vivo]
    P2 --> P4B[Control humano]
    P4 --> P4B
    P3 --> P5[Pruebas y AWS]
    P4B --> P5
    P5 --> P6[Entrega]
```

Configurar Budget en cuanto se disponga de acceso AWS; desplegar temprano, sin esperar a terminar todos los algoritmos. Los responsables indicados son funciones de equipo, no agentes creados automáticamente.

## Preparación metodológica

Intervención documental solicitada: [SPEC-006](especificaciones/SPEC-006-metodologia.md). No completa las fases de aplicación P0–P6.

| ID | Entregable | Estado | Evidencia |
|---|---|---|---|
| M0-01 | Auditar documentos, herramientas y alcance real | Verificado | CAM-004; lectura de repositorio y fuentes. |
| M0-02 | PRD/TRD, modelo OO + DDD, SDD, SPEC y plantillas | Verificado | Documentos y trazabilidad comprobados; SPEC-006. |
| M0-03 | Validadores y regresiones de trazabilidad | Verificado | Ocho regresiones correctas y validadores sin errores. |
| M0-04 | Validación, evidencia y transferencia | Verificado | CAM-004, reporte de SPEC-006 y estado actualizado. |

Elegir especificación y criterios antes de cada tarea; referencias de producto/técnicas en [trazabilidad](trazabilidad.md). La autorización actual cubre metodología; las funcionalidades siguen el alcance de la tarea de construcción que se solicite.

## Tareas

Estados permitidos: pendiente, en curso, verificado, bloqueado o descartado con motivo. «Verificado» exige evidencia; al interrumpir trabajo, registrar el estado real y el siguiente paso en [estado actual](estado-actual.md).

| ID | Entregable y responsable | Depende de | Aceptación | Estado |
|---|---|---|---|---|
| P0-01 | Base Python/FastAPI y configuración — backend | Lectura de `AGENTS.md` y `doc/` | Arranque local reproducible, secretos ficticios en ejemplos. | Verificado |
| P0-02 | Esquemas y fixtures — backend/dominio | P0-01 | `/paso` conserva contrato; mapa pequeño y errores definidos. | En curso |
| P0-03 | Budget, permisos y región — operación | Acceso AWS autorizado | Alerta real y evidencia sin datos sensibles. | Pendiente |
| P0-04 | CI y frontend mínimo — integración | P0-01 | Workflow backend/frontend configurado; suite Python y build frontend ejecutados localmente. Workflow remoto aún requiere publicación. | Verificado — CAM-030 |
| P0-05 | Primer despliegue — operación | P0-03 y base mínima | URL pública de salud comprobada. | Pendiente |
| P1-01 | Grafo Manta y refugios — dominio | P0-02 | Unas 300 intersecciones, barrios conectados, distancias y direcciones válidas. Fixture 300 nodos con cuatro anclas tsunami generado; falta validar cobertura representativa y confirmar calles/amenazas. | En curso |
| P1-02 | Entidades, modos e intenciones — dominio | P0-02 | Un mundo y un resolutor para humano/automático. | En curso |
| P1-03 | Zombies y mordidas — simulación | P1-02 | T-01 a T-06 cubiertas, visibilidad validada y supuestos identificados. | En curso |
| P1-04 | Reloj, eventos y snapshots — simulación | P1-03 | Turnos versionados; bootstrap demo, caso de uso y CLI local completan rondas en memoria. Reloj continuo/durable pendientes. | En curso |
| P1-05 | Escenarios estocásticos — simulación | P1-01 y P1-04 | Demo genera semilla nueva si se omite, muestrea posiciones iniciales/fase de caminantes; replay multi-turno y posible divergencia de rutas entre semillas se prueban. Cohortes sintéticas 20/80/200 recorren tres turnos en el fixture Manta (CAM-025). Parcial: composición oficial P-09, reglas/eventos estocásticos, movimiento de horda P-07, persistencia/replay integral y evaluación HTTP/carga pendientes. | En curso |
| P2-01 | Dijkstra y selección de refugio — rutas | P1-01 | Núcleo genérico considera tipo/distancia, cierres y peligros visibles; falta validar mapa real. | En curso |
| P2-02 | `/paso` y API key — backend | P2-01 y P1-04 | Demo explícita recomienda ruta por HTTP sobre un snapshot activo; mundo oficial, idempotencia durable y operación completa pendientes. | En curso |
| P2-03 | Integración y referencia — integración | P2-02 y P1-05 | Una ronda completa; luego tres rondas y reporte base. CAM-028/029 miden HTTP loopback multi-turno y cadencia de 2 s; CAM-044 solicitó 150 turnos, pero mundo sintético finalizó a los 12/15/13. Faltan cinco minutos por cohorte, parámetros oficiales y entorno remoto. | En curso |
| P3-01 | Búsqueda temporal acotada — rutas | P2-03 (referencia parcial disponible) | Núcleo `(nodo, turnos)` con espera, horizonte configurable, tope de expansiones/tiempo y reporte de medición local; ruta truncada no reemplaza la base. Sin integración HTTP ni predicción. | Verificado — CAM-033 |
| P3-02 | Pronóstico observable — rutas | P3-01 | No conoce dormidos ni fase privada; produce ocupación y supuestos de modelo para el horizonte temporal. El pronóstico actual es exploratorio: caminantes mezclan fases, sobrevivientes de corredor quedan fijos y horda estática es provisional. | Implementado parcialmente — CAM-034; comparación en P3-03 pendiente |
| P3-03 | Selección de política — integración | P3-02 | CAM-035 compara 27 pares sintéticos reproducibles de tres turnos; temporal mejora evacuados en 15/27 y no empeora mordidas en la muestra. Dijkstra permanece activa hasta validar reglas, T-22 ampliada y latencia HTTP/concurrencia. | Evaluado parcialmente — CAM-035; integración y T-22 pendientes |
| P4-01 | Panel y mapa — frontend/backend | P0-04 y contratos | Mapa/snapshot observables, filtro de dormidos, capas, refugios, cierres/hordas, movimientos, métricas por modo, ruta prevista seleccionable y consulta manual. Pruebas API y recorrido visual local; actualización en vivo corresponde a P4-02. | Verificado — CAM-031 |
| P4-02 | WebSocket y recuperación — frontend/backend | P1-04 y P4-01 | Snapshot completo al conectar/cambiar versión, heartbeat y reconexión desde versión vigente; filtra origen ajeno y no cruza runId. Almacenamiento del socket en memoria, sin replay durable/multi-worker. | Verificado — CAM-032 |
| P4B-01 | Sesión y aparición humana — backend | P2-03 | Un propietario, nodo aleatorio elegible y entrada al inicio de turno. CAM-036 implementa sesión local; CAM-043 recupera personaje y posición por cookie tras recarga; CAM-046 aplica TTL deslizante local de 30 min y tombstone para no transferir el personaje. Política productiva, revocación y persistencia durable/reinicio pendientes. | Implementada parcialmente — CAM-046 |
| P4B-02 | Órdenes idempotentes — backend | P4B-01 | `POST /juego/accion` valida sesión, propiedad, modo, fase, turno y topología; el mismo `accionId` devuelve el acuse original y la última orden válida sustituye la anterior. CAM-037 cubre memoria local; reloj/cierre atómico, consumo por coordinador y persistencia durable pendientes. | Implementada parcialmente — CAM-037 |
| P4B-03 | Controles y resultado — frontend | P4-02 y P4B-02 | CAM-038 implementa UI inicial por teclado/mouse y acuse; CAM-041 timer, CAM-042 radio, CAM-043 recuperación local, CAM-045 skip link/foco/anuncio de deadline y CAM-047 recorrido manual parcial de Tab/Enter/Space en selección. Falta probar orden/resultado end-to-end, lector de pantalla y T-19 integral. | Implementada parcialmente — CAM-047 |
| P5-01 | Ráfagas y reloj — integración | P2-03 y política elegida | p95 objetivo ≤150 ms, errores <0,5 %, ciclo dentro de dos segundos. CAM-044 obtiene p95 18,860/58,097/92,060 ms, cero errores y ciclos máximos <481 ms en una pasada local, pero las rondas acaban antes de 150 turnos. Faltan duración sostenida, repeticiones y entorno objetivo. | En curso — CAM-044 parcial |
| P5-02 | Seguridad/red/TLS — operación | P0-05 y contratos finales | Permisos, origen y sesión probados; sin claves maestras en navegador. | Pendiente |
| P5-03 | Tres rondas en AWS — integración | P5-01, P5-02 y panel | Reportes con versión, origen de medición y resultados reales. | Pendiente |
| P5-04 | Juego y recuperación — integración | P4B-03 y P5-02 | T-12 a T-19; una recarga no revive ni duplica control. CAM-039/040 conectan coordinador, deadline de 1,7 s, runner de 2 s y modo sintético opt-in; CAM-041 muestra el tiempo del servidor, CAM-042 agrega radio, CAM-043 recuperación local y CAM-046 caducidad local sin transferir personaje. Persistencia/reinicio, TLS y T-14/T-15/T-19 integral siguen pendientes. | Implementada parcialmente — CAM-046 |
| P6-01 | README y evidencias — integración | Ejecución real | Instalación, API, despliegue y métricas reproducibles. | Pendiente |
| P6-02 | Diagrama/costos/Budget — operación | Recursos reales | SVG/PNG y fuente, cálculo completo y gasto real. | Pendiente |
| P6-03 | Pitch y entrega — equipo | P5-03, P5-04, P6-01, P6-02 | PDF/PPT ≤20 MB, enlaces públicos y entrega anticipada. | Pendiente |

Los objetivos son metas, no garantías ni resultados ya existentes. Detalles de aceptación en [pruebas](pruebas.md). El juego es parte del alcance solicitado; capacidad de refugios y camionetas no están comprometidas todavía.

## Cronograma propuesto

Fechas del reto: entrega miércoles 28-10-2026 a las 10:00, Ecuador continental. Ventanas orientativas heredadas del análisis; al retomarlas, contrastar hora/fecha reales y replanificar lo pendiente sin fingir que el trabajo previsto ya ocurrió.

| Ventana | Objetivo |
|---|---|
| Lunes 26 | Contratos, Budget, base, grafo y primera ronda integrada en AWS. |
| Martes 27, mañana | Reglas completas, tres escenarios, panel y entrada humana mínima. |
| Martes 27, tarde | Predicción, juego integrado, ráfagas y correcciones. |
| Martes 27, noche | Congelar funcionalidades y completar evidencia/documentación. |
| Miércoles 28, 07:30–09:00 | Verificación final y pitch. |
| Miércoles 28, 09:00–09:30 | Enviar y comprobar entrega. |
| Miércoles 28, 09:30–10:00 | Margen de incidencias. |

Equipo orientativo: A dominio/simulador; B rutas/API; C frontend/operación/documentación, con revisión compartida del despliegue. Con dos personas, dividir núcleo y producto/infraestructura. Con una, mantener pasos secuenciales y panel/juego mínimos; reducir primero extras y refinamientos.

## Recortes y bloqueos

- Sin una ronda completa, no empezar camionetas o capacidad.
- Si predicción empeora resultados, conservar política mejor medida y registrar comparación.
- Si CPU/latencia falla, revisar I/O y trabajo repetido, reducir horizonte y después dimensionar.
- Reducir efectos, personalización y ayudas avanzadas del juego antes de sus validaciones de control.
- Dudas externas no bloquean núcleo local; mantener supuestos configurables en [pendientes](pendientes.md).
- No crear Redis, colas, réplicas o nuevas capas sin problema demostrado y decisión registrada.

## Checklist de entrega

- [ ] Repositorio público e historial real de commits.
- [ ] README raíz reproducible con endpoint `/paso`, autenticación y medición.
- [ ] Simulador completo, mapa vivo y tres rondas en AWS.
- [ ] Selector de modos y juego humano mínimo verificado.
- [ ] Métricas del juego separadas de la prueba automática.
- [ ] Arquitectura exportada y fuente en `doc/`.
- [ ] Budget con alerta y evidencia en `doc/evidencias/`.
- [ ] Costo mensual completo y gasto real diferenciados.
- [ ] Supuestos y limitaciones conocidos, sin resultados inventados.
- [ ] Pitch válido, enlaces comprobados y URL disponible hasta la presentación.

El uso de `doc/` difiere de la estructura sugerida `docs/` del reto; el documento admite una estructura sugerida. README y entrega deben enlazar las ubicaciones reales.
