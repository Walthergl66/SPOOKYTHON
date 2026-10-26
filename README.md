# Navira — Escape de Manta Zombie

Proyecto para el Track A del hackathon: evacuación sobre un grafo de Manta con zombies móviles, rutas recalculadas y dos modos previstos: simulador automático y juego con un personaje humano.

**Estado real al 26 de octubre de 2026:** `/salud` y `POST /paso` arrancan localmente y sus contratos HTTP tienen pruebas automatizadas y smoke test con Uvicorn. `/paso` requiere `x-api-key` y por ahora responde con espera determinista (`nodoActual`). Dijkstra y el núcleo de simulación existen aislados del endpoint; no hay mapa real, persistencia durable ni despliegue AWS.

## Empezar

1. Agentes y colaboradores: leer [AGENTS.md](AGENTS.md) y seguir el protocolo de lectura antes de editar.
2. Documentación central: [doc/README.md](doc/README.md).
3. Qué estamos construyendo: [contexto](doc/contexto.md).
4. Qué existe y qué sigue: [estado actual](doc/estado-actual.md).
5. Tareas y dependencias: [plan de implementación](doc/plan-implementacion.md).

## Documentos principales

- [Arquitectura](doc/arquitectura.md), [módulos backend](doc/modulos/backend.md) y [módulos frontend](doc/modulos/frontend.md).
- [Reglas](doc/reglas-juego.md), [modos](doc/modos.md) y [flujos por rol](doc/flujos/roles.md).
- [API](doc/contratos/api.md), [eventos](doc/contratos/eventos.md) y [datos](doc/datos.md).
- [Pruebas](doc/pruebas.md), [infraestructura](doc/infraestructura.md), [seguridad](doc/seguridad.md) y [costos](doc/costos.md).
- [Decisiones](doc/decisiones/README.md), [pendientes](doc/pendientes.md), [cambios](doc/cambios.md) y [continuidad entre agentes](doc/continuidad.md).
- [PRD](doc/PRD.md), [TRD](doc/TRD.md), [ODDD: OO + DDD](doc/ODDD.md) y [SDD](doc/SDD.md).
- [Especificaciones por funcionalidad](doc/especificaciones/README.md) y [trazabilidad](doc/trazabilidad.md).

## Backend local

Requiere Python 3.12 o posterior:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
export NAVIRA_API_KEY='local-navira-key-change-me'
uvicorn navira.main:app --app-dir src --reload
```

La salud local se consulta en `GET /salud`. El contrato inicial del motor:

```bash
curl -X POST http://127.0.0.1:8000/paso \
  -H 'content-type: application/json' \\
  -H 'x-api-key: local-navira-key-change-me' \\
  -d '{"sobrevivienteId":"S-0089","nodoActual":"N-0117","turno":142}'
```

Respuesta inicial: `{"siguienteNodo":"N-0117"}`. Esta espera cumple la alternativa permitida por el contrato, pero no calcula rutas ni garantiza seguridad. La clave de ejemplo es solo local; reemplázala y no uses una clave real en el repositorio. El contrato documentado está en [API](doc/contratos/api.md); el plan sigue en [estado actual](doc/estado-actual.md).

El modelo del grafo y el fixture de cuatro nodos son sintéticos; todavía no contienen calles reales de Manta. La carga y validación están en `src/navira/domain/mapa.py`; el origen y el área de extracción de OSM siguen pendientes.

Comprobación documental disponible, sin dependencias externas:

```bash
python3 scripts/check_docs.py
```

Comprueba enlaces locales y que los Markdown de `doc/` sean accesibles desde su índice. No comprueba URLs externas, renderizado o comportamiento de la aplicación.

Validación estructural SDD y regresiones del comprobador:

```bash
python3 scripts/check_sdd.py
python3 -m unittest discover -s tests -p 'test_check_sdd.py'
```

Para ejecutar todas las pruebas de la aplicación y del SDD, instala la dependencia opcional HTTP de pruebas:

```bash
python -m pip install -e '.[test]'
python -m unittest discover -s tests -p 'test_*.py' -v
```

El contrato base de `/paso` se verificó; planificación, idempotencia persistida, rendimiento y rondas completas todavía no están implementados/verificados.
