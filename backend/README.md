# Navira backend

API FastAPI del motor de evacuación de Navira: dominio, rutas, simulación, datos del mapa, scripts y pruebas Python. Todo lo que aparece aquí se ejecuta desde esta carpeta (`backend/`) salvo que se indique otra cosa.

**Estado real al 26 de octubre de 2026:** `/salud`, `POST /paso`, panel HTTP y `WS /ws/panel` están implementados localmente. `NAVIRA_DEMO=1` inicia el simulador sintético. `NAVIRA_GAME_DEMO=1` inicia un juego sintético local con sesión humana, aparición aleatoria y reloj servidor de dos segundos. Mundo, sesión y reserva se pierden al reiniciar; TLS/despliegue, persistencia durable, recuperación tras caída y política productiva de revocación siguen pendientes. El fixture OSM de Manta es parcial.

## Requisitos

- Python 3.12 o posterior (CI usa 3.12).
- El entorno virtual vive en `backend/.venv`. Si lo recreas, instala siempre desde esta carpeta.

## Arranque

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
env NAVIRA_API_KEY='local-navira-key-change-me' NAVIRA_DEMO=1 .venv/bin/uvicorn navira.main:app --app-dir src --reload
```

En fish, `source .venv/bin/activate.fish` activa el entorno y `env VAR=valor comando` sirve para variables de entorno en ambos shells. La clave de ejemplo es solo local: reemplázala y no uses una clave real en el repositorio. `.env.example` lista las variables reconocidas.

La salud local se consulta en `GET /salud`.

### Modos de arranque

| Variable | Efecto |
|---|---|
| `NAVIRA_API_KEY` | Clave de servicio para `POST /paso`. Obligatoria en todos los modos. |
| `NAVIRA_DEMO=1` | Simulador sintético en memoria. Sin esta variable, el backend responde con el respaldo de espera. |
| `NAVIRA_GAME_DEMO=1` | Juego humano sintético local, en lugar de `NAVIRA_DEMO=1`. Reloj de dos segundos; pierde su estado al reiniciar. |
| `NAVIRA_LOCAL_DEMO_CONTROL=1` | Permite iniciar, pausar, continuar y reiniciar la demo desde el tablero. Solo loopback y origen same-host; no habilitar en AWS ni detrás de un proxy público. |
| `NAVIRA_DEMO_MAP` | Mapa de desarrollo a usar en la demo. Por defecto, el sintético. |
| `NAVIRA_DEMO_SEED` | Fija la semilla para repetir una partida. Si se omite, se genera una nueva. |
| `NAVIRA_DEMO_SCENARIO`, `NAVIRA_DEMO_SURVIVORS` | Escenario y población iniciales de la demo. |

La demo ubica sobrevivientes y zombies aleatoriamente en nodos elegibles con ruta dirigida al refugio sintético de `D-005`; la recomendación depende de la semilla y del estado inicial. Ambos modos usan el mapa demo sintético, no Manta ni una guía de evacuación.

Para visualizar el fixture de Manta en el tablero:

```bash
cd backend
env NAVIRA_DEMO=1 \
  NAVIRA_DEMO_MAP=data/maps/manta-hackathon-v1.json \
  NAVIRA_DEMO_SEED=31 \
  NAVIRA_DEMO_SCENARIO=mixto \
  NAVIRA_DEMO_SURVIVORS=20 \
  PYTHONPATH=src .venv/bin/uvicorn navira.main:app --app-dir src --reload
```

## Comandos de simulación y medición

Simulador automático por línea de comandos, con salida JSONL:

```bash
cd backend
PYTHONPATH=src python -m navira.simulador_demo --escenario mixto --sobrevivientes 20 --turnos 10 --semilla 31 > /tmp/navira-demo.jsonl
```

Perfiles disponibles: `libre`, `caminantes`, `mixto` y `horda`. `--sobrevivientes` admite de 1 a 200 personajes con posiciones iniciales reproducibles al fijar semilla. `--mapa ruta/al/mapa.json` permite elegir otro mapa que contenga los nodos del perfil; en el mapa incluido las posiciones se reparten al azar entre cuatro nodos y pueden coincidir. El ejecutor termina al evacuar o perder a todos los sobrevivientes activos, o al llegar al límite de turnos. Cada línea reporta el resultado observable de un turno y excluye zombies que siguen dormidos. No es la prueba concurrente del endpoint ni sustituye las rondas oficiales; no espera dos segundos entre turnos y usa snapshots volátiles.

El fixture de Manta también sirve para recorridos sintéticos: `--mapa data/maps/manta-hackathon-v1.json`. CAM-025 documenta una ejecución de tres turnos con semilla fija y cohortes de 20/80/200; no es una evaluación oficial ni una recomendación de evacuación real.

Evaluación HTTP local con avance de turnos. El ejecutor inicia Uvicorn en loopback y consulta `/paso` por cada sobreviviente activo; los inicios se alinean a una cadencia monotónica de dos segundos:

```bash
cd backend
PYTHONPATH=src python -m navira.evaluacion_local --turnos 3 --poblaciones 20 80 200 --concurrencia 200 --semilla 20261026 --periodo-segundos 2
```

CAM-029 documenta esta prueba corta de tres turnos por cohorte. CAM-087 mantiene la ventana solicitada aunque la partida termine antes y reporta por separado los turnos de juego y slots ociosos; el período ocioso no genera solicitudes ni cuenta como carga del motor. Para ejecutar los presets Reto R1/R2/R3 en secuencia, usa `PYTHONPATH=src python -m navira.evaluacion_local --campana-reto`; sin `--turnos`, mide 150 slots de 2 s en cada una de las tres rondas. El proceso emite progreso por ronda en stderr y un JSON consolidado en stdout. Esto es evidencia HTTP loopback local, no medición de AWS ni garantía de 150 turnos activos.

Carga HTTP contra un servidor ya en marcha. Ejecuta el servidor con la misma configuración del cliente y luego el cliente desde otra terminal:

```bash
cd backend
env NAVIRA_DEMO=1 NAVIRA_DEMO_SURVIVORS=20 NAVIRA_DEMO_SEED=31 NAVIRA_DEMO_SCENARIO=libre NAVIRA_API_KEY='local-navira-key-change-me' \
  .venv/bin/uvicorn navira.main:app --app-dir src
