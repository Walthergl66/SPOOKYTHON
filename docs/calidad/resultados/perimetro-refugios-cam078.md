# CAM-078 — Verificación del perímetro de refugios

Fecha: 2026-10-27. Tipo: pruebas automatizadas locales; no es validación geográfica ni de seguridad real.

## Alcance comprobado

- El dominio produce el perímetro como el refugio y sus nodos adyacentes, sin propagar el búfer más allá de una calle.
- En mapa Manta, los caminantes no ejecutan tramos hacia nodos protegidos y el corredor descarta rutas que atraviesan ese perímetro.
- La población zombie inicial del mapa Manta excluye los nodos protegidos.
- Los mapas sintéticos conservan el movimiento existente.

## Verificación

- `cd backend && PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_resolver tests.test_demo`: 27 pruebas correctas.
- `cd backend && PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests`: 212 pruebas correctas.
- `python3 backend/scripts/check_docs.py`: 108 Markdown y 110 archivos comprobados.
- `python3 backend/scripts/check_sdd.py`: ocho SPEC con trazabilidad estructural válida; no certifica semántica.
- `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`: 8 pruebas correctas.
- `git diff --check`: correcto.
- Smoke local: API `/salud`, `/panel/mapa` y `/panel/estado` responden 200. En el turno 5 se observaron 159 zombies visibles y cero en los 17 nodos protegidos.

## Límites

La “cuadra” se aproxima mediante una arista topológica y puede variar mucho en metros. El smoke comprueba un snapshot local, no una garantía para todas las semillas. La comprobación no demuestra distancia física homogénea, cobertura OSM completa, resistencia ante tsunami/terremoto ni seguridad para evacuaciones reales. Ver [P-17](../../seguimiento/pendientes.md) y [ADR-031](../../arquitectura/decisiones/0031-perimetro-refugios-manta.md).
