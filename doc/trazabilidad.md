# Trazabilidad de requisitos, tareas y pruebas

Estado: referencias documentales; no representa funcionalidad implementada. Los requisitos se definen solo en [PRD](PRD.md) y [TRD](TRD.md). Cada SPEC contiene sus criterios CA, tareas y pruebas; [plan](plan-implementacion.md) conserva estado de tareas y [pruebas](pruebas.md) define los IDs T.

| Especificación | Requisitos cubiertos | Tareas/pruebas y situación |
|---|---|---|
| [SPEC-001](especificaciones/SPEC-001-mundo-simulacion.md) | PRD-01, PRD-02, TRD-03, TRD-04, TRD-05, TRD-09, TRD-11, TRD-12 | Implementación parcial; CAM-023/024 cubren semilla nueva, muestreo, replay local multi-turno y decisión estable por snapshot; recuperación durable y T-24 integral pendientes. |
| [SPEC-002](especificaciones/SPEC-002-motor-paso.md) | PRD-03, PRD-09, TRD-01, TRD-02, TRD-05, TRD-06, TRD-09, TRD-12 | Integración HTTP multi-turno local y cadencia de 2 s parcial (CAM-028/029); T-11 y producto siguen pendientes. |
| [SPEC-003](especificaciones/SPEC-003-panel-vivo.md) | PRD-04, PRD-06, TRD-05, TRD-06, TRD-07, TRD-09 | CAM-031 inicia P4-01 con proyección HTTP de mapa/snapshot y filtrado de dormidos; rutas completas, eventos, reconexión y juego pendiente. SPEC sin verificar. |
| [SPEC-004](especificaciones/SPEC-004-juego-humano.md) | PRD-05, PRD-06, TRD-03, TRD-04, TRD-05, TRD-06, TRD-09, TRD-12 | Metadatos de SPEC; producto pendiente. |
| [SPEC-005](especificaciones/SPEC-005-aws-evaluacion.md) | PRD-06, PRD-07, PRD-08, TRD-02, TRD-06, TRD-08, TRD-10, TRD-11 | Metadatos de SPEC; AWS pendiente. |
| [SPEC-006](especificaciones/SPEC-006-metodologia.md) | TRD-13 | Método documental; ver evidencia de la propia SPEC. |

## Cadena de ejemplo

`PRD-05 → SPEC-004 → CA-004-03 → P4B-02 → T-14 → CAM de implementación → evidencia real`.

El ejemplo todavía no tiene CAM de juego: solo expresa la cadena prevista. Para la intervención actual: `TRD-13 → SPEC-006 → M0-01..04 → T-20/T-21 → CAM-004 → reporte documental`.

`python3 scripts/check_sdd.py` comprueba que todos los requisitos tengan SPEC, referencias a tareas/pruebas existan, criterios usen pruebas declaradas, esta matriz coincida con metadatos y una SPEC verificada tenga CAM/evidencia. No demuestra cobertura ejecutada o semántica del requisito. Si cambia un ID, actualizar sus referencias conservando la historia de sustitución.
