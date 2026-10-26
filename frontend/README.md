# Navira frontend

Frontend web mínimo de Navira, construido con React, TypeScript y Vite. Ejecutar desde esta carpeta:

```bash
npm ci
npm run dev
```

La pantalla presenta los modos simulador y juego. El selector cambia solo la vista previa; no inicia partidas ni altera el modo actual del servidor. Si el backend entrega una partida activa, el panel dibuja el grafo, refugios, entidades visibles, cierres, áreas de horda, movimientos confirmados, rutas Dijkstra por personaje y métricas desde `/panel/mapa` y `/panel/estado`. En CAM-032 recibe snapshots completos por `/ws/panel`, muestra conexión/desactualización y reconecta con backoff; el botón conserva la consulta manual.

Para visualizar la fixture Manta local, iniciar primero el backend desde la raíz del repositorio:

```bash
NAVIRA_DEMO=1 \
NAVIRA_DEMO_MAP=data/maps/manta-hackathon-v1.json \
NAVIRA_DEMO_SEED=31 \
NAVIRA_DEMO_SCENARIO=mixto \
NAVIRA_DEMO_SURVIVORS=20 \
PYTHONPATH=src .venv/bin/uvicorn navira.main:app --app-dir src --reload
```

Luego iniciar Vite en otra terminal. Su proxy local reenvía `/panel` y `/ws` a `127.0.0.1:8000`. El WebSocket de desarrollo conserva la cabecera de origen del navegador para que el backend pueda aplicar su validación same-host a través del proxy. La fixture de Manta tiene cobertura parcial y los refugios de tsunami no están certificados ante sismos; la app no es una guía de emergencia.

Para comprobar la salida de producción:

```bash
npm run build
```
