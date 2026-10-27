# Evidencia — incorporación PRD/TRD/ODDD/SDD

Fecha: 2026-10-26, Ecuador continental. Cambio: CAM-004. Especificación: [SPEC-006](../../metodo/especificaciones/SPEC-006-metodologia.md). Esta evidencia verifica la metodología documental y sus utilidades, no funcionalidades del juego.

## Auditoría y alcance

Se revisaron instrucciones, índice, documentos del proyecto y propuesta del usuario. Se conservan `docs/`, decisiones, stack y modos. ODDD se interpreta como OO + DDD porque el usuario lo confirmó durante esta tarea. La aplicación, mapa, AWS, Budget, rendimiento y remoto no estaban verificados y no se implementaron aquí.

Se detectó que la ruta antigua `docs/PLAN_IMPLEMENTACION.md` ya no existe al comprobar el árbol actual. Se corrigen las afirmaciones vigentes sobre ese alias sin recrear otra carpeta documental; el plan histórico permanece en `docs/referencias/plan-previo.md`. No se atribuye esa ausencia a una acción del usuario sin evidencia.

El archivo de instrucciones encontrado para esta integración es `AGENTS.md`. No se crean archivos Claude, hooks, skills, agentes o comandos ficticios por seguir la plantilla. Los validadores son scripts Python ejecutables con biblioteca estándar.

## Comandos ejecutados — primera pasada

| Comando | Resultado observado |
|---|---|
| `python3 scripts/check_docs.py` | Exit 0; 51 Markdown en `docs/`, 53 archivos comprobados. |
| `python3 scripts/check_sdd.py` | Exit 0; seis SPEC con referencias y trazabilidad válidas; SPEC-006 aún figuraba implementada. |
| `python3 -m unittest discover -s tests -p 'test_check_sdd.py' -v` | Exit 0; ocho pruebas correctas. |
| Parseo con `ast.parse` de script y pruebas | Sintaxis válida. |
| Comparación de propuesta SDD con adjunto | Copia íntegra, igualdad exacta del cuerpo. |

El primer conteo no incluye este reporte, creado después. Pasada de cierre ejecutada: `check_docs.py` correcto con 52 Markdown en `docs/` y 54 archivos comprobados; `check_sdd.py` correcto con seis SPEC y SPEC-006 verificada; el comando enfocado `python3 scripts/check_sdd.py --spec SPEC-004` devolvió correctamente SPEC-004 lista; ocho regresiones volvieron a pasar. Todos finalizaron con exit 0. Resumen vigente en [estado actual](../../seguimiento/estado-actual.md).

## Qué protegen las ocho regresiones

Aceptan metadatos válidos y verificación con CAM/reporte; rechazan requisito desconocido, tarea desconocida, criterio con prueba no declarada, verificación sin evidencia, matriz divergente y requisito sin especificación. Usan un repositorio temporal aislado y no alteran documentos reales para simular errores.

## Revisión de criterios

- CA-006-01: cuatro documentos con responsabilidades diferenciadas e índice actualizado.
- CA-006-02: seis SPEC, 22 requisitos PRD/TRD y referencias a tareas/CA/pruebas; comprobador y pruebas negativas ejecutados.
- CA-006-03: AGENTS y continuidad mantienen lectura inicial, flujo proporcional y autorización persistente. La revisión de este criterio es editorial, no una prueba automatizada del comportamiento futuro de un agente.
- CA-006-04: se conserva historial y se registra CAM-004, ADR-005, tareas metodológicas y punto de reanudación. La pasada de cierre comprobó comandos y enlaces con resultado correcto.

## Límites

No se ejecutaron pruebas de producto, benchmarks, frontend, rutas AWS o recuperación real. No se validan URLs externas ni el significado de toda la prosa automáticamente. Un reporte existente puede contener errores; la revisión y pruebas de aplicación siguen siendo necesarias. Las SPEC-001 a SPEC-005 permanecen listas para tareas autorizadas, sin código ni verificación funcional.
