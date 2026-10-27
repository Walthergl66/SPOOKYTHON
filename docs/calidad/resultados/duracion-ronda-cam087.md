# Evidencia CAM-087 — Duración completa de la ventana local

Fecha: 2026-10-27, Ecuador continental.

## Objetivo

Evitar que el evaluador local termine antes de la duración solicitada cuando el mundo llega a un estado terminal antes de completar sus slots de cadencia. La ventana se conserva sin fabricar turnos, movimientos o solicitudes HTTP posteriores al cierre.

## Cambio

`python -m navira.evaluacion_local` mantiene la duración objetivo `turnos × periodo_segundos`. Si la partida finaliza o ya no tiene sobrevivientes activos, registra cada slot restante como ocioso (`solicitudes: 0`) y espera hasta completar la ventana. El JSON distingue `turnosEjecutados` (rondas reales), `slotsCadenciaSinActividad`, `slotsSinActividad`, `duracionObjetivoSegundos`, `duracionTotalSegundos` y `duracionObjetivoCumplida`.

Los intervalos ociosos solo completan el reloj de la evaluación. No aumentan carga HTTP, no mueven actores y no cuentan como rondas jugadas. Por ello, esta mejora no convierte una partida que termina pronto en 150 turnos activos, ni demuestra carga sostenida durante toda la ventana.

## Verificación

- `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_evaluacion_local.py' -v`: 6 pruebas pasan; incluye una partida ya finalizada al inicio, tres slots ociosos, cero solicitudes y duración objetivo cumplida.
- `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py'`: 215 pruebas pasan en 64,291 s.
- `python3 backend/scripts/check_docs.py`: correcto (117 Markdown/119 archivos).
- `python3 backend/scripts/check_sdd.py`: ocho SPEC con trazabilidad estructural válida; la salida informa estados documentales, no comportamiento.
- `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`: 8/8.
- `python3 -m compileall -q backend/src/navira` y `git diff --check`: correctos.

## Límites y siguiente paso

La prueba de ventana no sustituye T-11: faltan escenarios oficiales, repeticiones, rondas con turnos activos suficientes y medición contra el entorno de evaluación. Para resolver la brecha de actividad hay que ajustar el fixture/configuración de evaluación para que el mundo permanezca activo durante la ronda oficial, preservando las reglas terminales; esta mejora no impide su cierre natural.
