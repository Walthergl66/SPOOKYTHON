# CAM-033 — Medición local exploratoria de búsqueda temporal

Fecha: 2026-10-26, Ecuador continental. Implementación bajo evaluación P3-01.  
Mapa: `manta-osm-d76772f9d9e9`, fixture parcial de 300 nodos/4 refugios.  
Escenario: `mixto` sintético, semilla explícita `20261026`; mismo proceso local.  
Método: se crea un snapshot por cohorte, se convierten bloqueos/zombies actuales mediante `peligros_visibles()` y se llama una vez al planificador temporal por cada sobreviviente activo. Horizonte 6, presupuesto 25 ms por invocación, máximo 20.000 expansiones. Se reporta p95 nearest-rank de estas llamadas seriales locales.

| Sobrevivientes | Rutas dentro de horizonte | Sin ruta temporal al horizonte | p50 ms | p95 nearest-rank ms | Máximo ms | Máx. expansiones |
|---:|---:|---:|---:|---:|---:|---:|
| 20 | 14 | 6 | 0,631 | 1,331 | 1,566 | 95 |
| 80 | 45 | 35 | 0,667 | 1,514 | 1,773 | 125 |
| 200 | 106 | 94 | 0,494 | 1,291 | 1,955 | 132 |

Ninguna llamada individual agotó el límite temporal o de expansiones en esta ejecución. Una búsqueda que no alcanzó refugio dentro de seis acciones devolvió `sin_ruta_en_horizonte`; no se publicó ruta parcial ni se contó como supervivencia.

## Límites

Es una única ejecución serial de una función Python en el mismo host. No mide HTTP, concurrencia, p95 de servicio, tiempo global de ronda, reloj de dos segundos, rondas de cinco minutos, supervivencia, persistencia o AWS. No hubo pronóstico futuro de zombies: la entrada usó solo peligros visibles actuales y dejó las condiciones futuras vacías. Por tanto, esta tabla mide el núcleo acotado, no demuestra capacidad predictiva o mejora respecto a `/paso`. El mapa es parcial y no es guía de evacuación.

Para reproducir, utilizar `buscar_ruta_temporal()` con la configuración/fixture descritos; crear cada cohorte mediante `crear_contexto_demo(..., semilla=20261026, escenario="mixto", cantidad_sobrevivientes=N)`, proyectar el snapshot con `peligros_visibles()` y medir cada invocación con `time.perf_counter()`. CAM-033 conserva la prueba de ocho casos unitarios en `tests/test_ruta_temporal.py`.
