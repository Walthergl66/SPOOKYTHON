# Navira frontend

Tablero web de Navira, construido con React 19, TypeScript y Vite. Todo lo que aparece aquí se ejecuta desde esta carpeta (`frontend/`), salvo que se indique otra cosa.

**Estado real al 26 de octubre de 2026:** el tablero observa el simulador o entra al modo juego. El servidor define el modo activo. Si el backend entrega una partida activa, el panel combina cartografía vectorial externa centrada en Manta con refugios, entidades visibles, cierres, áreas de horda, movimientos confirmados y rutas por personaje de `/panel/mapa` y `/panel/estado`. Recibe snapshots completos por `/ws/panel`; los controles humanos llaman a `/juego/unirse` y `/juego/accion` cuando el backend tiene juego activo.

## Requisitos

- Node.js 20.19 o posterior (CI usa Node 24).
- Un backend en marcha para ver datos. Su arranque está en [backend/README.md](../backend/README.md).

## Arranque

```bash
cd frontend
npm ci
npm run dev
```

Vite sirve el tablero en `http://localhost:5173/`. Para comprobar la salida de producción:

```bash
cd frontend
npm run build
```

En desarrollo, Vite reenvía `/salud`, `/panel`, `/demo`, `/juego`, `/reto` y `/ws` al backend configurado (por defecto `127.0.0.1:8000`), conservando el origen del navegador para validación same-host. Otro servicio local se puede elegir con `NAVIRA_API_TARGET=http://127.0.0.1:8002` al arrancar Vite. Al modificar el proxy en `vite.config.ts`, Vite reinicia el servidor de desarrollo automáticamente.

### Backend para el tablero

Inicia el backend desde `backend/` con el modo que quieras probar. Los comandos completos, con sus variables, están en [backend/README.md](../backend/README.md). Resumen:

- Simulador con controles en el tablero (iniciar, pausar, continuar y reiniciar; solo loopback):

  ```bash
  cd backend
  env NAVIRA_LOCAL_DEMO_CONTROL=1 PYTHONPATH=src .venv/bin/uvicorn navira.main:app --app-dir src --reload
  ```

  Sin `NAVIRA_LOCAL_DEMO_CONTROL=1` la UI informa cómo habilitar el modo y el panel queda en observación. Desde el tablero se configuran escenario y población; cada inicio sin semilla usa un mundo nuevo. El reloj se ejecuta en memoria y se pierde al reiniciar el backend.

- Fixture de Manta en el tablero: ver el comando de `backend/README.md`, con `NAVIRA_DEMO=1` y `NAVIRA_DEMO_MAP` apuntando a `data/maps/manta-hackathon-v1.json` (ruta relativa a `backend/`).

- Juego local: el mismo arranque con `NAVIRA_GAME_DEMO=1` en lugar de `NAVIRA_DEMO=1`. Usa mapa demo sintético, reloj de dos segundos y almacenamiento efímero.

## Cartografía

El mapa base usa MapLibre GL JS y OpenFreeMap (`https://tiles.openfreemap.org/styles/dark` por defecto), con datos de OpenStreetMap. No requiere clave; el navegador solicita externamente los tiles de la zona visible y muestra la atribución del proveedor. La instancia pública se ofrece sin SLA y requiere conexión. Se puede configurar otro estilo vectorial compatible con `VITE_NAVIRA_MAP_STYLE` al compilar.

El mapa admite cámara 2D/3D, zoom y rotación; las huellas se extruyen solo cuando la fuente aporta altura. La capa base es visual: no altera el grafo, reglas, rutas ni snapshots de Navira, y los datos de actores y rutas se renderizan localmente sin enviarse al proveedor. Las rutas conectan nodos del fixture mediante segmentos rectos hasta que el dominio conserve geometría completa de calles.

Los límites de seguridad son explícitos: el fixture de Manta tiene cobertura parcial, sus zonas seguras de tsunami no están certificadas ante sismos y no es guía de emergencia. Los controles locales no deben habilitarse en AWS ni detrás de un proxy público.

## Estructura

| Ruta | Contenido |
|---|---|
| `src/app/` | Entrada, composición de la pantalla y selector de modo. |
| `src/features/mode/` | Tarjetas accesibles de modo. |
| `src/features/map/` | Mapa MapLibre y capas GeoJSON de snapshots. |
| `src/features/game/` | Controles de la partida humana (`GameControls.tsx`). |
| `src/shared/api/` | Única frontera HTTP: cliente de panel, juego y simulador, con validación en tiempo de ejecución. |
| `src/shared/realtime/` | WebSocket de solo lectura, secuencia, reconexión y estado vivo/desactualizado. |
| `src/shared/ui/` | Componentes reutilizables (marca). |
| `src/styles.css` | Tokens visuales, diseño responsivo y preferencia de movimiento reducido. |

## Reglas de la interfaz

- El servidor manda sobre posición, turno, mordida y propiedad. Una animación no confirma un movimiento.
- Las respuestas se validan en la frontera (`shared/api`); los componentes reciben tipos del producto, no JSON sin comprobar.
- La cookie de sesión es HttpOnly y no se expone a JavaScript. Ninguna clave de servicio llega al bundle.
- Accesibilidad por teclado y etiquetas en los botones; no depender solo del color.

La guía para agentes está en [.agents/frontend.md](../.agents/frontend.md).

## Especificaciones y documentación

- Módulos y estados de interfaz: [módulos frontend](../docs/arquitectura/modulos/frontend.md).
- Contratos que consume: [API](../docs/arquitectura/contratos/api.md) y [eventos](../docs/arquitectura/contratos/eventos.md).
- Especificaciones: [SPEC-003 panel vivo](../docs/metodo/especificaciones/SPEC-003-panel-vivo.md), [SPEC-004 personaje humano](../docs/metodo/especificaciones/SPEC-004-juego-humano.md), [SPEC-007 tablero y control local](../docs/metodo/especificaciones/SPEC-007-panel-operador-local.md), [SPEC-008 mapa cartográfico 3D](../docs/metodo/especificaciones/SPEC-008-mapa-cartografico-3d.md).
- Decisiones: [ADR-009 WebSocket de snapshots](../docs/arquitectura/decisiones/0009-panel-ws-snapshots-completos.md), [ADR-015 control local](../docs/arquitectura/decisiones/0015-control-local-de-demo.md), [ADR-016 MapLibre y OpenFreeMap](../docs/arquitectura/decisiones/0016-mapa-maplibre-openfreemap.md).
