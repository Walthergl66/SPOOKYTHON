---
description: Arranca el backend demo y Vite de Navira en local si no están activos
---
Arranca el entorno local de Navira. Fuentes: [backend/README.md](../../backend/README.md) (Arranque) y [docs/arquitectura/modulos/frontend.md](../../docs/arquitectura/modulos/frontend.md) (Comprobación local). Shell del usuario: fish, usa `env VAR=valor comando`, nunca `export`. Entorno: `backend/.venv`.

1. Comprueba si ya responden: `curl -s -m 3 http://127.0.0.1:8000/salud` y `curl -s -m 3 -o /dev/null -w '%{http_code}' http://localhost:5173/`. No relances lo que ya funciona.
2. Backend (si falla `/salud`), en segundo plano desde la raíz:
   `cd backend && env NAVIRA_API_KEY='local-navira-key-change-me' NAVIRA_DEMO=1 .venv/bin/uvicorn navira.main:app --app-dir src --reload`
   Añade `NAVIRA_LOCAL_DEMO_CONTROL=1` solo si el usuario lo pide en: $ARGUMENTS
3. Frontend (si falla `/`): si no existe `frontend/node_modules`, ejecuta antes `cd frontend && npm ci`. Luego `cd frontend && npm run dev` en segundo plano.
4. Espera unos segundos y repite las comprobaciones del paso 1. Si alguna falla, muestra el error real del proceso; no declares éxito sin respuesta.
5. Informa: backend `http://127.0.0.1:8000` (salud en `/salud`), panel Vite `http://localhost:5173`, y si el control local de demo está activo o no.

Aviso: los procesos en segundo plano se detienen si termina la sesión de Claude Code.
