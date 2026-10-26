# Navira frontend

Frontend web mínimo de Navira, construido con React, TypeScript y Vite. Ejecutar desde esta carpeta:

```bash
npm ci
npm run dev
```

La pantalla presenta los modos simulador y juego. El selector solo cambia la vista; el servidor define el modo activo. Si el backend entrega una partida activa, el panel dibuja el grafo, refugios, entidades visibles, cierres, áreas de horda, movimientos confirmados, rutas Dijkstra por personaje y métricas desde `/panel/mapa` y `/panel/estado`. En CAM-032 recibe snapshots completos por `/ws/panel`; los controles humanos llaman `/juego/unirse` y `/juego/accion` cuando el backend tiene juego activo.

Para visualizar la fixture Manta local, iniciar primero el backend desde la raíz del repositorio:

```bash
NAVIRA_DEMO=1 \
NAVIRA_DEMO_MAP=data/maps/manta-hackathon-v1.json \
NAVIRA_DEMO_SEED=31 \
NAVIRA_DEMO_SCENARIO=mixto \
NAVIRA_DEMO_SURVIVORS=20 \
PYTHONPATH=src .venv/bin/uvicorn navira.main:app --app-dir src --reload
```

Para jugar localmente, iniciar el backend con `NAVIRA_GAME_DEMO=1` (en lugar de `NAVIRA_DEMO=1`) y después Vite. Su proxy reenvía `/panel`, `/juego` y `/ws` a `127.0.0.1:8000`; conserva el origen del navegador para validación same-host. Este modo usa el mapa demo sintético, reloj de dos segundos y almacenamiento efímero; no es despliegue ni guía de emergencia. El fixture de Manta tiene cobertura parcial y sus zonas seguras de tsunami no están certificadas ante sismos.

Para comprobar la salida de producción:

```bash
npm run build
```
