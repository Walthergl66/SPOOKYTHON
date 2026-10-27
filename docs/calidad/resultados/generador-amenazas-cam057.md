# Verificación del generador sintético de amenazas — CAM-057

Fecha: 2026-10-26 (Ecuador continental). Estado: implementación y verificación local.

## Alcance

La demo permite seleccionar intensidad sintética baja/media/alta, distribuye tipos de amenaza por sectores geográficos del grafo y puede programar incidentes viales mediante cierres de segmento. Los metadatos del panel aparecen después de aplicar cada evento. No son conteos oficiales ni una simulación de terremotos o tsunamis.

## Verificación ejecutada

- `cd frontend && npm run build`: correcto. TypeScript y Vite compilaron; Vite emitió la advertencia ya conocida de bundle MapLibre mayor a 500 kB.
- `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_demo tests.test_panel tests.test_control_simulador_demo -v`: 28 pruebas correctas.
- Suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py'`: 162 pruebas correctas.
- `PYTHONPATH=src /tmp/navira-env/bin/python -m compileall -q src tests`: ejecutado sin errores de sintaxis.
- `python3 scripts/check_docs.py`: correcto (82 Markdown, 84 archivos comprobados).
- `python3 scripts/check_sdd.py`: correcto (8 SPEC estructuralmente válidas); ocho regresiones de `test_check_sdd.py` pasan.
- `git diff --check`: correcto.

## Smoke local

Se reinició Uvicorn para cargar el commit CAM-057 en `127.0.0.1:8000`, manteniendo Vite en `localhost:5173`. El control inició perfil `mixto`, 20 sobrevivientes, intensidad alta e incidentes activados. El endpoint de estado confirmó 65 amenazas visibles en turno 0; en turno 4 había 67 visibles, 10 sobrevivientes y el incidente del turno 2 aplicado. En la inspección del panel en navegador, el WebSocket aparecía en vivo, los controles mostraban intensidad alta/incidentes activados y el registro mostraba cierres ya aplicados en turnos 2, 5 y 8. La ronda siguió avanzando; al turno 9 reportaba 6 sobrevivientes activos, 5 evacuados y 9 mordidos.

## Límites

La suite verifica densidad espacial, reproducción de semilla, privacidad de dormidos y publicación posterior al cierre. El smoke local prueba el control/panel integrado, no la precisión visual de cada ficha o la cobertura de todos los barrios. Los validadores documentales comprueban estructura/enlaces, no comportamiento del backend. Los presets 6/14/25 % son elecciones de dificultad de demo y no describen la densidad real de Manta. Las rutas siguen usando el planificador actual, sin política temporal o garantía de evacuación.

## Siguiente paso

La unidad local queda verificada; para rondas oficiales aún faltan parámetros confirmados para densidad, hordas y eventos, además de su evaluación con las reglas aprobadas.
