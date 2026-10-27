# ADR-022 — Organización de docs/ por temas con índice general

Fecha: 2026-10-26 (Ecuador continental).
Estado: aceptada e implementada localmente (CAM-064).
Origen: el usuario pidió ordenar `docs/` en carpetas, con todo su contenido y especificaciones, y que `docs/README.md` indique dónde está cada documento.

## Contexto y restricciones

- `docs/` era una carpeta plana con unos 90 Markdown: producto, dominio, arquitectura, método, seguimiento, pruebas y referencias convivían en el mismo nivel, con subcarpetas parciales (`contratos/`, `decisiones/`, `especificaciones/`, `flujos/`, `modulos/`, `plantillas/`, `resultados/`).
- ADR-004 fija `docs/` como ubicación canónica y exige un índice que enlace todo el contenido.
- Los documentos de `referencias/` son fuentes del usuario o históricas y no deben reescribirse para adaptarse al código (AGENTS.md, sección 5).

## Decisión

Agrupar los documentos por tema y mantener un único índice general en `docs/README.md`:

| Carpeta | Contenido |
|---|---|
| `producto/` | PRD, TRD y contexto. |
| `dominio/` | ODDD, reglas del juego, modos, datos, fixture de Manta y `flujos/`. |
| `arquitectura/` | Arquitectura, algoritmos, `contratos/`, `modulos/` y `decisiones/` (ADR). |
| `metodo/` | SDD, trazabilidad, continuidad, `especificaciones/` (SPEC) y `plantillas/`. |
| `seguimiento/` | Estado actual, historial de cambios (CAM), pendientes y plan. |
| `calidad/` | Pruebas T-NN y `resultados/`. |
| `operacion/` | Infraestructura, seguridad y costos. |
| `referencias/` | Reto original y propuestas históricas, sin cambios de contenido. |

Los IDs (CAM, ADR, SPEC, P-NN, T-NN) y el contenido de cada documento no cambian. Los enlaces relativos y las rutas citadas en documentos, configuración y validadores se actualizan a la nueva ubicación.

## Alternativas consideradas

- **Mantener la carpeta plana con un índice más largo:** no resuelve la búsqueda por tema y deja las subcarpetas parciales.
- **Renombrar también los documentos por número de orden:** cambia nombres citados en toda la historia y no aporta más que el índice.
- **Volver a `doc/`:** descartado por decisión del usuario, que trabaja con `docs/`.

## Consecuencias, límites y costos

- Las referencias históricas dentro de `seguimiento/cambios.md` y de los ADR conservan texto antiguo cuando no son enlaces; los enlaces sí están actualizados.
- `scripts/check_docs.py` y `scripts/check_sdd.py` dependen de la ubicación de cada documento; un movimiento futuro exige actualizar sus rutas.
- Cada documento nuevo debe colocarse en su carpeta temática y enlazarse en el índice general.

## Supuestos y pendientes relacionados

- Ninguno de producto o alcance. No cambia requisitos del reto.

## Documentos y módulos propietarios afectados

`docs/README.md`, `docs/metodo/SDD.md` (rutas), `scripts/check_docs.py`, `scripts/check_sdd.py`, `tests/test_check_sdd.py`, `AGENTS.md`, `README.md` y la configuración de agentes ([ADR-023](0023-configuracion-de-agentes.md)).

## Evidencia de implementación/verificación

CAM-064: `python3 scripts/check_docs.py` (91 Markdown en `docs/`), `python3 scripts/check_sdd.py` (8 especificaciones) y `python -m unittest discover -s tests -p 'test_check_sdd.py'` (8 pruebas) correctos.

## Sustituye / sustituida por

No sustituye a ADR-004; la complementa con la estructura por temas.
