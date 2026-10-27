# Módulos frontend y estados de interfaz

Estado: base React + TypeScript + Vite, panel en vivo y tablero de control local implementados parcialmente en `frontend/`. La UI consume el panel HTTP y snapshots públicos de `WS /ws/panel`; CAM-051 reemplaza el SVG por MapLibre GL JS con cartografía vectorial OpenFreeMap/OSM, edificios extruidos cuando hay altura, cámara 2D/3D y capas de snapshot. CAM-038 agrega controles humanos para `POST /juego/unirse` y `POST /juego/accion`; CAM-040 ensambla el backend en modo demo local y el proxy Vite reenvía `/juego`; CAM-041 muestra el restante informado por servidor. CAM-050 agrega un tablero y operaciones locales para demos; CAM-057 permite elegir intensidad sintética e incidentes viales, y muestra estos últimos solo tras su aplicación; no son controles públicos de operador. El mundo conserva autoridad de modo y auditoría T-19 sigue parcial.

| Área | Responsabilidad | Estado que le corresponde |
|---|---|---|
| `app/` | Entrada, rutas, proveedores y selector de modo | Vista actual y navegación. |
| `features/simulation/` | Panel global, rondas y métricas | Proyección automática y filtros. |
| `features/game/` | Personaje, vecinos, acciones, radio y resultado | Intención local y órdenes confirmadas. |
| `features/map/` | Cartografía externa MapLibre y capas GeoJSON de snapshots | Instancia visual, cámara 2D/3D y selección de ruta. |
| `features/session/` | Sesión temporal y recuperación | Identidad permitida, sin secretos de servicio. |
| `domain/` | Tipos, parsers y reglas puras (`panel`, `game`, `simulator`) con pruebas vitest | Datos validados, sin red. |
| `infrastructure/http/` | Única frontera HTTP (`health`, `panel`, `game`, `simulator`) y errores tipados `GameApiError`/`SimulatorApiError` | Solicitudes y respuestas. |
| `infrastructure/realtime/` | WebSocket, secuencia, reconexión y sincronización | Conectado/desconectado/recuperando. |
| `shared/ui/` | Botones, alertas, contadores y accesibilidad | Estados visuales reutilizables. |

## Estructura implementada en P0-04

