# Validación acotada por solicitud — CAM-133

Fecha: 2026-10-28 (America/Guayaquil).

## Motivo y cambio

CAM-132 redujo búsquedas repetidas de rutas, pero nuevas ráfagas mostraron variación alta en `/paso`. En `DecidirPaso._obtener_contexto`, cada petición llamaba `Partida.validar_mapa()`, que recorría todos los sobrevivientes y zombies aunque solo se solicitaba una decisión. Como los snapshots son inmutables y se validan al crearlos, preparar/resolver turnos, la validación de la petición ahora comprueba versión del mapa, nodo y refugio objetivo del personaje solicitado. Las transiciones del mundo siguen validando la partida completa.

Se conservan errores explícitos para versión incompatible y referencias inválidas del habitante solicitado. El cambio no altera rutas, prioridades, API ni autoridad del servidor.

## Evidencia

La prueba focalizada `test_decidir_paso.py` pasa 21/21 e incluye casos para versión de mapa incompatible, nodo inválido y refugio inválido. Para medir el endpoint se usó Uvicorn loopback, semilla 20261026, escenario mixto, concurrencia de 200 y período de dos segundos:

| Muestra | Cohorte/turnos | Solicitudes | p50 | p95 | p99 | Fallas HTTP | Turnos >2 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| Corta | 200 / 3 | 600 | 71,853 ms | 216,299 ms | 224,692 ms | 0 | 1/3 |
| Intermedia | 200 / 10 | 1.997 | 75,078 ms | 129,513 ms | 179,234 ms | 0 | 3/10 |
| Extendida | 200 / 20 | 3.944 | 72,072 ms | 151,720 ms | 201,729 ms | 0 | 5/20 |

La muestra intermedia queda bajo la meta interna p95 de 150 ms, pero la muestra de 20 turnos la excede ligeramente y la corta excede con mayor margen. Por tanto, el resultado es variable y no demuestra cumplimiento sostenido. La cadencia de dos segundos tampoco se sostuvo en todas las rondas.

La suite backend completa pasó 250/250 en 385,702 s. `python3 backend/scripts/check_docs.py` pasó con 143 Markdown/145 archivos, `check_sdd.py` con 11 SPEC, las pruebas de regresión SDD pasaron 8/8 y `git diff --check` no encontró errores.

## Límites y siguiente paso

Las muestras corrieron en el mismo host que Uvicorn y el cliente; no miden la red, CPU ni configuración de Lightsail. La aplicación desplegada sigue en `ddfa843f81c9cb87732d56b4a1f5b59cf0ee466`; CAM-133 no se ha publicado. Ejecutar varias campañas completas con escenarios R1/R2/R3, aislar el costo de planificación y repetir desde un cliente externo antes de cerrar P-22/T-11 o declarar el requisito satisfecho.
