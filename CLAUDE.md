@AGENTS.md

# Específico de Claude Code

Empieza por `docs/seguimiento/estado-actual.md`. La documentación vive en `docs/` y su índice es `docs/README.md`.

## Reglas, procesos y comandos del proyecto

- Reglas por zona: `.claude/rules/` (dominio-juego, backend-capas, frontend-panel, pruebas, docs-cambios).
- Procesos: `.claude/skills/` (navira-cambio-sdd, navira-juego, navira-verificar).
- Comandos: `.claude/commands/` (navira-arrancar, navira-verificar, navira-cambio).
- Guías por área: `.agents/README.md` (backend, frontend, pruebas y scripts).

## Comandos reales

- Instalar backend: `cd backend && python -m pip install -e '.[test]'`
- Pruebas backend: `cd backend && python -m unittest discover -s tests -p 'test_*.py' -v`
- Validadores: `python backend/scripts/check_docs.py` y `python backend/scripts/check_sdd.py`. Ambos comprueban `docs/`.
- Frontend (en `frontend/`): `npm ci`, `npm run build`, `npm run dev`.
- Backend demo: `cd backend && env NAVIRA_API_KEY='local-navira-key-change-me' NAVIRA_DEMO=1 NAVIRA_LOCAL_DEMO_CONTROL=1 .venv/bin/uvicorn navira.main:app --app-dir src --reload`
- El entorno Python es `backend/.venv`.

## Reglas de trabajo

- Shell del usuario: fish. Variables de entorno con `env VAR=valor comando`, nunca `export`.
- No hacer commit, push ni publicar sin que el usuario lo pida.
- No crear hooks, agentes ni archivos de herramientas sin necesidad real.
