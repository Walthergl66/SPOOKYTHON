# ADR-026 — Aplanado de `backend/src` y empaquetado con setuptools

Fecha: 2026-10-26 (Ecuador continental).
Estado: sustituida por [ADR-027](0027-reversion-del-aplanado-de-backend.md) (CAM-069). El aplanado y setuptools se revirtieron; este texto es antecedente histórico.
Origen: durante el lote 1 de migración a Clean Architecture ([ADR-025](0025-agentes-de-proyecto-y-clean-architecture.md)) se comprobó que, con `hatchling`, la instalación editable copiaba archivos a `site-packages` en lugar de apuntar a `src/`, y que el código exigía `--app-dir src` o `PYTHONPATH=src`.

## Contexto y restricciones

- [ADR-024](0024-backend-y-frontend-por-carpeta.md) dejó el paquete en `backend/src/navira/`.
- El nombre importable debe seguir siendo `navira` (`uvicorn navira.main:app`, `python -m navira.simulador_demo`).
- No debe cambiar el contrato de `POST /paso`, la API key ni el comportamiento del backend.

## Decisión

1. Aplanar el paquete: el código vive en `backend/src/` (`domain/`, `application/`, `adapters/`, `api/`, `routing/`, `simulation/`, `main.py`, `demo.py`, etc.), sin la carpeta intermedia `navira/`.
2. Build backend con `setuptools>=68` y `[tool.setuptools] package-dir = {"navira" = "src"}` con los subpaquetes listados. El nombre importable sigue siendo `navira`.
3. Las rutas calculadas desde `__file__` bajan un nivel (`parents[2]` a `parents[1]` en `src/demo.py`, `src/evaluacion_rutas.py` y `src/evaluacion_local.py`).
4. Se retiran `--app-dir src` y `PYTHONPATH=src` de los comandos vigentes.

## Alternativas consideradas

- **Mantener `hatchling`:** descartada; la instalación editable no apuntaba a `src/`.
- **Mantener `src/navira/` y setuptools:** posible, pero la carpeta intermedia era redundante con `package-dir`.
- **Renombrar el paquete a `src`:** descartada; rompería los identificadores `navira.*` y [AGENTS.md](../../../AGENTS.md).

## Consecuencias, límites y costos

- Comandos más cortos: `uvicorn navira.main:app` sin opciones. Verificado: `/salud` responde 200 con `{"estado":"activo","servicio":"navira"}` y `POST /paso` sin clave da 401.
- El texto histórico de CAM y ADR anteriores conserva `src/navira/`.
- El directorio `backend/src/navira/` sobrante (solo un entorno huérfano) se borró con aprobación del usuario; `backend/.venv` sigue funcionando.
- La CI de GitHub no se ha ejecutado con el nuevo empaquetado; no verificado.

## Documentos y módulos propietarios afectados

`backend/pyproject.toml`, `backend/README.md`, `docs/arquitectura/guia-clean-architecture.md`, `docs/arquitectura/modulos/backend.md`, `docs/calidad/pruebas.md`, `.claude/` y `.agents/` (comandos).

## Evidencia de implementación/verificación

CAM-067: suite backend de 178 pruebas correctas, arranque de `uvicorn navira.main:app` sin `--app-dir`, validadores documentales.

## Sustituye / sustituida por

Sustituye parcialmente a [ADR-024](0024-backend-y-frontend-por-carpeta.md), solo en la ruta `backend/src/navira/` (ahora `backend/src/`) y en el sistema de build; el resto de ADR-024 sigue vigente.

Sustituida por [ADR-027](0027-reversion-del-aplanado-de-backend.md).
