---
name: navira-cambio-sdd
description: Usar al iniciar un cambio significativo en Navira (código, reglas, contratos o documentación) para seguir el ciclo SDD Specify, Plan, Implement, Verify, Document.
---

# Cambio significativo según SDD

Fuente: [SDD](../../../docs/metodo/SDD.md). Plantillas: [cambio](../../../docs/metodo/plantillas/cambio.md) y [plan de cambio](../../../docs/metodo/plantillas/plan-cambio.md). La documentación vive en `docs/`; su índice es `docs/README.md`.

1. **Leer contexto**: [README](../../../docs/README.md), [estado actual](../../../docs/seguimiento/estado-actual.md), [contexto](../../../docs/producto/contexto.md), [pendientes](../../../docs/seguimiento/pendientes.md) y la SPEC aplicable según el [índice de especificaciones](../../../docs/metodo/especificaciones/README.md).
2. **Specify**: fijar alcance, requisitos PRD/TRD y criterios `CA-NNN-NN` verificables. Enlazar reglas y contratos; no copiarlos. No resolver como confirmado lo que sigue en `pendientes.md`.
3. **Plan**: lista corta de pasos pequeños, tareas del plan, módulos y pruebas T-NN, con el primer resultado ejecutable (plantilla `plan-cambio`).
4. **Implement**: solo lo ya autorizado; respetar capas, contratos e invariantes. Sin funcionalidades extra ni refactors fuera de alcance.
5. **Verify**: ejecutar solo los comandos del área tocada (ver skill `navira-verificar`). Anotar comando, resultado real, fallos y lo no ejecutado.
6. **Document**: añadir el siguiente `CAM-NNN` en [cambios](../../../docs/seguimiento/cambios.md) (mirar el último ID existente), actualizar [estado actual](../../../docs/seguimiento/estado-actual.md) con hechos y siguiente paso exacto, y la SPEC (estado, CA, pruebas). No marcar `verificada` sin evidencia y CAM.
7. **Cambio trivial**: registro breve en el CAM con objetivo, criterio, prueba y SPEC existente; sin archivo nuevo.
8. Un cambio que altera contrato, reglas, varios módulos o alcance exige SPEC completa y plan; si es duradero, crear ADR en `docs/arquitectura/decisiones/` e indexar cualquier `.md` nuevo.

## Comandos reales

- Backend: `cd backend && python -m unittest discover -s tests -p 'test_*.py' -v` (usar el `backend/.venv`).
- Frontend: `cd frontend && npm ci && npm run build`.
- Validadores: `python backend/scripts/check_docs.py`, `python backend/scripts/check_sdd.py`, `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`.
- Shell fish: variables con `env VAR=valor comando`.
