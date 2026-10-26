# Evidencia CAM-050 — tablero y control local del simulador

Fecha: 2026-10-26, Ecuador continental. Entorno local de desarrollo; no es evidencia de AWS ni de operación productiva.

## Resultado

- El frontend `http://localhost:5173/` mostró el tablero oscuro inspirado en la referencia: controles a la izquierda, mapa central y métricas/refugios/actualizaciones a la derecha, con distribución apilada en la ventana móvil inspeccionada.
- Se inició una partida desde el botón del frontend. El panel cambió a «En curso» y mostró el mapa parcial de Manta con 300 nodos y cuatro refugios, publicados por el backend local.
- Se pausó desde el frontend. Las consultas a `/demo/simulador` y `/panel/estado`, separadas por 2,5 segundos, conservaron `estado=pausada` y turno 2.
- El primer intento desde `localhost:5173` encontró `403 Origen no permitido`: Vite encaminó el request a `127.0.0.1:8000`. La comparación local ahora permite los alias `localhost`, `127.0.0.1` y `::1` para origen/Host; sigue rechazando orígenes ajenos y clientes no loopback. T-26 incluye esta regresión.

## Verificaciones automatizadas

- `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_control_simulador_demo.py'`: 5 pruebas correctas.
- `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests`: 159 pruebas correctas.
- `npm run build` en `frontend/`: TypeScript y Vite compilan correctamente.
- `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py` y `python3 -m unittest discover -s tests -p 'test_check_sdd.py'`: correctos tras incluir este reporte.

La suite imprime el mensaje de uso de argparse durante un test negativo esperado; el proceso termina con código 0 y la suite pasa.

## Límites

El fixture cartográfico es parcial y sintético para evaluación, aunque tenga anclas derivadas de Manta. No certifica seguridad ante sismos ni sirve para emergencias. El control y el estado existen solo en memoria del proceso, en loopback, con `NAVIRA_LOCAL_DEMO_CONTROL=1`; el backend productivo no debe habilitar ese flag. La inspección del diseño fue manual y no sustituye pruebas integrales de lector de pantalla, T-19, carga sostenida o despliegue.
