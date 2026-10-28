# CAM-099 — Repetibilidad local de la campaña Reto

- Fecha: 2026-10-27, Ecuador continental.
- Origen: continuación de CAM-098 para reducir la incertidumbre de una sola ejecución por ronda.
- Método: tres campañas secuenciales, cada una con R1/R2/R3; 150 turnos y período de 2 s por ronda; máximo 200 workers; Uvicorn y cliente HTTP en loopback; sin benchmarks paralelos.
- Semillas base: `20261026`, `20261027`, `20261028`. Cada campaña deriva semillas consecutivas por ronda.
- Comando por campaña: `cd backend && PYTHONPATH=src /tmp/navira-env/bin/python -m navira.evaluacion_local --campana-reto --turnos 150 --periodo-segundos 2 --concurrencia 200 --semilla <base>`.
- Reportes JSON íntegros locales: `/tmp/navira-campana-reto-cam098.json`, `/tmp/navira-campana-reto-cam099-seed-20261027.json`, `/tmp/navira-campana-reto-cam099-seed-20261028.json`. No se versionaron por su tamaño; este documento resume la evidencia relevante.

## Resultado agregado

Las nueve rondas completaron 150 turnos activos y sus ventanas de 300 s; no hubo slots ociosos, turnos fuera del período objetivo ni solicitudes fallidas. En total, las campañas duraron 2.741,724 s frente a 2.700 s de ventana objetivo y enviaron 69.572 solicitudes, todas HTTP 200. Los eventos programados se aplicaron: puente en R2 y dos calles distintas en R3 en cada campaña.

El p95 de `/paso` quedó entre 10,625 y 64,313 ms; el máximo individual fue 127,566 ms. El p95 de duración de ciclo por turno varió de 435,635 a 1.378,374 ms; el ciclo más largo fue 1.676,531 ms, por debajo del período de 2 s en estas corridas. Los resultados de mordidos y evacuados varían por semilla, como se espera del preset estocástico.

| Semilla base | Ronda (semilla efectiva) | Solicitudes | p95 `/paso` / máximo | p95 / máximo ciclo de turno | Evacuados / mordidos / activos | Eventos aplicados |
|---:|---|---:|---:|---:|---|---|
| 20261026 | R1 (20261026) | 1.420 | 10,625 / 42,504 ms | 463,409 / 603,021 ms | 19 / 0 / 1 | — |
| 20261026 | R2 (20261027) | 5.741 | 26,184 / 38,135 ms | 1.104,635 / 1.306,071 ms | 65 / 2 / 13 | Puente, turno 50 |
| 20261026 | R3 (20261028) | 15.394 | 64,313 / 127,566 ms | 1.378,374 / 1.676,531 ms | 167 / 7 / 26 | Calles 1 y 2, turnos 50/100 |
| 20261027 | R1 (20261027) | 1.371 | 10,843 / 37,374 ms | 489,927 / 563,046 ms | 19 / 0 / 1 | — |
| 20261027 | R2 (20261028) | 5.995 | 27,778 / 47,909 ms | 1.192,779 / 1.420,656 ms | 66 / 1 / 13 | Puente, turno 50 |
| 20261027 | R3 (20261029) | 16.061 | 62,678 / 99,648 ms | 1.127,380 / 1.209,971 ms | 165 / 6 / 29 | Calles 1 y 2, turnos 50/100 |
| 20261028 | R1 (20261028) | 1.534 | 11,300 / 76,679 ms | 435,635 / 524,525 ms | 18 / 0 / 2 | — |
| 20261028 | R2 (20261029) | 6.656 | 24,279 / 43,736 ms | 988,798 / 1.148,642 ms | 65 / 1 / 14 | Puente, turno 50 |
| 20261028 | R3 (20261030) | 15.400 | 55,105 / 65,941 ms | 986,570 / 1.193,467 ms | 163 / 7 / 30 | Calles 1 y 2, turnos 50/100 |

## Lectura del resultado

En estas tres campañas locales, cada cohorte mantuvo población activa a lo largo de sus 150 turnos; la medición no dependió de completar el reloj con slots sin actividad. El p95 HTTP quedó por debajo de 150 ms en las nueve rondas, no hubo fallas y el ciclo máximo quedó por debajo de 2 s. Los totales de evacuados/mordidos cambian entre semillas, por lo que el número de una ejecución no debe presentarse como garantía ni como superioridad estadística.

La regla de horda es R-06: su nodo y todos sus vecinos son intransitables. Evitar solo el nodo y cruzar por un vecino es un error, según la aclaración del usuario; el código y las regresiones T-03 ya la aplican.

## Límites y siguiente validación

Esto fortalece la evidencia de T-11/P5-01 en el entorno local, pero no completa la evaluación oficial. Las campañas comparten host, versión del mapa, implementación y metodología; no miden RTT de cliente remoto, AWS, disponibilidad, interferencia de red, persistencia ni variabilidad de infraestructura. Se conserva la cadencia local de 2 s y concurrencia máxima de 200, sin confirmar si el jurado usará exactamente esos perfiles. Densidad y turnos 50/100 siguen siendo supuestos provisionales, no decisiones confirmadas por la organización. La siguiente validación es correr el mismo harness en el entorno AWS/oficial, con permisos, Budget y endpoint comprobados, conservando reportes y versiones.

## Trazabilidad

- CAM-098: implementación del ejecutor secuencial y primera campaña semilla `20261026`.
- [T-11/T-50](../pruebas.md): carga/rondas y campaña secuencial local.
- [SPEC-005](../../metodo/especificaciones/SPEC-005-aws-evaluacion.md): repetición local registrada; AWS sigue pendiente.
- [SPEC-009](../../metodo/especificaciones/SPEC-009-modo-reto.md): presets R1/R2/R3, semilla/eventos y límites.
- CAM-099: repetición de dos campañas y comparación de nueve rondas.