- `frontend/src/app/`: composición de la pantalla inicial y selección local entre simulador y juego.
- `frontend/src/features/mode/`: tarjetas accesibles de modo; la selección solo altera la vista previa.
- `frontend/src/shared/ui/`: marca vectorial reutilizable.
- `frontend/src/domain/panel.ts` y `frontend/src/infrastructure/http/panel.ts`: tipos y validación runtime de esquema/mapVersion, y cliente HTTP GET (CAM-068).
- `frontend/src/infrastructure/http/health.ts`: `checkHealth` sobre `/salud`.
- `frontend/src/application/ports.ts`, `usePanel.ts` y `useSimulator.ts`: puertos y hooks que orquestan panel y simulador; `App.tsx` los compone con puertos definidos como constantes de módulo. `SimulatorUnavailableError` traduce el 404. Helpers puros en `domain/panel.ts` (`nextPanelLog`, `classifyCursor`, `pickMap`). Sin pruebas unitarias de hooks (CAM-070).
- `frontend/src/infrastructure/realtime/panel.ts`: WebSocket de solo lectura, validación de sobres, cursor por partida, estado live/stale y reconexión exponencial.
- `frontend/src/features/map/`: MapLibre con estilo vectorial externo, extrusión de huellas con altura disponible y capas de calles, cierres, rutas, refugios, sobrevivientes y zombies visibles del snapshot. Encuadra la caja jugable documentada de Manta, limita allí el pan/zoom y enmascara la cartografía exterior; no la presenta como límite administrativo. Anima transiciones entre nodos únicamente cuando llegan snapshots confirmados. Los datos de Navira no se envían al proveedor de tiles.
- `frontend/src/features/game/GameControls.tsx`: presentación de la unión, el estado propio y los controles de orden accesibles por teclado/mouse, deshabilitados en fase incorrecta o al perder frescura del panel. Importa el tipo `GameSessionView` desde `application` (`import type`, observación aceptada).
- `frontend/src/domain/game.ts`: validación runtime de sesión y acuse, funciones puras (`activeGameState`, `findPlayer`, `legalMoves`, `radioSuggestion`, `buildGameOrder`, `remainingMs`, `createActionId`, `classifyGameError`) y errores de dominio (`GameSessionMissingError`, `GameSessionExpiredError`, `GameOrderRejectedError`). `infrastructure/http/game.ts` es el cliente same-origin y traduce el status con `httpError`; la cookie HttpOnly no se expone a JavaScript (F4, CAM-072).
- `frontend/src/application/ports.ts` añade `GamePort`; `application/useGameSession.ts` contiene la red, la sesión, la recuperación y el temporizador de 100 ms. El hook vive en `App.tsx` para que la sesión sobreviva al cambio de modo; `App` se re-renderiza con el temporizador mientras hay partida en modo juego. Se descarta la sesión si cambia `runId` o llega 403, y se limpian `pendingOrder` y `activity` al salir de la partida (CAM-072).
- `frontend/src/features/map/mapFeatures.ts`: funciones puras de proyección a GeoJSON (`createSimulationFeatures`, `createActorFeatures`, `createMovementAnimations`, `positionAlongPath`, `emptyCollection`) y tipos `Position`, `FeatureCollection`, `AnimatedMovement`, con `mapFeatures.test.ts` (9 pruebas). Está en `features/map` y no en `domain/` por ser proyección a GeoJSON; `CityMap.tsx` solo dibuja (F5, CAM-072).
- `frontend/src/domain/simulator.ts` y `frontend/src/infrastructure/http/simulator.ts`: cliente de estado e inicio/pausa/continuación/reinicio de demo local; no transmite API keys.
- `frontend/src/styles.css`: tokens visuales, layout responsivo y preferencia de movimiento reducido.
- `frontend/README.md`: inicio local y límites de esta base.

P4-01 permite consultas iniciales/manuales a `GET /panel/estado` y `GET /panel/mapa`. P4-02 añade snapshots completos por WebSocket, secuencia derivada de versión, heartbeat, aviso de desconexión/desactualización y reconexión. El backend omite zombies dormidos y la UI muestra modo real, métricas, grafo, refugios, cierres, hordas, movimientos confirmados y ruta prevista del planificador activo en fase de decisiones (CAM-058). El cliente acepta saltos porque cada snapshot reemplaza el estado completo y descarta repeticiones/estados antiguos de la misma partida. El canal depende del mismo proceso y almacenamiento en memoria; no hay replay durable, control multi-worker o despliegue. El mapa parcial de Manta no certifica seguridad sísmica.

CAM-050 sustituye la portada de vista previa por un tablero inspirado en el mapa central y paneles de operación de la referencia. El selector mantiene dos modos de vista; el simulador se inicia explícitamente cuando `/demo/simulador` está habilitado. Escenario, población, mapa, refugios, turno y métricas vienen de configuración o snapshot; lo no disponible aparece vacío. La secuencia lateral describe snapshots recibidos, no un historial completo de eventos. CAM-052 separa la fuente GeoJSON de actores para interpolar su movimiento durante 1,6 s entre snapshots, ajusta la cámara al fixture y conserva la regla de que una animación no confirma una acción. CAM-053 limita la vista al recorte cartográfico declarado en `docs/dominio/mapa-manta.md`, pinta un fondo opaco fuera de él y fija el zoom mínimo a la vista general del área. CAM-054 amplió la ventana visual unos 1,7 km; CAM-055 la llevó a ~50 km por lado y CAM-056 la redujo a ~15 km por lado del recorte OSM. CAM-073 agrega «Todo Manta» y «Ver partida» y amplía el límite al mapa OSM de juego; caja con margen, no polígono municipal.

