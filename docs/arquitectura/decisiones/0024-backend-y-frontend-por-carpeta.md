# ADR-024 — Backend y frontend en carpetas propias; raíz general

Fecha: 2026-10-26 (Ecuador continental).
Estado: aceptada e implementada localmente (CAM-065).
Origen: el usuario pidió centralizar el backend en una carpeta, separarlo del frontend y dejar en la raíz solo lo general: README general y `.gitignore`. Pidió también que `pyproject.toml` y `.env.example` estén dentro del backend y que cada área tenga su README con arranque y especificaciones.

## Contexto y restricciones

- El código Python, sus datos, sus scripts y sus pruebas estaban repartidos entre `src/`, `data/`, `scripts/`, `tests/` y la raíz (`pyproject.toml`, `.env.example`, `.venv/`).
- El frontend ya vivía en `frontend/`, pero sus instrucciones estaban en el README raíz junto con las del backend.
- `src/navira/` calcula la raíz del repositorio con `parents[2]` y `tests/` con `parents[1]`. Al mover `src/`, `data/`, `tests/` y `scripts/` juntos, esas rutas siguen siendo válidas.
- `scripts/check_docs.py` y `scripts/check_sdd.py` leen `docs/` de la raíz; tras moverlos a `backend/scripts/` necesitan subir dos niveles.
- Git ejecuta la CI desde la raíz del repositorio; el job del backend necesita `working-directory: backend`.
- El entorno virtual contiene rutas absolutas y no puede moverse; se recrea dentro de `backend/`.

## Decisión

- `backend/` contiene: `src/`, `data/`, `scripts/`, `tests/`, `pyproject.toml`, `.env.example`, `.venv/` (local, ignorado por git) y `README.md`.
- `frontend/` contiene el tablero y su `README.md`.
- La raíz contiene el `README.md` general, `.gitignore`, `docs/`, `.agents/`, `.claude/`, `.github/`, `AGENTS.md` y `CLAUDE.md`.
- Cada carpeta de código tiene su README con el arranque, la configuración y la lista de especificaciones aplicables; el README raíz solo indica dónde está cada cosa.
- La CI ejecuta el backend desde `backend/`.

## Alternativas consideradas

- **Dejar `pyproject.toml` en la raíz:** descartado por decisión del usuario, que quiere el backend completo dentro de su carpeta.
- **Mover también `docs/` a una carpeta propia:** no se hizo; la documentación es transversal a backend y frontend.
- **Mover `.venv` sin recrearlo:** descartado; las rutas absolutas hacen que el entorno movido no funcione.

## Consecuencias, límites y costos

- Los comandos de arranque y de pruebas empiezan con `cd backend` o usan rutas `backend/...`.
- `pyproject.toml` conserva `readme = "README.md"`, que ahora apunta a `backend/README.md`.
- Los scripts de validación calculan la raíz del repositorio con `parents[2]`; si se mueven de nuevo, hay que actualizarlo.
- La CI no se ha ejecutado en GitHub Actions; solo se han ejecutado los mismos comandos localmente.

## Supuestos y pendientes relacionados

- `.env.example` queda en `backend/`; no se comprobó si el backend lo lee automáticamente. La documentación lo presenta como lista de variables de referencia.

## Documentos y módulos propietarios afectados

`README.md`, `backend/README.md`, `frontend/README.md`, `backend/pyproject.toml`, `backend/scripts/`, `.github/workflows/ci.yml`, `docs/` (rutas de comandos) y la configuración de agentes (`CLAUDE.md`, `AGENTS.md`, `.agents/`, `.claude/`).

## Evidencia de implementación/verificación

CAM-065: `python3 backend/scripts/check_docs.py` y `python3 backend/scripts/check_sdd.py` correctos; pruebas del backend (`cd backend && python -m unittest discover -s tests -p 'test_*.py'`) con 178 pruebas correctas; `npm run build` del frontend correcto; `backend/.venv` recreado e importa `navira`.

## Sustituye / sustituida por

Complementa [ADR-004](0004-documentacion-y-continuidad.md) y [ADR-022](0022-organizacion-documental-por-temas.md); no sustituye ninguna.
