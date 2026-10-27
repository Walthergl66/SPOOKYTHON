---
paths:
  - "docs/**"
---
# Documentación y trazabilidad

Fuentes: [SDD](../../docs/metodo/SDD.md), [continuidad](../../docs/metodo/continuidad.md), [plantilla de cambio](../../docs/metodo/plantillas/cambio.md), [cambios](../../docs/seguimiento/cambios.md).

- Ubicación canónica: `docs/`. No crear otra carpeta documental ni duplicar contratos: enlazar al documento propietario.
- Todo `.md` nuevo se agrega al índice de `docs/README.md` (y al de su carpeta si existe, p. ej. ADR o especificaciones).
- Cada tarea significativa agrega una entrada `CAM-NNN` en `docs/seguimiento/cambios.md` con la plantilla de cambio. Verificar el último ID real con `rg` sobre `docs/seguimiento/cambios.md`, porque el archivo no está en orden numérico, y usar el siguiente correlativo.
- Actualizar `docs/seguimiento/estado-actual.md` con hechos reales y el siguiente paso exacto, también si la tarea queda interrumpida.
- Conservar IDs (CAM, ADR, P-NN, T-NN, SPEC) e historial; las preguntas resueltas se marcan, no se borran.
- No modificar `docs/referencias/reto-original.md`. `docs/referencias/plan-previo.md` no es el plan vigente (usar `docs/seguimiento/plan-implementacion.md`).
- Una errata no requiere ADR; un cambio duradero de arquitectura, contrato, regla o alcance sí (`docs/arquitectura/decisiones/`, plantilla de decisión).
- No marcar una SPEC `verificada` sin criterios completos, CAM existente y reporte de evidencia; separar previsto, implementado y verificado.
- Sin secretos ni credenciales en ejemplos. Distinguir requisito del reto, decisión de diseño y supuesto.
- Al cerrar, ejecutar `python3 backend/scripts/check_docs.py` y `python3 backend/scripts/check_sdd.py` y reportar la salida real.