```

```bash
cd backend
PYTHONPATH=src python -m navira.carga_http --sobrevivientes 20 --semilla 31 --escenario libre --rondas 1 --concurrencia 20
```

El cliente imprime solicitudes, estados HTTP, errores y p50/p95/p99/max desde el cliente. `--sobrevivientes` acepta 20, 80 o 200 y `--rondas 150` agenda ráfagas cada dos segundos. Cada ráfaga repite el mismo snapshot, por lo que esto mide decisiones HTTP locales, no un turno completo ni la evaluación oficial. La clave debe permanecer en una variable de entorno.

## Contrato inicial de `/paso`

```bash
curl -X POST http://127.0.0.1:8000/paso \
  -H 'content-type: application/json' \
  -H 'x-api-key: local-navira-key-change-me' \
  -d '{"sobrevivienteId":"S-DEMO-001","nodoActual":"D-001","turno":0}'
```

Respuesta demo para `S-DEMO-001`, `D-001`, turno `0`: `{"siguienteNodo":"D-002"}`. El motor devuelve una recomendación del estado actual; no garantiza seguridad futura. Sin `NAVIRA_DEMO=1`, el respaldo responde con el nodo actual. El contrato documentado está en [API](../docs/arquitectura/contratos/api.md).

## Pruebas y validación

Pruebas del backend (desde `backend/`, con el entorno instalado con `[test]`):

```bash
cd backend
python -m unittest discover -s tests -p 'test_*.py' -v
```

Validadores documentales y SDD, que no prueban la aplicación. Se ejecutan desde cualquier carpeta; leen `docs/` de la raíz del repositorio:

```bash
python3 backend/scripts/check_docs.py
python3 backend/scripts/check_sdd.py
python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'
```

El contrato base de `/paso` se verificó; planificación, idempotencia persistida, rendimiento y rondas completas todavía no están implementados ni verificados. Las metas de p95, supervivencia y costos son objetivos, no mediciones.

## Estructura

| Ruta | Contenido |
|---|---|
| `src/navira/` | Código del motor: `domain/` (grafo y entidades), `routing/` (rutas y pronóstico), `simulation/` (resolución de turnos), `application/` (casos de uso y puertos), `adapters/` (implementaciones en memoria), `api/` (HTTP y WebSocket), `main.py` (ensamblado). |
| `data/maps/` | Fixtures de mapa: `demo-sintetico.json` (desarrollo), `manta-hackathon-v1.json` (grafo OSM parcial) y su archivo de fuentes. |
| `scripts/` | `check_docs.py` y `check_sdd.py` (validadores documentales) y `exportar_mapa_manta.py` (regenera el fixture de Manta; no ejecutar sin fuente registrada). |
| `tests/` | Pruebas `unittest`. Catálogo de escenarios en [pruebas](../docs/calidad/pruebas.md). |
| `pyproject.toml` | Paquete `navira` y dependencias; `[test]` añade la dependencia de pruebas HTTP. |
| `.env.example` | Variables de entorno de ejemplo, con valores ficticios. |

El dominio no importa FastAPI ni SDKs de AWS. Las capas y dependencias se describen en [módulos backend](../docs/arquitectura/modulos/backend.md) y en la guía para agentes [.agents/backend.md](../.agents/backend.md).

## Especificaciones y documentación

- Arquitectura y límites: [arquitectura](../docs/arquitectura/arquitectura.md), [módulos backend](../docs/arquitectura/modulos/backend.md).
- Contratos: [API](../docs/arquitectura/contratos/api.md), [eventos](../docs/arquitectura/contratos/eventos.md), [datos](../docs/dominio/datos.md).
- Reglas y dominio: [reglas del juego](../docs/dominio/reglas-juego.md), [ODDD](../docs/dominio/ODDD.md), [mapa Manta](../docs/dominio/mapa-manta.md).
- Especificaciones: [SPEC-001 mundo y simulación](../docs/metodo/especificaciones/SPEC-001-mundo-simulacion.md), [SPEC-002 motor de paso](../docs/metodo/especificaciones/SPEC-002-motor-paso.md), [SPEC-005 AWS y evaluación](../docs/metodo/especificaciones/SPEC-005-aws-evaluacion.md).
- Pruebas: [pruebas](../docs/calidad/pruebas.md) y guía [.agents/pruebas.md](../.agents/pruebas.md).
- Decisiones relevantes: [ADR-008](../docs/arquitectura/decisiones/0008-simulacion-estocastica-reproducible.md), [ADR-015](../docs/arquitectura/decisiones/0015-control-local-de-demo.md), [ADR-016](../docs/arquitectura/decisiones/0016-mapa-maplibre-openfreemap.md).
