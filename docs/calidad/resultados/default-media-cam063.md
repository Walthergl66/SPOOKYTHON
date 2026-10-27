# CAM-063 — Intensidad media inicial en la demo

Fecha: 2026-10-26. Comparación local reproducible en el checkout de Navira.

## Método

Se ejecutó el mismo evaluador de política temporal para cada intensidad con mapa `data/maps/manta-hackathon-v1.json`, escenario `mixto`, población 20, eventos viales activados, horizonte 12 y hasta 30 turnos. Semillas idénticas en ambas configuraciones: 101, 202 y 303. Cada ejecución empezó desde un mundo nuevo y usó el mismo resolutor.

Comando equivalente:

```python
from navira.evaluacion_rutas import _ejecutar_corrida

for intensidad in ("media", "alta"):
    for semilla in (101, 202, 303):
        _ejecutar_corrida(
            "temporal", "data/maps/manta-hackathon-v1.json", "mixto",
            semilla, 20, 30, 12, intensidad, True,
        )
```

## Resultados

| Intensidad | Semilla | Evacuados | Mordidos | Activos | Turnos |
|---|---:|---:|---:|---:|---:|
| Media | 101 | 6 | 12 | 2 | 30 |
| Media | 202 | 16 | 2 | 2 | 30 |
| Media | 303 | 7 | 13 | 0 | 27 |
| **Media total** | — | **29** | **27** | **4** | — |
| Alta | 101 | 5 | 14 | 1 | 30 |
| Alta | 202 | 5 | 15 | 0 | 20 |
| Alta | 303 | 3 | 16 | 1 | 30 |
| **Alta total** | — | **13** | **45** | **2** | — |

Por seed, media evacuó 1/11/4 habitantes más y tuvo 2/13/3 mordidas menos que alta. Los totales por intensidad suman 60 habitantes. La intensidad media aumenta evacuados en esta muestra, sin reducir la aleatoriedad; otras semillas y escenarios pueden variar.

## Alcance

La muestra exploratoria, aunque emparejada, es de solo tres semillas y un escenario. Justifica el valor inicial de la demo, no una mejora universal ni una densidad real de zombies. Incidentes continúan activados por defecto; el operador puede desactivarlos y elegir intensidad alta/baja antes de iniciar. La prueba no certifica rutas de emergencia.
