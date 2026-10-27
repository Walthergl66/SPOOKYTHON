---
description: Redacta una entrada CAM-NNN en docs/seguimiento/cambios.md y actualiza el estado actual
argument-hint: <descripción breve del cambio>
---
Registra un cambio de Navira. Fuentes: [docs/seguimiento/cambios.md](../../docs/seguimiento/cambios.md), [docs/metodo/plantillas/cambio.md](../../docs/metodo/plantillas/cambio.md), [docs/seguimiento/estado-actual.md](../../docs/seguimiento/estado-actual.md). Objetivo del cambio: $ARGUMENTS

1. Calcula el siguiente ID: el mayor `CAM-NNN` de `docs/seguimiento/cambios.md` más uno. El orden del archivo no es estrictamente numérico, así que usa `grep -o '^## CAM-[0-9]*' docs/seguimiento/cambios.md | sort | tail -1`.
2. Lee la plantilla y las dos últimas entradas para copiar el formato (encabezado `## CAM-NNN — Título`).
3. Redacta el borrador con los campos de la plantilla, usando `git status` y `git diff --stat` para archivos reales. Solo registra como validación lo que se ejecutó de verdad; lo demás va en "no ejecutada y causa". Sin secretos.
4. Muestra el borrador y pide confirmación. Añádelo a `docs/seguimiento/cambios.md` solo si el usuario confirma en esta conversación.
5. Tras añadirlo, actualiza `docs/seguimiento/estado-actual.md` (hechos reales y "Próxima acción concreta" exacta).
6. Si cambió documentación, sugiere `python backend/scripts/check_docs.py` y `python backend/scripts/check_sdd.py`.
