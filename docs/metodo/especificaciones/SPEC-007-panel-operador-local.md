# SPEC-007 — Panel de operación local del simulador

ID: SPEC-007
Estado: verificada
Requisitos: PRD-06, TRD-06, TRD-07
Tareas: P4-03
Pruebas: T-26, T-37
Cambio: CAM-063
Evidencia: ../../calidad/resultados/default-media-cam063.md

## Objetivo y alcance

Origen: solicitud del usuario de reparar el inicio del simulador desde el frontend y acercar su jerarquía visual al tablero de referencia. La SPEC-003 continúa siendo la fuente para el panel público de solo lectura. Esta especificación agrega controles de operador para una demo sintética en desarrollo local, protegidos por opt-in de proceso, conexión loopback y validación de origen.

El panel permite configurar escenario/población y comenzar, pausar, continuar o reiniciar una partida automática local. El backend conserva autoridad del turno y publica snapshots por el canal existente. Por defecto el tablero usa el fixture parcial de Manta; puede sobreescribirse con `NAVIRA_DEMO_MAP`. El mapa permanece en el centro; la configuración está a la izquierda y métricas, refugios representados y secuencia de snapshots a la derecha. Las métricas no disponibles se muestran vacías, nunca se inventan. El fixture y las zonas de tsunami no acreditan seguridad sísmica ni sirven como guía de emergencia.

Quedan fuera: control administrativo público, autenticación productiva de operador, mapa oficial para emergencia, persistencia durable, multi-worker, reglas oficiales adicionales y cambios al contrato `POST /paso`.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-007-01 | Sin opt-in local las rutas de control no se exponen; con opt-in solo aceptan loopback y POST same-origin. | T-26 |
| CA-007-02 | Iniciar crea partida simulador con escenario, población y semilla solicitada; el panel HTTP/WebSocket y motor consultan la misma partida activa. | T-26 |
| CA-007-03 | Pausa impide iniciar turnos adicionales; continuar y reiniciar tienen controles separados y el reloj conserva cadencia monotónica nominal de dos segundos. | T-26 |
| CA-007-04 | La UI permite operar la demo, adapta sus paneles al ancho de pantalla, representa datos reales y presenta errores de conexión/configuración con instrucciones. | T-26 |
| CA-007-05 | La demo inicia en intensidad media si no se especifica dificultad; el operador conserva selección explícita de intensidad e incidentes. | T-37 |

## Plan, módulos y verificación

Tarea nueva P4-03: ensamblar control local, runner de simulador, rutas same-origin, controles de configuración y tablero visual. CAM-050 cubre el panel y control inicial; CAM-063 fija intensidad media como valor inicial según comparación documentada, manteniendo los controles. Módulos propietarios: [backend](../../arquitectura/modulos/backend.md), [frontend](../../arquitectura/modulos/frontend.md), [API](../../arquitectura/contratos/api.md), [arquitectura](../../arquitectura/arquitectura.md) y [seguridad](../../operacion/seguridad.md). Ver también [evidencia original de CAM-050](../../calidad/resultados/panel-operador-local-cam050.md).

T-26 cubre rutas locales, opt-in, creación de partida, snapshots, pausa y validación de entrada. `frontend/npm run build` valida compilación/TypeScript; el flujo de control se comprueba con pruebas API. La suite no prueba despliegue, seguridad productiva, duración de cinco minutos o rendimiento de AWS.

Límite operativo: el mundo, el reloj y el administrador local viven en memoria del proceso. Al reiniciarlo la partida se pierde. No definir `NAVIRA_LOCAL_DEMO_CONTROL=1` en un despliegue.
