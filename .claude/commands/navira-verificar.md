---
description: Ejecuta las verificaciones de Navira (backend, validadores, frontend) y muestra resultados reales
argument-hint: '[backend|docs|frontend|T-NN]'
---
Verifica Navira. Si existe la skill `navira-verificar` ([.claude/skills/navira-verificar/SKILL.md](../skills/navira-verificar/SKILL.md)), úsala; si no, sigue estos pasos. Fuente de las pruebas T-NN: [docs/calidad/pruebas.md](../../docs/calidad/pruebas.md).

Área pedida: $ARGUMENTS (vacío = backend, validadores y frontend).

- backend: `cd backend && .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
- docs: `python backend/scripts/check_docs.py` y `python backend/scripts/check_sdd.py`. Si fallan, repórtalo con la salida real.
- frontend: `cd frontend && npm ci && npm run build` (omite `npm ci` si `node_modules` ya existe).
- Si el argumento es un ID `T-NN`, localízalo en `docs/calidad/pruebas.md` y ejecuta solo las pruebas que lo cubran.

Reglas: muestra la salida real (resumen y fallos completos); no declares éxito sin salida que lo respalde; indica qué no se ejecutó y por qué. No edites pruebas para que pasen.
