# Scripts de Navira

Reglas generales en [`../AGENTS.md`](../AGENTS.md).

## Scripts
- `check_docs.py`: valida enlaces Markdown locales y descubribilidad de la documentación.
- `check_sdd.py`: valida IDs, referencias, metadatos, criterios y evidencia SDD; admite `--spec SPEC-004`.
- `exportar_mapa_manta.py`: construye el artefacto de calles de Manta desde datos públicos de OSM y zonas seguras del GAD Manta.

## Reglas
- Los validadores no prueban la aplicación (ni latencia ni seguridad); ver [`../docs/metodo/SDD.md`](../docs/metodo/SDD.md).
- `exportar_mapa_manta.py` regenera fixtures de `backend/data/maps/`: no ejecutarlo ni modificar esos datos sin fuente registrada en [`../docs/dominio/mapa-manta.md`](../docs/dominio/mapa-manta.md) (sección Procedencia y alcance).
- Los scripts de validación usan solo la biblioteca estándar; no añadir dependencias externas.
- Pruebas del validador: `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`.
