# Navira — Escape de Manta Zombie

Proyecto para el Track A del hackathon: evacuación sobre un grafo de Manta con zombies móviles, rutas recalculadas y dos modos previstos: simulador automático y juego con un personaje humano.

**Estado real al 26 de octubre de 2026:** `/salud` y `POST /paso` arrancan localmente. Con `NAVIRA_DEMO=1`, el proceso inicializa un mundo sintético y `/paso` usa Dijkstra. Existe una pantalla React con selector de vista previa y un panel inicial que consulta manualmente proyecciones de solo lectura de una partida activa. El mapa sintético no representa Manta; la fixture OSM de Manta es parcial. WebSocket, reloj de producción, persistencia durable y despliegue AWS siguen pendientes.

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
export NAVIRA_DEMO=1
uvicorn navira.main:app --app-dir src --reload
```

La demo ubica sobrevivientes y zombies aleatoriamente en nodos elegibles con ruta dirigida al refugio sintético de `D-005`; la recomendación depende de la semilla y del estado inicial. Para usar otro mapa de desarrollo, configura `NAVIRA_DEMO_MAP`; `NAVIRA_DEMO_SEED` fija la semilla para repetir una partida. Si se omite, se genera una semilla nueva. `NAVIRA_DEMO=1` solo configura una partida en memoria para desarrollo: reiniciar el proceso reinicia el mundo.

Para correr varias rondas automáticas localmente y guardar la salida JSONL:

```bash
PYTHONPATH=src python -m navira.simulador_demo --escenario mixto --sobrevivientes 20 --turnos 10 --semilla 31 > /tmp/navira-demo.jsonl
```

Perfiles disponibles: `libre`, `caminantes`, `mixto` y `horda`; `--sobrevivientes` admite de 1 a 200 personajes con posiciones iniciales reproducibles al fijar semilla. `--mapa ruta/al/mapa.json` permite elegir otro mapa que contenga los nodos del perfil. En el mapa incluido las posiciones se reparten al azar entre cuatro nodos y pueden coincidir. El ejecutor termina al evacuar o perder a todos los sobrevivientes activos, o al llegar al límite de turnos. Cada línea reporta el resultado observable de un turno y excluye zombies que siguen dormidos. Esto es una simulación sintética del dominio; no es la prueba concurrente del endpoint ni sustituye las rondas oficiales. El comando no espera dos segundos entre turnos y usa snapshots volátiles.

El fixture de Manta también se puede usar para recorridos sintéticos, por ejemplo con `--mapa data/maps/manta-hackathon-v1.json`. CAM-025 documenta una ejecución de tres turnos con semilla fija y cohortes de 20/80/200; no es una evaluación oficial ni una recomendación de evacuación real.

Para evaluar decisiones HTTP mientras avanza el mundo, el ejecutor local inicia Uvicorn en loopback y consulta `/paso` por cada sobreviviente activo. Los inicios se alinean a una cadencia monotónica de dos segundos (configurable) y el reporte registra latencias y retrasos:

```bash
PYTHONPATH=src python -m navira.evaluacion_local --turnos 3 --poblaciones 20 80 200 --concurrencia 200 --semilla 20261026 --periodo-segundos 2
```

CAM-029 documenta esta prueba corta de tres turnos por cohorte. Es evidencia local exploratoria; no sustituye los 150 turnos de cada ronda oficial ni una medición desde AWS o el entorno del evaluador.

Para medir localmente la respuesta HTTP de `/paso`, ejecuta el servidor con la misma configuración y luego corre el cliente desde otra terminal:

```bash
export NAVIRA_DEMO=1
export NAVIRA_DEMO_SURVIVORS=20
export NAVIRA_DEMO_SEED=31
export NAVIRA_DEMO_SCENARIO=libre
export NAVIRA_API_KEY='local-navira-key-change-me'
uvicorn navira.main:app --app-dir src
```

```bash
PYTHONPATH=src python -m navira.carga_http --sobrevivientes 20 --semilla 31 --escenario libre --rondas 1 --concurrencia 20
```

El cliente imprime solicitudes, estados HTTP, errores y p50/p95/p99/max desde el cliente. `--sobrevivientes` acepta 20, 80 o 200 y `--rondas 150` agenda ráfagas cada dos segundos. La configuración del proceso debe coincidir con la del cliente. Cada ráfaga repite el mismo snapshot, por lo que esto mide decisiones HTTP locales, no un turno completo ni la evaluación oficial. La clave debe permanecer en una variable de entorno.

La salud local se consulta en `GET /salud`. El contrato inicial del motor:

```bash
curl -X POST http://127.0.0.1:8000/paso \
  -H 'content-type: application/json' \\
  -H 'x-api-key: local-navira-key-change-me' \\
  -d '{"sobrevivienteId":"S-DEMO-001","nodoActual":"D-001","turno":0}'
```

Respuesta demo para `S-DEMO-001`, `D-001`, turno `0`: `{"siguienteNodo":"D-002"}`. El motor devuelve una recomendación del estado actual; no garantiza seguridad futura. Sin `NAVIRA_DEMO=1`, el respaldo responde con el nodo actual. La clave de ejemplo es solo local; reemplázala y no uses una clave real en el repositorio. El contrato documentado está en [API](doc/contratos/api.md); el plan sigue en [estado actual](doc/estado-actual.md).

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

## Frontend local

Requiere Node.js 20.19 o posterior (CI usa Node 24). Desde `frontend/`:

```bash
npm ci
npm run dev
```

Para verificar el bundle: `npm run build`. El modo de la tarjeta solo cambia una vista previa. El panel muestra el modo real del servidor, métricas del snapshot y una ruta Dijkstra seleccionable; requiere partida activa para cargar el mapa/estado. La ruta no es una garantía de seguridad. El detalle está en [frontend](doc/modulos/frontend.md).

Para mostrar la fixture de Manta, inicia el backend como se describe en [guía frontend](frontend/README.md); Vite reenvía las consultas `/panel` al servicio local. La actualización del estado es manual, sin WebSocket.
