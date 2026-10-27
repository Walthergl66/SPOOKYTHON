# Ejecución exploratoria del simulador sobre el mapa de Manta — CAM-025

Fecha: 2026-10-26. Entorno: local, `/tmp/navira-env`. Código del simulador en `27a95d9`; no se midió el tiempo de pared ni se usó un endpoint HTTP.

## Configuración

- Mapa: `data/maps/manta-hackathon-v1.json`, versión `manta-osm-d76772f9d9e9`.
- Perfil: `demo-sintetico-mixto` (composición reducida de desarrollo; no oficial).
- Semilla: `20261026` en cada ejecución.
- Turnos: hasta 3 por cohorte.
- Poblaciones: 20, 80 y 200 sobrevivientes.
- Comando equivalente por cohorte: `PYTHONPATH=src /tmp/navira-env/bin/python -m navira.simulador_demo --turnos 3 --semilla 20261026 --escenario mixto --sobrevivientes N --mapa data/maps/manta-hackathon-v1.json`.

## Resultados observados

| Sobrevivientes iniciales | Turnos | Movimientos de sobrevivientes | Evacuados | Mordidos | Activos al final | Movimientos zombie visibles |
|---:|---:|---:|---:|---:|---:|---:|
| 20 | 3 | 60 | 2 | 0 | 18 | 3 |
| 80 | 3 | 240 | 8 | 0 | 72 | 6 |
| 200 | 3 | 600 | 28 | 0 | 172 | 6 |

El reporte del CLI incluye la versión de mapa, semilla, movimientos, mordidas, evacuaciones y estado activo. La prueba [`test_simulacion_mapa_manta.py`](../../../backend/tests/test_simulacion_mapa_manta.py) vuelve a ejecutar las tres cohortes, comprueba que los inicios no sean refugios y valida que los pasos registrados sean vecinos dirigidos o espera.

## Límites de esta evidencia

Son tres ejecuciones locales deterministas con el mismo mapa, perfil y semilla; cambiar población altera también el consumo aleatorio. No son muestras independientes ni las rondas oficiales del reto. No se ejecutaron las duraciones oficiales, no se midió latencia/carga, el mundo no se avanzó por HTTP y el perfil no fija densidad zombie oficial. El mapa contiene anclas identificadas como zonas seguras ante tsunami; esta prueba no acredita seguridad ante terremotos, cobertura completa ni uso para evacuación real. P-07, P-09, P-13 y P-14 continúan abiertos.
