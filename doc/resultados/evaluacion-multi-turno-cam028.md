# Evaluación HTTP multi-turno local — CAM-028

Fecha: 2026-10-26. Entorno: local, intérprete `/tmp/navira-env/bin/python`. Revisión base: `fa7ebd8` (rama `master` sincronizada con `origin/master` al iniciar el ensayo; CAM-028 añade el ejecutor). Ejecutó Uvicorn en loopback y el cliente HTTP en la misma máquina.

## Configuración

- Mapa: `data/maps/manta-hackathon-v1.json`, versión `manta-osm-d76772f9d9e9`.
- Perfil sintético: `mixto`; semilla: `20261026`.
- Cinco turnos por cohorte, máximo 200 workers, timeout de solicitud de 1 s.
- Cada ronda consulta por `/paso` a cada sobreviviente activo; las solicitudes de ese turno leen la misma versión. Los destinos recibidos se aplican como intenciones y luego el snapshot avanza por resolución CAS.
- Comando: `PYTHONPATH=src /tmp/navira-env/bin/python -m navira.evaluacion_local --turnos 5 --poblaciones 20 80 200 --concurrencia 200 --semilla 20261026`.

## Resultados observados

| Cohorte | Turnos | Solicitudes | Fallos | p50 (ms) | p95 (ms) | p99 (ms) | Máx. (ms) | Evacuados | Mordidos | Activos finales | Duración (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 5 | 91 | 0 | 10,159 | 20,712 | 25,102 | 25,102 | 9 | 0 | 11 | 0,320 |
| 80 | 5 | 374 | 0 | 32,900 | 52,781 | 54,545 | 54,938 | 22 | 0 | 58 | 0,809 |
| 200 | 5 | 911 | 0 | 61,603 | 109,847 | 112,929 | 116,095 | 63 | 0 | 137 | 1,841 |

Todas las respuestas observadas fueron HTTP 200 y coincidieron con la recomendación calculada sobre el snapshot vigente. Las cifras son una ejecución local única con semilla fija; los tiempos pueden cambiar con hardware y carga del equipo.

## Alcance y límites

La evaluación ahora sí avanza el mundo entre turnos y aplica al resolutor los destinos devueltos por HTTP. No espera el período de dos segundos, no mide tres rondas oficiales de cinco minutos, no usa población zombie oficial ni representa solicitudes desde AWS/internet. Los tiempos incluyen la máquina compartida y el loopback; no son evidencia de p95 del servicio desplegado ni demuestran cumplimiento T-11. Las cohortes son sintéticas; cero mordidas en esta ejecución no acredita seguridad ni supervivencia esperada. El fixture identifica zonas seguras ante tsunami y no verifica amenaza sísmica.

En caso de fallo, timeout o respuesta distinta a la recomendación esperada, el evaluador cuenta la solicitud como fallida y usa espera en ese turno para poder concluir la transición; el JSON no registra claves ni coordenadas de zombies dormidos. La clave de prueba se genera aleatoriamente por ejecución, se limita al proceso local y se restaura al terminar.
