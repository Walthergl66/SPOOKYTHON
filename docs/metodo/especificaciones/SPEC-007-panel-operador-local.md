# SPEC-007 — Panel de operación local del simulador

ID: SPEC-007
Estado: en-revision
Requisitos: PRD-02, PRD-06, TRD-06, TRD-07, TRD-17
Tareas: P4-03
Pruebas: T-26, T-37, T-41, T-43, T-44, T-51
Cambio: CAM-100
Evidencia: ../../calidad/resultados/incidentes-siempre-activos-cam081.md

## Objetivo y alcance

Origen: solicitud del usuario de reparar el inicio del simulador desde el frontend y acercar su jerarquía visual al tablero de referencia. La SPEC-003 continúa siendo la fuente para el panel público de solo lectura. Esta especificación agrega controles de operador para una demo sintética en desarrollo local, protegidos por opt-in de proceso, conexión loopback y validación de origen.

El panel permite iniciar la demo libre mediante un flujo de dos pasos: selección de cuatro puntos seguros, luego conteos de 1–200 habitantes y zombies antes de crear el mundo. La velocidad se fija en 4× y no se ofrece como opción. El escenario mixto, composición de amenazas y posiciones siguen usando generación sintética aleatoria; el servidor conserva autoridad del turno y publica snapshots por el canal existente. Por defecto el tablero usa el fixture parcial de Manta; puede sobreescribirse con `NAVIRA_DEMO_MAP`. El mapa permanece en el centro; la ficha del habitante seleccionado está a la izquierda, y métricas, refugios representados y secuencia de snapshots a la derecha. Las métricas no disponibles se muestran vacías, nunca se inventan. El fixture y las zonas de tsunami no acreditan seguridad sísmica ni sirven como guía de emergencia.

Quedan fuera: control administrativo público, autenticación productiva de operador, mapa oficial para emergencia, persistencia durable, multi-worker, reglas oficiales adicionales y cambios al contrato `POST /paso`.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-007-01 | Sin opt-in local las rutas de control no se exponen; con opt-in solo aceptan loopback y POST same-origin. | T-26 |
| CA-007-02 | Iniciar crea partida simulador con escenario, población y semilla solicitada; el panel HTTP/WebSocket y motor consultan la misma partida activa. | T-26 |
| CA-007-03 | Pausa impide iniciar turnos adicionales; continuar y reiniciar tienen controles separados. El factor local puede acortar la cadencia nominal de dos segundos, pero las rondas siguen ejecutándose secuencialmente sin omisiones. | T-26, T-41 |
| CA-007-04 | La UI permite operar la demo, adapta sus paneles al ancho de pantalla, representa datos reales y presenta errores de conexión/configuración con instrucciones. | T-26 |
| CA-007-05 | La demo inicia en intensidad media si no se especifica dificultad; el operador puede elegir intensidad, mientras los incidentes viales permanecen siempre activos y no aparecen como control en el menú. | T-37, T-43 |
| CA-007-06 | La demo local inicia en 4× (objetivo 0,5 s); la animación ocupa al menos esa cadencia y se adapta al turno local observado, conserva movimientos confirmados entre snapshots intermedios y respeta movimiento reducido. 1×/2×/4× solo ajusta reloj y presentación locales. | T-41 |
| CA-007-07 | Inicio y reinicio crean incidentes viales aunque reciban el campo legado `eventosCiudad: false`; el cliente actual omite ese campo y el menú no permite desactivarlos. | T-43 |
| CA-007-08 | Cada partida local sortea entre 1 y 10 cierres, y el tablero alerta al aplicarse, marca el punto y actualiza las rutas sin mostrar eventos futuros. | T-44 |
| CA-007-09 | Sin partida, la vista de Simulador muestra solo la acción «Iniciar simulación». Al activarla abre el paso de refugios; solo después de asignar los cuatro puntos seguros permite pasar a habitantes/zombies y comenzar. | T-51 |
| CA-007-10 | El operador puede definir conteos enteros de 1–200 habitantes y zombies; la partida respeta el conteo de zombies configurado en el mundo. La cadencia local es fija en 4× y la UI no ofrece selector de velocidad. | T-51 |

## Plan, módulos y verificación

Tarea nueva P4-03: ensamblar control local, runner de simulador, rutas same-origin, controles de configuración y tablero visual. CAM-050 cubre el panel y control inicial; CAM-063 fija intensidad media como valor inicial según comparación documentada, manteniendo los controles. Módulos propietarios: [backend](../../arquitectura/modulos/backend.md), [frontend](../../arquitectura/modulos/frontend.md), [API](../../arquitectura/contratos/api.md), [arquitectura](../../arquitectura/arquitectura.md) y [seguridad](../../operacion/seguridad.md). Ver también [evidencia original de CAM-050](../../calidad/resultados/panel-operador-local-cam050.md).

T-26 cubre rutas locales, opt-in, creación de partida, snapshots, pausa y validación de entrada. T-41 cubre duración/interpolación y cadencia 4× fija de la demo. T-43 verifica el campo legado falso en inicio/reinicio y que la solicitud frontend no envíe una opción de incidentes. T-44 comprueba cierres, aplicación y marcador. T-51 cubre el orden del asistente, el contrato de conteos y la cantidad generada. `frontend/npm run build` valida compilación/TypeScript. La suite no prueba despliegue, seguridad productiva, duración de cinco minutos o rendimiento de AWS. Si el cálculo de una ronda tarda más que el periodo objetivo, el reloj la completa y continúa sin descartar turnos; 4× es una cadencia objetivo, no una garantía de rendimiento.

Límite operativo: el mundo, el reloj y el administrador local viven en memoria del proceso. Al reiniciarlo la partida se pierde. No definir `NAVIRA_LOCAL_DEMO_CONTROL=1` en un despliegue.
