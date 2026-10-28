# Evidencia CAM-097 — Nueva simulación desde Reto pausado

Fecha: 2026-10-27, Ecuador continental. Control local; no acredita campaña oficial ni despliegue.

## Criterio

- Una acción principal única muestra iniciar/pausar/continuar según estado.
- Con Reto pausado, es posible continuar el mismo mundo, reiniciar el mismo preset o iniciar un preset nuevo seleccionado; iniciar nuevo reemplaza el mundo pausado con otro `runId`.
- El backend conserva protección de partida activa y de simulador libre pausado.

## Evidencia

- Backend: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_control_simulador_demo -v` — 14/14. La ronda pausada R2 se reemplaza por R3 con `runId` distinto y 200 sobrevivientes; intentar sustituir una activa da 409. Un simulador libre pausado también sigue protegido (409).
- Frontend: `npm test -- --run` — 96/96; `npm run build` — correcto. Permanece advertencia de chunk `mapArea` 1.065,62 kB.
- Documentación: `python3 backend/scripts/check_docs.py` — 127 Markdown/129 archivos; `python3 backend/scripts/check_sdd.py` — 9 SPEC estructuralmente válidas; `test_check_sdd.py` — 8/8; `git diff --check` correcto.
- Navegador local `http://localhost:5173/`: botón principal pasó entre «Continuar R2» y «Pausar R2». Se pulsó «Nueva simulación R2» desde pausa; comenzó otro R2 con 80 sobrevivientes y nuevo `runId`, luego se pausó. Estado final visible: R2 pausada en turno 4, con «Continuar R2», «Nueva simulación R2» y «Reiniciar R2».
- API actualizada en `127.0.0.1:8001`; `/salud` y UI responden HTTP 200.

## Límite

El reinicio del backend necesario para cargar esta versión descartó la partida pausada en memoria anterior; el nuevo flujo se validó con una R2 nueva. Al reemplazar un Reto pausado, el mundo anterior deja de estar disponible en el almacén volátil local. No se reemplazan partidas activas ni simulador libre pausado. No se añade historial durable.
