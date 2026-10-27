# Guías por área de Navira

Reglas generales de todo el repositorio: [AGENTS.md](../AGENTS.md). Documentación del producto: [índice general](../docs/README.md).

Estas guías describen cada zona del código. Leer la guía del área antes de tocarla. Las reglas que se aplican automáticamente al abrir archivos de esa zona están en `.claude/rules/`; los procesos en `.claude/skills/` y los comandos en `.claude/commands/`.

| Área | Guía | Carpeta | Reglas asociadas (`.claude/rules/`) |
|---|---|---|---|
| Backend | [backend.md](backend.md) | `backend/src/navira/` | `backend-capas`, `dominio-juego` |
| Frontend | [frontend.md](frontend.md) | `frontend/` | `frontend-panel` |
| Pruebas | [pruebas.md](pruebas.md) | `backend/tests/` | `pruebas` |
| Scripts | [scripts.md](scripts.md) | `scripts/` | `pruebas` (cubre `backend/scripts/**`) |

Las guías no duplican contratos ni reglas: enlazan a `docs/`, que es la fuente propietaria.

Para diseñar o mover código entre capas, usar la [guía de Clean Architecture](../docs/arquitectura/guia-clean-architecture.md) y los subagentes `arquitecto-backend` y `arquitecto-frontend` de `.claude/agents/`.
