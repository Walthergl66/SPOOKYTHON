# Navira frontend

Frontend web mínimo de Navira, construido con React, TypeScript y Vite. Ejecutar desde esta carpeta:

```bash
npm ci
npm run dev
```

La pantalla presenta un tablero para observar el simulador o entrar al modo juego. El servidor define el modo activo. Si el backend entrega una partida activa, el panel combina cartografía vectorial externa centrada en Manta con refugios, entidades visibles, cierres, áreas de horda, movimientos confirmados y rutas Dijkstra por personaje de `/panel/mapa` y `/panel/estado`. El mapa admite cámara 2D/3D, zoom y rotación; las huellas se extruyen solo cuando la fuente aporta altura. En CAM-032 recibe snapshots completos por `/ws/panel`; los controles humanos llaman `/juego/unirse` y `/juego/accion` cuando el backend tiene juego activo.

El mapa base usa MapLibre GL JS y OpenFreeMap (`https://tiles.openfreemap.org/styles/dark` por defecto), con datos cartográficos de OpenStreetMap. No requiere clave; el navegador solicita externamente tiles de la zona visible y muestra la atribución del proveedor. La instancia pública se ofrece sin SLA y requiere conexión. Se puede configurar otro estilo vectorial compatible con `VITE_NAVIRA_MAP_STYLE` al compilar. La capa base es visual: no altera el grafo, reglas, rutas ni snapshots de Navira. Los datos de actores/rutas se renderizan localmente y no se envían al proveedor. Las rutas conectan nodos del fixture mediante segmentos rectos hasta que el dominio conserve geometría completa de calles. Consulte [SPEC-008](../doc/especificaciones/SPEC-008-mapa-cartografico-3d.md) y [ADR-016](../doc/decisiones/0016-mapa-maplibre-openfreemap.md).

Para iniciar/pausar una demo sintética desde el tablero, inicia el backend en modo de control local:

```bash
NAVIRA_LOCAL_DEMO_CONTROL=1 PYTHONPATH=src uvicorn navira.main:app --app-dir src --reload
```

El control local se limita a loopback y origen same-host, y no debe habilitarse en AWS ni detrás de un proxy público. Por defecto la demo usa el fixture parcial de Manta y se puede cambiar con `NAVIRA_DEMO_MAP`. Desde el tablero se configuran escenario y población; cada inicio sin semilla usa un mundo nuevo. El reloj se ejecuta en memoria y se pierde al reiniciar el backend. El fixture no acredita seguridad ante sismos ni es guía de emergencia. Sin esta variable la UI informa cómo habilitar el modo y el resto del panel sigue siendo de solo lectura.

Para visualizar la fixture Manta local, iniciar primero el backend desde la raíz del repositorio:

```bash
NAVIRA_DEMO=1 \
NAVIRA_DEMO_MAP=data/maps/manta-hackathon-v1.json \
NAVIRA_DEMO_SEED=31 \
NAVIRA_DEMO_SCENARIO=mixto \
NAVIRA_DEMO_SURVIVORS=20 \
PYTHONPATH=src .venv/bin/uvicorn navira.main:app --app-dir src --reload
```

Para jugar localmente, iniciar el backend con `NAVIRA_GAME_DEMO=1` (en lugar de `NAVIRA_DEMO=1`) y después Vite. Su proxy reenvía `/salud`, `/panel`, `/demo`, `/juego` y `/ws` a `127.0.0.1:8000`; conserva el origen del navegador para validación same-host. El proxy puede apuntar a otro servicio local con `NAVIRA_API_TARGET=http://127.0.0.1:8002`. El juego usa mapa demo sintético, reloj de dos segundos y almacenamiento efímero; no es despliegue ni guía de emergencia. El fixture de Manta tiene cobertura parcial y sus zonas seguras de tsunami no están certificadas ante sismos.

Para comprobar la salida de producción:

```bash
npm run build
```
