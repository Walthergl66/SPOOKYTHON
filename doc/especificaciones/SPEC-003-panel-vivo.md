# SPEC-003 — Panel de observación

ID: SPEC-003
Estado: lista
Requisitos: PRD-04, PRD-06, TRD-05, TRD-06, TRD-07, TRD-09
Tareas: P0-04, P4-01, P4-02
Pruebas: T-04, T-15, T-16, T-19
Cambio: pendiente
Evidencia: pendiente

## Objetivo y alcance

Hacer comprensible la partida en vivo sin capacidad de alterar el mundo para espectadores. Fuentes: [espectador](../flujos/espectador.md), [eventos](../contratos/eventos.md), [frontend](../modulos/frontend.md). No requiere controles administrativos web ni un diseño visual no aprobado.

P4-01 verificado en CAM-031 para el alcance de mapa, capas observables, ruta Dijkstra seleccionable y métricas con consulta manual. CA-003-02 y sincronización/frescura quedan en P4-02; esta SPEC permanece lista y no se declara verificada integralmente.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-003-01 | Mapa representa entidades visibles, rutas previstas, refugios, cierres y área de hordas; no filtra dormidos o secretos. | T-04, T-16 |
| CA-003-02 | Cada turno confirmado actualiza posiciones y fase; desconexión queda visible y reconexión recupera snapshot sin huecos o datos de otra partida. | T-15 |
| CA-003-03 | Panel distingue modo y métricas automáticas/humanas; espectador no inicia, mueve o termina partidas. | T-16 |
| CA-003-04 | Selección y controles permitidos funcionan con teclado, foco visible y señales distintas del color; sin animación obligatoria para entender estado. | T-19 |

## Plan y verificación

P0-04 crea base compilable; P4-01 representa mapa/proyección; P4-02 sincroniza/reconecta. Separar estado de servidor y selección local. Probar eventos duplicados, salto de secuencia, falta de partida y caída de tiles. El mapa de simulación no depende de tiles en vivo. Validar ausencia de credenciales en bundle y respuestas; no hay resultados actuales.
