# Navira frontend

Frontend web mínimo de Navira, construido con React, TypeScript y Vite. Ejecutar desde esta carpeta:

```bash
npm ci
npm run dev
```

La pantalla presenta un tablero para observar el simulador o entrar al modo juego. El servidor define el modo activo. Si el backend entrega una partida activa, el panel dibuja el grafo, refugios, entidades visibles, cierres, áreas de horda, movimientos confirmados, rutas Dijkstra por personaje y métricas desde `/panel/mapa` y `/panel/estado`. En CAM-032 recibe snapshots completos por `/ws/panel`; los controles humanos llaman `/juego/unirse` y `/juego/accion` cuando el backend tiene juego activo.

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
