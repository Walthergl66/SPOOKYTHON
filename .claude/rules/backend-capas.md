---
paths:
  - "backend/src/navira/**"
---
# Capas y contratos del backend

Fuentes: [arquitectura](../../docs/arquitectura/arquitectura.md), [módulos backend](../../docs/arquitectura/modulos/backend.md), [contrato HTTP](../../docs/arquitectura/contratos/api.md).

- Dirección de dependencias: `domain` no importa nada del proyecto; `routing` y `player` dependen de `domain`; `application` orquesta y define los puertos; `api` y `adapters` dependen de contratos internos; el núcleo nunca importa adaptadores.
- Los puertos (p. ej. `RepositorioSnapshots`, `RepositorioOrdenes`) se definen en `application`; las implementaciones (memoria, futuro DynamoDB) viven en `adapters/`.
- `main.py` solo ensambla implementaciones concretas y arranca componentes; sin lógica de simulación.
- Los controladores HTTP/WebSocket traducen transporte a casos de uso: nada de reglas, búsqueda de rutas ni resolución dentro de `api/`.
- No importar FastAPI, boto3 ni esquemas HTTP desde `domain`, `routing`, `simulation` o `application`.
- `POST /paso` conserva nombre, método, campos y cuerpo de éxito (`{"siguienteNodo": ...}`); exige `x-api-key` y debe responder en menos de 500 ms (R-11). Nunca responder con un turno anterior para ocultar errores.
- Errores de `/paso`: 401 credencial ausente/incorrecta, 422 esquema inválido, 404 sobreviviente inexistente, 409 turno/fase/posición incompatible, 503 estado o mapa no disponible o `NAVIRA_API_KEY` sin configurar.
- Las rutas de panel y juego no usan la clave maestra; las de mutación del juego validan `Origin` del mismo host y cookie propietaria. Sesión: errores 403/409/410 según el contrato.
- La proyección observable omite dormidos, semilla y estado RNG; cookie de sesión solo `HttpOnly; Secure; SameSite=Strict`.
- Una tarea, un coordinador: no añadir workers ni caché como fuente de verdad. No afirmar durabilidad de los adaptadores en memoria.
- Un cambio de contrato o de responsabilidad de módulo actualiza `docs/arquitectura/contratos/api.md` o `docs/arquitectura/modulos/backend.md` y registra CAM.
