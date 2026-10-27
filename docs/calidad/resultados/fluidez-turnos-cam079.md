# Evidencia CAM-079 — Fluidez de turnos y movimientos

Fecha: 2026-10-27, hora local Ecuador continental.

## Origen y alcance

Solicitud del usuario para reducir la lentitud visual de la partida automática, con transiciones más fluidas y conservando las acciones que corresponden a cada personaje. Se ajusta la velocidad de la demo local y la interpolación frontend; el resolutor, el orden de turnos, las reglas y el reloj de evaluaciones oficiales no cambian.

## Cambios

- La demo local inicia a 4× (intervalo objetivo de 500 ms) y conserva los controles 1×/2×/4×.
- La interpolación usa el periodo nominal de turno dividido por la velocidad seleccionada.
- El mapa mantiene animaciones confirmadas durante snapshots de fase sin nuevos movimientos; una trayectoria solo se crea desde dos snapshots consecutivos públicos. Actores terminales o que ya no aparecen dejan de animarse y el mapa usa el estado remoto más reciente.
- Respeto de `prefers-reduced-motion` conservado.
- El reloj mantiene sus rondas completas, seriales y con espera de CPU mínima; si el cómputo excede el intervalo objetivo, se retrasa el próximo turno y no se descarta ninguno.

## Verificación

- `cd frontend && npm test -- --run`: 83 pruebas correctas en 7 archivos.
- `cd frontend && npm run build`: correcto; Vite conserva la advertencia existente de chunk cartográfico mayor a 500 kB.
- `cd backend && PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_velocidad_simulador -v`: 5 pruebas correctas. El Python de sistema no tiene FastAPI; el entorno `/tmp/navira-env` sí permitió ejecutar el conjunto enfocado.
- `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py'` desde `backend/`: 212 pruebas correctas. El conjunto imprime un mensaje CLI de argumento inválido como parte de un caso esperado.
- `python3 backend/scripts/check_docs.py`: correcto, 109 Markdown y 111 archivos comprobados.
- `python3 backend/scripts/check_sdd.py`: correcto, ocho SPEC con trazabilidad estructural válida; `SPEC-007` verificada con este CAM/evidencia.
- `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`: 8 pruebas correctas. `git diff --check`: correcto.
- Smoke local: `POST /demo/simulador/velocidad` same-origin devolvió `estado=activa`, `runId=navira-demo-945a7cbab29c4776be336ccb6fd7bdb3`, `turno=172`, `velocidad=4.0`, sin error.
- Revisión del navegador local: el run siguió activo, el control mostró 4× seleccionado y la cartografía cargó con atribución OSM. Esta inspección no midió fotogramas ni cadencia sostenida, y se realizó antes de añadir la adaptación a la cadencia observada.
- Tres lecturas de `GET /demo/simulador` con intervalos de espera de 1 s observaron 1,361 s y 1,172 s entre incrementos de turno bajo la partida y el equipo locales. La demo, por tanto, no sostuvo el objetivo de 0,5 s en esta muestra; el frontend ahora estima el periodo de turnos y prolonga cada transición activa para acompañarlo. Es una muestra breve, no benchmark ni garantía.

## Límites

La duración 4× es un objetivo local, no una garantía si una ronda tarda más de 500 ms. No se ejecutó una inspección visual manual ni medición sostenida bajo carga. La interpolación no modifica el mundo ni permite predecir movimientos no confirmados. Esta mejora no valida rutas para emergencias reales.
