# Navira — Escape de Manta Zombie

Proyecto para el Track A del hackathon: evacuación sobre un grafo de Manta con zombies móviles, rutas recalculadas y dos modos previstos: simulador automático y juego con un personaje humano.

**Estado real al 26 de octubre de 2026:** el backend y el tablero están implementados localmente. El estado detallado y lo pendiente está en [estado actual](docs/seguimiento/estado-actual.md). No hay despliegue en AWS ni persistencia durable todavía.

## Estructura del repositorio

| Ruta | Qué contiene | Dónde empezar |
|---|---|---|
| [`backend/`](backend/) | API FastAPI, dominio, rutas, simulación, datos del mapa, scripts y pruebas Python. | [backend/README.md](backend/README.md) |
| [`frontend/`](frontend/) | Tablero web React + TypeScript + Vite. | [frontend/README.md](frontend/README.md) |
| [`docs/`](docs/) | Producto, reglas, arquitectura, decisiones, especificaciones, pruebas y seguimiento. | [docs/README.md](docs/README.md) |
| [`.agents/`](.agents/) | Guías por área para agentes de código. | [.agents/README.md](.agents/README.md) |
| [`.claude/`](.claude/) | Reglas, skills y comandos para Claude Code. | — |
| [`.github/`](.github/) | Integración continua (`ci.yml`): pruebas del backend, validadores y build del frontend. | — |
| [`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md) | Instrucciones para agentes y colaboradores. | — |
| [`.gitignore`](.gitignore) | Archivos que no se versionan (entornos, cachés y dependencias). | — |

## Empezar

1. Agentes y colaboradores: leer [AGENTS.md](AGENTS.md) y seguir el protocolo de lectura antes de editar.
2. Documentación central: [docs/README.md](docs/README.md).
3. Qué estamos construyendo: [contexto](docs/producto/contexto.md).
4. Qué existe y qué sigue: [estado actual](docs/seguimiento/estado-actual.md).
5. Tareas y dependencias: [plan de implementación](docs/seguimiento/plan-implementacion.md).

## Arranque rápido

Requisitos: Python 3.12 o posterior para el backend, Node.js 20.19 o posterior para el frontend.

- Backend: `cd backend`, crear `.venv`, instalar con `python -m pip install -e '.[test]'` y arrancar con el modo que quieras. Pasos completos en [backend/README.md](backend/README.md).
- Frontend: `cd frontend`, `npm ci` y `npm run dev`. Pasos completos y conexión con el backend en [frontend/README.md](frontend/README.md).

## Documentos principales

- [Arquitectura](docs/arquitectura/arquitectura.md), [módulos backend](docs/arquitectura/modulos/backend.md) y [módulos frontend](docs/arquitectura/modulos/frontend.md).
- [Reglas](docs/dominio/reglas-juego.md), [modos](docs/dominio/modos.md) y [flujos por rol](docs/dominio/flujos/roles.md).
- [API](docs/arquitectura/contratos/api.md), [eventos](docs/arquitectura/contratos/eventos.md) y [datos](docs/dominio/datos.md).
- [Pruebas](docs/calidad/pruebas.md), [infraestructura](docs/operacion/infraestructura.md), [seguridad](docs/operacion/seguridad.md) y [costos](docs/operacion/costos.md).
- [Decisiones](docs/arquitectura/decisiones/README.md), [pendientes](docs/seguimiento/pendientes.md), [cambios](docs/seguimiento/cambios.md) y [continuidad entre agentes](docs/metodo/continuidad.md).
- [PRD](docs/producto/PRD.md), [TRD](docs/producto/TRD.md), [ODDD: OO + DDD](docs/dominio/ODDD.md) y [SDD](docs/metodo/SDD.md).
- [Especificaciones por funcionalidad](docs/metodo/especificaciones/README.md) y [trazabilidad](docs/metodo/trazabilidad.md).

## Comprobaciones

Validadores documentales (no prueban la aplicación) y pruebas del backend:

```bash
python3 backend/scripts/check_docs.py
python3 backend/scripts/check_sdd.py
cd backend && python -m unittest discover -s tests -p 'test_*.py' -v
cd frontend && npm run build
```

El fixture OSM de Manta es parcial y no es una guía de emergencia. Las metas de latencia, supervivencia y costos son objetivos, no mediciones.
