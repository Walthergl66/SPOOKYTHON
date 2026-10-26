# Módulos frontend y estados de interfaz

Estado: base React + TypeScript + Vite y panel manual/en vivo implementados parcialmente en `frontend/`. La UI consume el panel HTTP y snapshots públicos de `WS /ws/panel`; el mapa es SVG sobre el grafo recibido, no Leaflet. CAM-038 agrega una pantalla de control humano que consume `POST /juego/unirse` y `POST /juego/accion`, presenta vecinos dirigidos disponibles, espera y acuse. El selector no inicia una partida; si la instancia no publica un mundo activo en modo juego, la UI explica que no puede entrar. El backend aún no ensambla un ciclo jugable.

| Área | Responsabilidad | Estado que le corresponde |
|---|---|---|
| `app/` | Entrada, rutas, proveedores y selector de modo | Vista actual y navegación. |
| `features/simulation/` | Panel global, rondas y métricas | Proyección automática y filtros. |
| `features/game/` | Personaje, vecinos, acciones, radio y resultado | Intención local y órdenes confirmadas. |
| `features/map/` | Capas Leaflet, selección y animación | Instancia visual, zoom y selección. |
| `features/session/` | Sesión temporal y recuperación | Identidad permitida, sin secretos de servicio. |
| `shared/api/` | Única frontera HTTP, parseo de respuestas y errores tipados | Datos recibidos y solicitudes. |
| `shared/realtime/` | WebSocket, secuencia, reconexión y sincronización | Conectado/desconectado/recuperando. |
| `shared/ui/` | Botones, alertas, contadores y accesibilidad | Estados visuales reutilizables. |

## Estructura implementada en P0-04

- `frontend/src/app/`: composición de la pantalla inicial y selección local entre simulador y juego.
- `frontend/src/features/mode/`: tarjetas accesibles de modo; la selección solo altera la vista previa.
- `frontend/src/shared/ui/`: marca vectorial reutilizable.
- `frontend/src/shared/api/panel.ts`: cliente HTTP GET y validación runtime de esquema/mapVersion.
- `frontend/src/shared/realtime/panel.ts`: WebSocket de solo lectura, validación de sobres, cursor por partida, estado live/stale y reconexión exponencial.
- `frontend/src/features/map/`: SVG del grafo, refugios, entidades observables, cierres y trayectos zombie confirmados.
- `frontend/src/features/game/GameControls.tsx`: unión, estado propio y controles de orden accesibles por teclado/mouse, deshabilitados en fase incorrecta o al perder frescura del panel.
- `frontend/src/shared/api/game.ts`: cliente same-origin con validación runtime para sesión y acuse; la cookie HttpOnly no se expone a JavaScript.
- `frontend/src/styles.css`: tokens visuales, layout responsivo y preferencia de movimiento reducido.
- `frontend/README.md`: inicio local y límites de esta base.

P4-01 permite consultas iniciales/manuales a `GET /panel/estado` y `GET /panel/mapa`. P4-02 añade snapshots completos por WebSocket, secuencia derivada de versión, heartbeat, aviso de desconexión/desactualización y reconexión. El backend omite zombies dormidos y la UI muestra modo real, métricas, grafo, refugios, cierres, hordas, movimientos confirmados y rutas previstas Dijkstra solo en fase de decisiones. El cliente acepta saltos porque cada snapshot reemplaza el estado completo y descarta repeticiones/estados antiguos de la misma partida. El canal depende del mismo proceso y almacenamiento en memoria; no hay replay durable, control multi-worker o despliegue. El mapa parcial de Manta no certifica seguridad sísmica.

CAM-038 conecta la vista seleccionada «Jugar» a los contratos de sesión/orden: recuperación se hace al pulsar entrar (la cookie se guarda fuera de JS), y los movimientos posibles salen de las calles dirigidas que no estén cerradas ni bloqueadas por horda. Se etiqueta el riesgo de zombie visible, pero el servidor permite que la persona decida. El acuse no se presenta como movimiento confirmado. Faltan radio, deadline/contador autoritativo, navegación/resultado completo, instancia ensamblada y T-19 automatizada; el build acredita TypeScript/empacado, no usabilidad end-to-end.

## Comprobación local

Desde `frontend/`, `npm ci` instala el lockfile y `npm run build` valida TypeScript y produce el bundle Vite. En desarrollo, Vite reenvía `/panel` y `/ws` a `127.0.0.1:8000`. `.github/workflows/ci.yml` define las verificaciones backend/frontend en push a `master` y pull request; esta configuración se revisó localmente, pero el workflow remoto no se ha ejecutado ni publicado.

## Reglas

- El servidor manda sobre posición, turno, mordida y propiedad; una animación no confirma un movimiento.
- Separar estado remoto de selección local. No copiar la misma partida en varios estados independientes sin sincronización.
- Validar respuestas en la frontera. Los componentes reciben tipos del producto, no JSON sin comprobar.
- Orden humana: `sin_orden → enviando → recibida → aplicada`; una sugerencia de radio no cambia esa cadena.
- Reconexión: mostrar datos desactualizados, recuperar instantánea y después consumir eventos nuevos.
- Botones por vecino con etiquetas, foco visible y acceso por teclado; no depender de hover ni de color solamente.
- No bloquear el hilo principal reconstruyendo capas completas por turno. Respetar preferencia de movimiento reducido.
- Rutas previstas y peligros estimados deben distinguirse de posiciones confirmadas.

Los paneles consumen solo la proyección observable. No incluir API keys de servicio, credenciales administrativas o dormidos ocultos en bundles o mensajes. La apariencia detallada se definirá al implementar; no hay todavía un sistema visual aprobado.
