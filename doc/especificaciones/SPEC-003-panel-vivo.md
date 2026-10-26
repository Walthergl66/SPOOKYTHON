# SPEC-003 — Panel de observación

ID: SPEC-003
Estado: lista
Requisitos: PRD-04, PRD-06, TRD-05, TRD-06, TRD-07, TRD-09
Tareas: P0-04, P4-01, P4-02
Pruebas: T-04, T-15, T-16, T-19
Cambio: CAM-032
Evidencia: pruebas locales descritas abajo; criterios de panel integral aún no verificados.

## Objetivo y alcance

Hacer comprensible la partida en vivo sin capacidad de alterar el mundo para espectadores. Fuentes: [espectador](../flujos/espectador.md), [eventos](../contratos/eventos.md), [frontend](../modulos/frontend.md). No requiere controles administrativos web ni un diseño visual no aprobado.

P4-01 verificado en CAM-031 para el alcance de mapa, capas observables, ruta Dijkstra seleccionable y métricas. P4-02 implementado/verificado localmente en CAM-032 con snapshot inicial y por versión, heartbeat, rechazo cross-origin y reconexión a la versión vigente. La SPEC permanece `lista`: el juego aún no está conectado y falta completar accesibilidad/producto y validación desplegada.

El panel de esta SPEC sigue siendo de solo lectura. Los controles de inicio/pausa/reinicio de la demo sintética local se especifican por separado en [SPEC-007](SPEC-007-panel-operador-local.md) y no cambian permisos de espectadores.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-003-01 | Mapa representa entidades visibles, rutas previstas, refugios, cierres y área de hordas; no filtra dormidos o secretos. | T-04, T-16 |
| CA-003-02 | Cada turno confirmado actualiza posiciones y fase; desconexión queda visible y reconexión recupera snapshot sin huecos o datos de otra partida. | T-15 — verificado localmente por CAM-032; despliegue/recovery multi-proceso no cubiertos. |
| CA-003-03 | Panel distingue modo y métricas automáticas/humanas; espectador no inicia, mueve o termina partidas. | T-16 |
| CA-003-04 | Selección y controles permitidos funcionan con teclado, foco visible y señales distintas del color; sin animación obligatoria para entender estado. | T-19 |

## Plan y verificación

P0-04 crea base compilable; P4-01 representa mapa/proyección; P4-02 sincroniza/reconecta con snapshots completos. `test_panel.py` comprueba snapshot inicial, cambio de versión/fase, cambio de partida, heartbeat, rechazo de origen y reanudación desde una secuencia posterior. `npm run build` comprueba el cliente; el navegador local mostró `EN VIVO` a través de Vite/Uvicorn. No se simularon caída de proceso o despliegue. El mapa de simulación no depende de tiles en vivo. Faltan auditoría WCAG, juego real y verificación integral de CA-003-01/03/04; no cerrar la SPEC completa.