CAM-038 conecta la vista seleccionada «Jugar» a los contratos de sesión/orden: la cookie queda fuera de JS y los movimientos posibles salen de calles dirigidas abiertas no bloqueadas por horda. CAM-040 añade instancia sintética local con ciclo de 2 s y cierre servidor de 1,7 s; CAM-041 muestra un contador local basado en `decisionRestanteMs`. CAM-042 presenta la ruta prevista del servidor como sugerencia opcional de radio, y envía solo tras una acción explícita del usuario. CAM-043 recupera una sesión existente después de recarga; CAM-045 agrega enlace de salto, foco visible del selector y anuncios del reloj limitados al umbral. CAM-046 comunica el estado 410 de sesión vencida, borra la sesión del estado UI y explica que el personaje permanece reservado. CAM-047 observa que Tab/Enter/Space alcanzan el contenido y alternan el modo; no completa el recorrido de órdenes. Se etiqueta riesgo zombie y el acuse no se presenta como movimiento confirmado. Falta auditoría T-19 completa y recorrido con tecnologías de asistencia.

## Comprobación local

Desde `frontend/`, `npm ci` instala el lockfile y `npm test` ejecuta vitest (59 pruebas en 6 archivos: dominio, infraestructura de `game` y `mapFeatures`; CAM-068, CAM-070 y CAM-072) y `npm run build` valida TypeScript y produce el bundle Vite. En desarrollo, Vite reenvía `/panel`, `/juego` y `/ws` a `127.0.0.1:8000`. `.github/workflows/ci.yml` define las verificaciones backend/frontend en push a `master` y pull request; el workflow remoto no se afirma como ejecutado.

## Reglas

- El servidor manda sobre posición, turno, mordida y propiedad; una animación no confirma un movimiento.
- Separar estado remoto de selección local. No copiar la misma partida en varios estados independientes sin sincronización.
- Validar respuestas en la frontera. Los componentes reciben tipos del producto, no JSON sin comprobar.
- Orden humana: `sin_orden → enviando → recibida → aplicada`; una sugerencia de radio no cambia esa cadena.
- Reconexión: mostrar datos desactualizados, recuperar instantánea y después consumir eventos nuevos.
- Botones por vecino con etiquetas, foco visible y acceso por teclado; no depender de hover ni de color solamente.
- No bloquear el hilo principal reconstruyendo capas completas por turno. Respetar preferencia de movimiento reducido.
- Rutas previstas y peligros estimados deben distinguirse de posiciones confirmadas.

Los paneles consumen solo la proyección observable. No incluir API keys de servicio, credenciales administrativas o dormidos ocultos en bundles o mensajes. La capa base requiere internet y solicita tiles del área visible a OpenFreeMap; la instancia pública no ofrece SLA. La geometría de rutas Navira une coordenadas de intersecciones y puede diferir de la curva real de la calle. Véanse [SPEC-008](../../metodo/especificaciones/SPEC-008-mapa-cartografico-3d.md) y [ADR-016](../decisiones/0016-mapa-maplibre-openfreemap.md).


CAM-073: `features/map/mapArea.ts` calcula caja del mapa desde nodos; `CityMap` indexa coordenadas una vez por versión. CAM-074/075 establecieron una vista completa con margen de 5 km y resaltado de agua. CAM-076 añade la ventana urbana estimada. CAM-077 comparte `limitesJugables` desde el contrato de candidatos: el selector encuadra esa caja, dibuja solo nodos/calles interiores y bloquea clics externos; el backend aplica la misma caja al grafo de cada partida. El fixture fuente ampliado permanece disponible. T-27 cubre cartografía y T-39 selector/límite. Los tiles siguen siendo dependencia externa.
