# Backend Navira (`backend/src/navira`)

Documentación de referencia: [arquitectura](../docs/arquitectura/arquitectura.md), [módulos backend](../docs/arquitectura/modulos/backend.md) (responsabilidades y pruebas por módulo), [ODDD](../docs/dominio/ODDD.md) (lenguaje e invariantes) y [contrato API](../docs/arquitectura/contratos/api.md).

## Carpetas

| Ruta | Rol |
|---|---|
| `domain/` | Grafo (`mapa.py`) y entidades/estado (`modelo.py`). Sin I/O. |
| `routing/` | Dijkstra de respaldo, búsqueda temporal acotada y predicción observable. |
| `simulation/` | Coordinador de turnos, reloj y resolución (`resolver.py`). |
| `application/` | Casos de uso y puertos: decidir paso, panel, juego, órdenes, snapshots, relojes locales. |
| `adapters/` | Implementaciones en memoria de los puertos (snapshots, mapas, órdenes). |
| `api/` | FastAPI: rutas, esquemas, autenticación, WebSocket. |
| `main.py` | Ensamblaje de dependencias; `demo.py` ensambla el modo demo local. |
| `simulador_demo.py`, `carga_http.py`, `evaluacion_local.py`, `evaluacion_rutas.py` | Herramientas locales de simulación y medición. |

## Reglas clave

- Dependencias: `domain` no importa nada del proyecto ni FastAPI/boto3; `routing` y `application` dependen del dominio; `api` y `adapters` dependen de contratos internos; el núcleo nunca importa adaptadores.
- `application` define los puertos; `adapters` los implementan.
- `main.py` solo ensambla; sin lógica de simulación ni controladores con reglas.
- Una única validación de movimientos para humanos y automáticos.
- Ningún endpoint mueve posiciones: solo el coordinador avanza el turno.
- No exponer zombies dormidos ni estado RNG privado (panel, WebSocket, routing, respuestas).
- `POST /paso` conserva su contrato, exige API key y responde en menos de 500 ms.
- Un cambio de responsabilidad requiere actualizar `docs/arquitectura/modulos/backend.md` y registrar el cambio en `docs/seguimiento/cambios.md`.
