# CAM-098 — Campaña local R1, R2 y R3

- Fecha: 2026-10-27, Ecuador continental.
- Entorno: host local, cliente HTTP y Uvicorn en loopback; mapa Manta incluido en el repositorio.
- Propósito: ejecutar en secuencia las tres cohortes de evaluación Reto durante ventanas de 150 slots con cadencia objetivo de 2 s y registrar carga, eventos y resultado de cada run.
- Comando: `cd backend && PYTHONPATH=src /tmp/navira-env/bin/python -m navira.evaluacion_local --campana-reto --turnos 150 --periodo-segundos 2 --concurrencia 200`.
- Reproducibilidad: semilla base `20261026`; cada ronda deriva una semilla consecutiva. Los valores de densidad y turnos de eventos son presets provisionales, no parámetros confirmados por la organización.

## Resultado agregado

La campaña completó R1, R2 y R3 en 913,964 s (objetivo combinado: 900 s). Se enviaron 22.555 solicitudes HTTP y las 22.555 respondieron con HTTP 200; hubo cero fallas. Cada ronda ejecutó sus 150 turnos, no registró slots sin actividad, respetó la cadencia de inicio de 2 s dentro de la precisión local y cumplió la ventana objetivo de 300 s.

| Ronda | Población | HTTP | p95 / máximo `/paso` | p95 / máximo duración turno | Turnos fuera de período | Evacuados | Mordidos | Activos finales | Eventos aplicados |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| R1 | 20 | 1.420 | 10,625 / 42,504 ms | 463,409 / 603,021 ms | 0 | 19 | 0 | 1 | Ninguno |
| R2 | 80 | 5.741 | 26,184 / 38,135 ms | 1.104,635 / 1.306,071 ms | 0 | 65 | 2 | 13 | `EV-RETO-R2-PUENTE`, turno 50 |
| R3 | 200 | 15.394 | 64,313 / 127,566 ms | 1.378,374 / 1.676,531 ms | 0 | 167 | 7 | 26 | `EV-RETO-R3-CALLE-1`, turno 50; `EV-RETO-R3-CALLE-2`, turno 100 |

Las tasas de evacuación observadas fueron 95 % en R1, 81,25 % en R2 y 83,5 % en R3. Son resultados de una ejecución reproducible local, no garantías de supervivencia ni una comparación estadística.

## Criterio de horda

La regla oficial aclarada por el usuario es que cada horda bloquea su nodo y todos sus nodos vecinos. Una ruta que evita el nodo de la horda, pero cruza cualquiera de esos vecinos, cuenta como error. El código y las pruebas existentes de T-03 ya aplican esta regla; esta campaña no modifica ni reemplaza esas pruebas.

## Verificación de eventos y cadencia

- R1 no programa eventos de reto.
- El puente de R2 se programó y aplicó en el turno 50.
- Los dos cierres distintos de R3 se programaron y aplicaron en los turnos 50 y 100.
- Los inicios de los 150 turnos por ronda mantuvieron intervalos p95 de aproximadamente 2.000,01 ms; ningún turno excedió el período objetivo de 2 s en esta corrida.
- La latencia p95 de cada solicitud fue menor que 500 ms en los tres runs.

## Límites

Es evidencia exploratoria de una sola campaña en loopback; no mide internet, AWS, latencia del cliente remoto, variabilidad entre semillas, disponibilidad sostenida ni el entorno oficial. Aunque se alcanzaron 150 turnos y cinco minutos en cada ventana, los criterios de población y temporización no fueron ratificados por la organización. La cadencia de 2 s es un parámetro de este harness, no prueba la duración o el comportamiento del reloj continuo exigido en producción. Los tiempos máximos de turno de R2/R3 superaron 2 s, aunque no hubo inicios de turno fuera del período porque el trabajo se completó antes de la siguiente cadencia. Ejecutar una sola campaña no completa T-11 ni SPEC-005/SPEC-009; siguen pendientes repeticiones, evaluación en AWS y confirmación externa de los parámetros provisionales.

## Artefactos y trazabilidad

El JSON íntegro se conservó localmente en `/tmp/navira-campana-reto-cam098.json`; contiene `runId`, semilla, versión del mapa, métricas de turno y eventos programados/aplicados. El archivo temporal no forma parte del repositorio. El comando agregó `--campana-reto` al evaluador local. Véase [T-50 y T-11](../pruebas.md), [CAM-098](../../seguimiento/cambios.md#cam-098-ejecutar-campana-local-reto-r1r2r3-con-ventana-completa), [SPEC-005](../../metodo/especificaciones/SPEC-005-aws-evaluacion.md) y [SPEC-009](../../metodo/especificaciones/SPEC-009-modo-reto.md).
