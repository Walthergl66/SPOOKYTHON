# ADR-028 — Configuración de seguridad leída una vez e inyectada

Fecha: 2026-10-26 (Ecuador continental).
Estado: aceptada e implementada localmente (CAM-071).
Origen: paso B4b de la [guía de Clean Architecture](../guia-clean-architecture.md), tras la revisión de arquitectura y seguridad.

## Contexto y restricciones

- `api/` leía `NAVIRA_API_KEY`, `NAVIRA_COOKIE_SECURE` y `NAVIRA_LOCAL_DEMO_CONTROL` desde `os.environ` en cada petición; el comportamiento dependía del entorno del proceso y las pruebas debían parchear `os.environ`.
- No debe cambiar el contrato de `POST /paso`, la API key ni los códigos HTTP.

## Decisión

1. `main.py` (`_crear_app_configurada`) lee el entorno una sola vez y construye `ConfiguracionSeguridad` (dataclass congelada; `api_key` con `repr=False`).
2. `crear_app(seguridad=...)` asigna `app.state.seguridad`. Sin valor, la configuración es la más cerrada: sin clave `POST /paso` responde 503, la cookie es `Secure` y el control de demo local queda apagado.
3. `api/` y `evaluacion_local.py` no leen `os.environ`; `evaluacion_local.py` pasa su clave de forma explícita.

## Alternativas consideradas

- **Leer el entorno en cada petición (estado previo):** descartada; acopla la API al proceso y obligaba a parchear `os.environ` en pruebas.

## Consecuencias, límites y costos

- Rotar la clave o cambiar los flags exige reiniciar el proceso (limitación operativa).
- Las pruebas usan `seguridad=...` en lugar de `patch.dict`.
- No hay gestión de secretos productiva ni TLS; sigue fuera de alcance.

## Documentos y módulos propietarios afectados

[Módulos backend](../modulos/backend.md), [contrato de API](../contratos/api.md), [guía de Clean Architecture](../guia-clean-architecture.md).

## Evidencia de implementación/verificación

CAM-071: suite backend de 181 pruebas correctas (datos del orquestador); revisión de seguridad sin hallazgos medios o altos.

## Sustituye / sustituida por

No sustituye a ninguna ADR. Complementa [ADR-025](0025-agentes-de-proyecto-y-clean-architecture.md).
