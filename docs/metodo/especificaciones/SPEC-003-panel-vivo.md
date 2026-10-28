# SPEC-003 — Panel de observación

ID: SPEC-003
Estado: lista
Requisitos: PRD-04, PRD-06, PRD-14, TRD-05, TRD-06, TRD-07, TRD-09, TRD-20
Tareas: P0-04, P4-01, P4-02
Pruebas: T-04, T-15, T-16, T-19, T-41, T-44, T-45, T-65
Cambio: CAM-143
Evidencia: pruebas locales descritas abajo; criterios de panel integral aún no verificados.

## Objetivo y alcance

Hacer comprensible la partida en vivo sin capacidad de alterar el mundo para espectadores. Fuentes: [espectador](../../dominio/flujos/espectador.md), [eventos](../../arquitectura/contratos/eventos.md), [frontend](../../arquitectura/modulos/frontend.md). No requiere controles administrativos web ni un diseño visual no aprobado.

P4-01 verificado en CAM-031 para el alcance de mapa, capas observables, ruta seleccionable y métricas. CAM-083 verifica en navegador la selección por marcador y el detalle de la ruta vigente. P4-02 implementado/verificado localmente en CAM-032 con snapshot inicial y por versión, heartbeat, rechazo cross-origin y reconexión a la versión vigente. La SPEC permanece `lista`: faltan criterios integrales de accesibilidad/producto y validación desplegada.

El panel de esta SPEC sigue siendo de solo lectura. Los controles de inicio/pausa/reinicio de la demo sintética local se especifican por separado en [SPEC-007](SPEC-007-panel-operador-local.md) y no cambian permisos de espectadores.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-003-01 | Mapa representa entidades visibles, rutas previstas, refugios, cierres y área de hordas; no filtra dormidos o secretos. | T-04, T-16 |
| CA-003-02 | Cada turno confirmado actualiza posiciones y fase; una transición animada continúa durante snapshots intermedios sin movimientos nuevos y termina en la posición confirmada. Desconexión queda visible y reconexión recupera snapshot sin huecos o datos de otra partida. Un socket abierto también sigue el contexto cuando el control local inicia otro run. | T-15 y T-41 — CAM-032/052/079; despliegue/recovery multi-proceso no cubiertos. |
| CA-003-03 | Panel distingue modo y métricas automáticas/humanas; espectador no inicia, mueve o termina partidas. | T-16 |
| CA-003-04 | Selección y controles permitidos funcionan con teclado, foco visible y señales distintas del color; sin animación obligatoria para entender estado. | T-19 |
| CA-003-05 | Al confirmarse un incidente, el mapa avisa con turno/causa y publica un marcador amarillo parpadeante en el segmento cerrado. La alerta desaparece sin borrar el marcador; con movimiento reducido, el marcador se mantiene visible sin parpadeo. | T-44 |
| CA-003-06 | Al seleccionar un habitante desde su marcador, la ficha del habitante y su ruta recomendada del snapshot vigente aparece en el panel lateral izquierdo; incluye estado, nodo actual, siguiente paso y destino. La lista accesible también permite elegirlo; la selección no modifica el mundo ni presenta una ruta obsoleta como confirmada. | T-45 |
| CA-003-07 | La ficha muestra el perfil ficticio del habitante seleccionado (nombre, edad, ocupación y descripción) cuando existe. El contrato se valida en el borde; perfiles ausentes de snapshots legados no rompen el panel. La selección solo afecta presentación y nunca se incorpora a la lógica de decisión. | T-65 |

## Plan y verificación

P0-04 crea base compilable; P4-01 representa mapa/proyección; P4-02 sincroniza/reconecta con snapshots completos. `test_panel.py` comprueba snapshot inicial, cambio de versión/fase, cambio de partida, heartbeat, rechazo de origen y reanudación desde una secuencia posterior. `npm run build` comprueba el cliente; el navegador local mostró `EN VIVO` a través de Vite/Uvicorn. No se simularon caída de proceso o despliegue. El mapa de simulación no depende de tiles en vivo. CAM-082 añade coordenadas de segmentos cerrados a la proyección observable; marcador y alerta se derivan solo de incidentes aplicados, y las recomendaciones nuevas ya usan el mismo snapshot con el cierre. Faltan auditoría WCAG, juego real y verificación integral de CA-003-01/03/04; no cerrar la SPEC completa.

CAM-083/T-45 prueba la derivación del detalle del habitante y el clic en marcador; CAM-085 reubica esa ficha al panel lateral izquierdo. CAM-093 añade `GET /panel/ruta/{id}` para calcular una ruta individual fuera de decisiones en el modo automático y la integra con la ficha/capa del mapa. `prefers-reduced-motion` sigue aplicando a animaciones cartográficas; la lista alternativa conserva selección sin requerir precisión de clic. CAM-093 prueba parseo, endpoint y proyección; la inspección visual interactiva tras reiniciar el frontend sigue pendiente. La SPEC no queda verificada integralmente.

CAM-143 amplía el snapshot de sobrevivientes con `perfilNarrativo` opcional validado por backend y frontend. `SurvivorRoutePanel` presenta la identidad narrativa solo para la persona seleccionada. La narración no afecta rutas. Build actualizado; T-65 de comportamiento y recorrido visual quedan pendientes de ejecución.
