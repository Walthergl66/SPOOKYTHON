# SDD — Desarrollo guiado por especificaciones

Versión: 1. Fecha: 2026-10-26. Estado: proceso incorporado al repositorio. La aplicación todavía no está implementada. Adaptación de la [propuesta aportada por el usuario](referencias/propuesta-sdd.md), usando `doc/` y los documentos actuales. Referencia conceptual adicional: [Spec-Driven Development de GitHub Spec Kit](https://github.com/github/spec-kit/blob/main/spec-driven.md); no se instala Spec Kit ni se afirman sus automatizaciones como disponibles.

## Responsabilidad de cada documento

| Documento | Pregunta que responde |
|---|---|
| [PRD](PRD.md) | ¿Qué necesita el producto y por qué? |
| [TRD](TRD.md) | ¿Qué condiciones técnicas debe cumplir? |
| [ODDD](ODDD.md) | ¿Qué conceptos, invariantes y límites tiene el dominio? |
| [Especificación](especificaciones/README.md) | ¿Qué comportamiento y aceptación corresponden a esta funcionalidad? |
| [Arquitectura](arquitectura.md) y ADR | ¿Cómo se estructura y por qué? |
| [Plan](plan-implementacion.md) | ¿Qué tareas se ejecutan y en qué orden? |
| [Cambios](cambios.md) y estado | ¿Qué ocurrió, qué se verificó y qué falta? |

Instrucciones actuales del usuario y requisitos del reto son fuentes de origen. PRD/TRD y especificaciones refinan esos requisitos, no los sustituyen por conveniencia. Arquitectura regula diseño; evidencia describe implementación real. Ante conflicto, registrar la discrepancia y corregir la fuente propietaria con trazabilidad.

## Ciclo de trabajo

1. **Specify:** identificar alcance, fuente, requisitos PRD/TRD, casos límite, pendientes y criterios CA verificables. Enlazar reglas/contratos en vez de copiarlos.
2. **Plan:** asociar tareas existentes del roadmap, módulos y pruebas T. Definir pasos pequeños y el primer resultado ejecutable.
3. **Implement:** ejecutar solo lo autorizado. Mantener contratos, invariantes y separación de capas; no crear funcionalidades por completar una plantilla.
4. **Verify:** ejecutar pruebas pertinentes y criterios. Guardar comando, resultado, versiones y limitaciones. Los validadores documentales no sustituyen pruebas de aplicación.
5. **Document:** actualizar especificación, tareas, documentos propietarios, CAM y estado. Incorporar nuevos riesgos o ADR.

Un cambio trivial puede usar un registro breve dentro de la tarea/CAM con objetivo, criterio, prueba y especificación existente. No exige archivo nuevo. Un cambio que altera contrato, reglas, varios módulos o alcance sí actualiza una especificación completa y su plan.

## Estados de especificación

| Estado | Significado |
|---|---|
| `borrador` | Hay propuestas o preguntas no resueltas; no implica autorización de cambios amplios. |
| `en-revision` | Se contrastan alcance y criterios. |
| `lista` | Comportamiento suficientemente definido para tareas autorizadas; pendientes locales explícitos. |
| `implementada` | Existe código/documentación objetivo; aún falta completar evidencia. |
| `verificada` | Criterios comprobados con evidencia y CAM relacionados. |
| `sustituida` | Una especificación posterior la reemplaza con enlace trazable. |

El estado `lista` no concede permisos externos, ni requiere volver a pedir aprobación para cada paso rutinario ya autorizado. La autorización humana existente persiste. Preguntar solo si falta información esencial o hay una ampliación real no autorizada. Los supuestos configurables permiten avanzar sin fingir aclaraciones oficiales.

## Formato y trazabilidad

Cada SPEC tiene metadatos `ID`, `Estado`, `Requisitos`, `Tareas`, `Pruebas`, `Cambio` y `Evidencia`. Criterios de aceptación estables `CA-NNN-NN` se vinculan a pruebas T. La [matriz](trazabilidad.md) enlaza requisitos con SPEC; la propia SPEC detalla tareas/CA/pruebas. Estados de la app permanecen pendientes hasta ejecutarse.

Para una SPEC verificada, `Cambio` referencia un CAM existente y `Evidencia` es una ruta relativa a su archivo con resultados. Un archivo existente no demuestra que los resultados sean ciertos: la revisión humana/agente y las pruebas reales siguen siendo necesarias.

## Comandos disponibles

```bash
python3 scripts/check_docs.py
python3 scripts/check_sdd.py
python3 scripts/check_sdd.py --spec SPEC-004
python3 -m unittest discover -s tests -p 'test_check_sdd.py'
```

`check_sdd.py` comprueba IDs, referencias, metadatos, criterios, cobertura documental y presencia de evidencia al declarar verificación. No ejecuta zombies, no mide latencia y no prueba seguridad de la app. El comando enfocado limita la salida a una SPEC, manteniendo comprobación global de integridad.

No se crean hooks, skills, subagentes o archivos para otras herramientas sin una necesidad real. El procedimiento es portable mediante Markdown y Python estándar. Incorporación obligatoria: [AGENTS.md](../AGENTS.md). Plantillas: [especificación](plantillas/especificacion.md) y [plan de cambio](plantillas/plan-cambio.md).
