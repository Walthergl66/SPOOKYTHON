# Navira — Escape de Manta Zombie

Simulación de evacuación sobre el grafo vial de Manta: zombies que se mueven, rutas que se recalculan en cada turno y dos modos de juego sobre las mismas reglas.

> **Estado al 26 de octubre de 2026:** backend y tablero funcionan en local. No hay despliegue en AWS ni persistencia durable todavía. Detalle en [estado actual](docs/seguimiento/estado-actual.md).

## Qué demuestra

- **Rutas que se recalculan:** en cada turno el planificador evita zombies activos, hordas, cierres viales y cruces opuestos. Usa búsqueda temporal acotada, con respaldo en Dijkstra.
- **Servidor autoritativo:** el servidor decide reloj, posiciones, legalidad, mordidas y llegadas. El navegador no modifica el mundo.
- **Dos modos, mismas reglas:** un simulador automático reproducible por semilla, y un juego en el que un personaje humano recibe órdenes por turno.
- **Panel en vivo:** mapa de Manta con refugios, sobrevivientes, zombies visibles y ruta prevista, actualizado por WebSocket.

## Demo en local

Requisitos: Python 3.12 o posterior, y Node.js 24 (la versión que usa la CI).

**1. Backend**, desde `backend/`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
env NAVIRA_API_KEY='local-navira-key-change-me' NAVIRA_DEMO=1 NAVIRA_LOCAL_DEMO_CONTROL=1 .venv/bin/uvicorn navira.main:app --reload
```

**2. Tablero**, desde `frontend/`, en otra terminal:

```bash
npm ci
npm run dev
```

Abre `http://localhost:5173/`. Con `NAVIRA_LOCAL_DEMO_CONTROL=1` puedes iniciar, pausar, continuar y reiniciar el simulador desde el tablero. Desde allí también eliges escenario y población; cada inicio sin semilla genera un mundo nuevo.

**Modo juego:** arranca el backend con `NAVIRA_GAME_DEMO=1` en lugar de `NAVIRA_DEMO=1`, sin `NAVIRA_LOCAL_DEMO_CONTROL`, y elige el modo Juego en el tablero. El juego usa un mapa sintético, un reloj de dos segundos y almacenamiento en memoria.

**Mapa de Manta:** para simular sobre el fixture vial de Manta, añade `NAVIRA_DEMO_MAP=data/maps/manta-hackathon-v1.json` al arranque del backend. La ruta es relativa a `backend/`. El fixture tiene 300 nodos de la zona central y cuatro refugios.

## Pruebas

```bash
cd backend && .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
cd frontend && npm test && npm run build
python3 backend/scripts/check_docs.py && python3 backend/scripts/check_sdd.py
```

Al 26 de octubre: 181 pruebas de backend y 59 de frontend. Los validadores documentales comprueban la documentación; no prueban la aplicación.

## Límites

- No hay despliegue en AWS, ni TLS, ni persistencia durable. El mundo, la sesión y las reservas viven en memoria y se pierden al reiniciar.
- El fixture de Manta es parcial, y sus parámetros de amenaza son sintéticos. No es una guía de emergencia ni acredita seguridad sísmica.
- El mapa base usa tiles públicos de OpenFreeMap y requiere conexión a internet.
- Las metas de latencia, supervivencia y costos son objetivos. No son mediciones.

## Estructura del repositorio

| Ruta | Qué contiene | Dónde empezar |
|---|---|---|
| [`backend/`](backend/) | API FastAPI, dominio, rutas, simulación, datos del mapa, scripts y pruebas Python. | [backend/README.md](backend/README.md) |
| [`frontend/`](frontend/) | Tablero web React + TypeScript + Vite. | [frontend/README.md](frontend/README.md) |
| [`docs/`](docs/) | Producto, reglas, arquitectura, decisiones, especificaciones, pruebas y seguimiento. | [docs/README.md](docs/README.md) |
| [`.agents/`](.agents/) | Guías por área para agentes de código. | [.agents/README.md](.agents/README.md) |
| [`.claude/`](.claude/) | Reglas, skills y comandos para Claude Code. | — |
| [`.github/`](.github/) | CI (`ci.yml`): pruebas del backend, validadores y build del frontend. Configurada; aún no se ha ejecutado en GitHub Actions. | — |
| [`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md) | Instrucciones para agentes y colaboradores. | — |

La arquitectura sigue Clean Architecture: en el backend, el dominio no depende de nadie, la aplicación define puertos y los adaptadores los implementan. Ver [arquitectura](docs/arquitectura/arquitectura.md) y [guía de Clean Architecture](docs/arquitectura/guia-clean-architecture.md).

## Documentación

- Para colaboradores y agentes: leer [AGENTS.md](AGENTS.md) y seguir el protocolo de lectura antes de editar. Índice completo en [docs/README.md](docs/README.md).
- Qué construimos: [contexto](docs/producto/contexto.md). Qué existe y qué sigue: [estado actual](docs/seguimiento/estado-actual.md).
- Reglas: [reglas del juego](docs/dominio/reglas-juego.md), [modos](docs/dominio/modos.md) y [flujos por rol](docs/dominio/flujos/roles.md).
- Contratos: [API](docs/arquitectura/contratos/api.md), [eventos](docs/arquitectura/contratos/eventos.md) y [datos](docs/dominio/datos.md).
- Calidad y operación: [pruebas](docs/calidad/pruebas.md), [infraestructura](docs/operacion/infraestructura.md), [seguridad](docs/operacion/seguridad.md) y [costos](docs/operacion/costos.md).
- Decisiones y trazabilidad: [decisiones](docs/arquitectura/decisiones/README.md), [cambios](docs/seguimiento/cambios.md), [especificaciones](docs/metodo/especificaciones/README.md) y [trazabilidad](docs/metodo/trazabilidad.md).
