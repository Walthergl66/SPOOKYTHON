# ADR-027 — Reversión del aplanado de `backend/src`

Fecha: 2026-10-26 (Ecuador continental).
Estado: aceptada e implementada localmente (CAM-069).
Origen: decisión del usuario de mantener el paquete en `backend/src/navira/` y el build original con `hatchling`.

## Contexto y restricciones

- [ADR-026](0026-aplanado-backend-y-setuptools.md) aplanó `backend/src/` y cambió a `setuptools` (CAM-067).
- El nombre importable debe seguir siendo `navira`; no debe cambiar el contrato de `POST /paso`, la API key ni el comportamiento.

## Decisión

1. `backend/src/` contiene solo `navira/`, con todo el paquete dentro.
2. El build vuelve a `hatchling` con `packages = ["src/navira"]` (estado de HEAD).
3. Las rutas desde `__file__` vuelven a `parents[2]` en `navira/demo.py`, `navira/evaluacion_rutas.py` y `navira/evaluacion_local.py`.
4. El arranque vigente es `uvicorn navira.main:app --app-dir src`; sin `--app-dir` también funciona.
5. Se conservan B1, B2, B3, F1, F2, F3 y F6.

## Alternativas consideradas

- **Mantener el aplanado:** descartada por el usuario.
- **Mover `main.py` a `src/`:** pendiente de decisión del usuario; hoy `main.py` está dentro de `navira/`.

## Consecuencias, límites y costos

- Se vuelve a usar `--app-dir src` (o `PYTHONPATH=src`) en los comandos.
- El texto histórico de CAM-067 y de ADR-026 conserva el aplanado como antecedente.
- La CI de GitHub no se ha ejecutado con esta estructura; no verificado.

## Documentos y módulos propietarios afectados

`backend/pyproject.toml`, `docs/arquitectura/guia-clean-architecture.md`, `docs/arquitectura/modulos/backend.md`, `docs/calidad/pruebas.md`.

## Evidencia de implementación/verificación

CAM-069: 178 pruebas de backend correctas, mapas resueltos con `parents[2]`, búsquedas de dependencias sin coincidencias (datos del orquestador).

## Sustituye / sustituida por

Sustituye a [ADR-026](0026-aplanado-backend-y-setuptools.md). [ADR-024](0024-backend-y-frontend-por-carpeta.md) vuelve a estar vigente sin la salvedad de ADR-026.
