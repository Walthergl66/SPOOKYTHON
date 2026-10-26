# Módulos frontend y estados de interfaz

Estado: base React + TypeScript + Vite implementada en `frontend/`; no hay cliente conectado a la API, mapa operativo ni transporte en tiempo real. Leaflet sigue previsto para la fase de mapa interactivo. La pantalla actual es una selección/vista previa de modos con una ilustración que se identifica como tal.

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
- `frontend/src/styles.css`: tokens visuales, layout responsivo y preferencia de movimiento reducido.
- `frontend/README.md`: inicio local y límites de esta base.

`GET /panel/estado`, `GET /panel/mapa`, sesión, WebSocket, selección de personajes y controles aún no existen. No mostrar la silueta ilustrativa como cartografía ni inferir estado de una partida a partir de ella. El criterio CA-003-01 sigue pendiente hasta integrar una proyección real que oculte zombies dormidos y peligros privados.

## Comprobación local

Desde `frontend/`, `npm ci` instala el lockfile y `npm run build` valida TypeScript y produce el bundle Vite. `.github/workflows/ci.yml` define las verificaciones backend/frontend en push a `master` y pull request; esta configuración se revisó localmente, pero el workflow remoto no se ha ejecutado ni publicado.

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
