# Evidencia CAM-081 — Incidentes viales siempre activos en demo

Fecha: 2026-10-27 (Ecuador continental). Entorno: pruebas locales, fixture Manta sintético del repositorio; no corresponde a incidentes reales.

## Verificación

- Backend focalizado: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_control_simulador_demo -v` — 8 pruebas correctas; inicio y reinicio con el campo legado falso conservan eventos programados en el snapshot.
- Frontend: `npm test -- --run` — 85 pruebas correctas en 7 archivos.
- Frontend build: `npm run build` — correcto; Vite muestra la advertencia existente de chunk cartográfico mayor a 500 kB.
- Documentación: `python3 backend/scripts/check_docs.py` — 111 Markdown/113 archivos comprobados, correcto. SDD: `python3 backend/scripts/check_sdd.py` — 8 SPEC correctas. Regresiones del validador: `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py' -v` — 8 pruebas correctas. `compileall` y `git diff --check` correctos.

La prueba HTTP envía `eventosCiudad: false` tanto al iniciar como al reiniciar y comprueba que la respuesta del control mantenga el valor activo. La prueba frontend confirma que el cuerpo de inicio no incluye ese campo. Esto verifica el control de demo local; no cambia la configuración explícita de `crear_contexto_demo` usada por evaluaciones/CLI, no mide la calidad del planificador ni simula cierres futuros de una ronda completa.

La inspección del navegador local confirmó que el menú conserva escenario, población e intensidad sin mostrar control de incidentes. El run ya terminado mostrado en el panel registró incidentes aplicados en los turnos 2 y 5.

## Límites operativos

La UI local actualizada por Vite ya no ofrece el selector. El proceso backend que estaba ejecutándose antes de CAM-081 conserva el código anterior mientras mantiene su run finalizado en memoria; debe reiniciarse para que el servidor ignore el campo legado de clientes antiguos. No se reinició como parte de esta verificación para conservar el resultado local.
