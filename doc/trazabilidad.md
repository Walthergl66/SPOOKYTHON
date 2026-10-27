# Trazabilidad de requisitos, tareas y pruebas

Estado: referencias documentales; no representa funcionalidad implementada. Los requisitos se definen solo en [PRD](PRD.md) y [TRD](TRD.md). Cada SPEC contiene sus criterios CA, tareas y pruebas; [plan](plan-implementacion.md) conserva estado de tareas y [pruebas](pruebas.md) define los IDs T.

| Especificación | Requisitos cubiertos | Tareas/pruebas y situación |
|---|---|---|
| [SPEC-001](especificaciones/SPEC-001-mundo-simulacion.md) | PRD-01, PRD-02, TRD-03, TRD-04, TRD-05, TRD-09, TRD-11, TRD-12 | Implementación parcial; CAM-023/024 cubren semilla y replay; CAM-057 agrega densidad sintética espacial y cierres viales reproducibles (T-28/T-29 parcial). P-07/P-09 oficiales, recuperación durable y T-24 integral pendientes. |
| [SPEC-002](especificaciones/SPEC-002-motor-paso.md) | PRD-03, PRD-09, PRD-10, TRD-01, TRD-02, TRD-05, TRD-06, TRD-09, TRD-12, TRD-14 | CAM-033/034 implementan núcleo/pronóstico; CAM-035 compara 27 pares; CAM-058 activa la política temporal riesgo-primero; CAM-059 agrega cruce futuro, salida de emergencia y reuso de ruta panel/acción (T-31/T-32/T-33); CAM-060 mantiene terminal evacuación (T-34); CAM-061 coordina siguientes pasos bajo un snapshot compartido (T-35 parcial). T-22 ampliada, T-11 HTTP, reglas oficiales y latencia bajo carga siguen pendientes; resultados sintéticos no prueban mejora universal. |
| [SPEC-003](especificaciones/SPEC-003-panel-vivo.md) | PRD-04, PRD-06, TRD-05, TRD-06, TRD-07, TRD-09 | CAM-031 verifica mapa/proyección; CAM-032 verifica snapshots WebSocket/heartbeat y CAM-052 agrega seguimiento del contexto al iniciar otro run local. Juego, auditoría accesible integral, despliegue y SPEC completa pendientes. |
| [SPEC-004](especificaciones/SPEC-004-juego-humano.md) | PRD-05, PRD-06, TRD-03, TRD-04, TRD-05, TRD-06, TRD-09, TRD-12 | CAM-036/037 implementan parte de P4B-01/02; CAM-038 inicia P4B-03/T-19; CAM-039/040 integran aparición, orden, deadline y runner local; CAM-041 muestra cuenta atrás, CAM-042 sugerencia de radio, CAM-043 recuperación local de sesión por cookie, CAM-045 accesibilidad parcial y CAM-046 cumple T-25 localmente. TLS, persistencia/reinicio, revocación productiva y T-14/T-15/T-19 integral pendientes. |
| [SPEC-005](especificaciones/SPEC-005-aws-evaluacion.md) | PRD-06, PRD-07, PRD-08, TRD-02, TRD-06, TRD-08, TRD-10, TRD-11 | Metadatos de SPEC; AWS pendiente. |
| [SPEC-006](especificaciones/SPEC-006-metodologia.md) | TRD-13 | Método documental; ver evidencia de la propia SPEC. |
| [SPEC-007](especificaciones/SPEC-007-panel-operador-local.md) | PRD-06, TRD-06, TRD-07 | CAM-050/T-26 prueban arranque, control y lectura local del mismo run; despliegue y control de operador productivo fuera de alcance. |
| [SPEC-008](especificaciones/SPEC-008-mapa-cartografico-3d.md) | PRD-01, PRD-04, TRD-07, TRD-09 | CAM-051/052/053/054/055/056/P4-04/T-27 integran cartografía, fichas animadas, cambio de run y ventana visual/interactiva ~15 km por lado; la extensión solo afecta al basemap, no equivale a límite administrativo ni a cobertura del grafo. |

## Cadena de ejemplo

`PRD-05 → SPEC-004 → CA-004-03 → P4B-02 → T-14 → CAM-037 → tests/test_ordenes_juego.py`.

La evidencia CAM-037 es parcial: valida aceptación y acuse local, pero aún no demuestra deadline, cierre atómico compartido ni consumo por el resolutor. Para la intervención metodológica: `TRD-13 → SPEC-006 → M0-01..04 → T-20/T-21 → CAM-004 → reporte documental`.

`python3 scripts/check_sdd.py` comprueba que todos los requisitos tengan SPEC, referencias a tareas/pruebas existan, criterios usen pruebas declaradas, esta matriz coincida con metadatos y una SPEC verificada tenga CAM/evidencia. No demuestra cobertura ejecutada o semántica del requisito. Si cambia un ID, actualizar sus referencias conservando la historia de sustitución.
