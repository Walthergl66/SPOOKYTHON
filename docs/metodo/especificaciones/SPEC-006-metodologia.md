# SPEC-006 — PRD, TRD, ODDD y SDD

ID: SPEC-006
Estado: verificada
Requisitos: TRD-13
Tareas: M0-01, M0-02, M0-03, M0-04
Pruebas: T-20, T-21
Cambio: CAM-004
Evidencia: ../../calidad/resultados/verificacion-sdd.md

## Objetivo y alcance

Incorporar las cuatro prácticas solicitadas sobre el proyecto real, preservando `docs/`, stack, modos y decisiones. El usuario confirmó ODDD como OO + DDD. Esta SPEC implementa metodología/documentación y sus comprobadores; no autoriza ni declara terminadas funcionalidades de producto.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-006-01 | PRD, TRD, ODDD y SDD existen, tienen responsabilidades claras y están enlazados desde el índice. | T-20 |
| CA-006-02 | SPEC funcionales enlazan requisitos, tareas, criterios y pruebas definidos; el validador detecta referencias inválidas y verificación sin evidencia. | T-21 |
| CA-006-03 | `AGENTS.md` y continuidad aplican SDD proporcional, lectura de `docs/` y autorización existente sin aprobaciones repetidas innecesarias. | T-20, T-21 |
| CA-006-04 | Estado, plan, ADR y CAM conservan lo anterior y declaran aplicación/AWS pendientes; comandos documentados funcionan y el ciclo de esta SPEC queda registrado. | T-20, T-21 |

## Plan y verificación

M0-01 auditar documentación y fuente; M0-02 crear requisitos/modelo/SPEC/plantillas; M0-03 comprobador estructural y pruebas negativas; M0-04 validar, revisar coherencia y registrar evidencia/CAM/estado. Comparar la copia de la propuesta SDD con el adjunto. No crear configuración de otras herramientas, instalar skills o delegar por el solo hecho de existir la metodología.

Comandos, revisión de criterios y límites se conservan en el [reporte](../../calidad/resultados/verificacion-sdd.md). Los criterios editoriales se revisaron manualmente; el comprobador solo cubre estructura, no comprensión semántica ni resultados de juego.
