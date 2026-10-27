---
paths:
  - "backend/tests/**"
  - "backend/scripts/**"
---
# Pruebas y validadores

Fuente: [pruebas](../../docs/calidad/pruebas.md) (matriz T-01 a T-37 y comandos).

- Framework: `unittest` (`cd backend && python3 -m unittest discover -s tests -p 'test_x.py'`). No suponer `pytest` ni benchmarks configurados.
- Todo cambio de lógica no trivial lleva una prueba enlazada a un T-NN de la matriz; si no hay T adecuado, proponer uno nuevo en `docs/calidad/pruebas.md`.
- Núcleo con grafos pequeños y resultados conocidos, sin AWS ni servidor; adaptadores en memoria antes de integración.
- Reloj controlado (inyectado o monotónico falso): sin `sleep` reales para plazos, TTL o deadlines.
- No modificar una prueba para hacerla pasar salvo que el plan lo indique; un fallo se analiza, no se oculta.
- No declarar una prueba exitosa sin ejecutarla. Reportar comando, resultado real y fallos con su salida; registrar lo no ejecutado y por qué.
- `backend/scripts/check_docs.py` y `backend/scripts/check_sdd.py` (y `test_check_sdd.py`) son comprobaciones documentales: no prueban la aplicación ni sustituyen T-01 a T-19 y T-22 a T-24.
- Metas (p95, supervivencia, costos) son objetivos, no mediciones; no escribir «cumplido» sin reporte real en `docs/calidad/resultados/`.
- Fixtures sintéticos no representan densidades ni mapas oficiales; no usar secretos ni claves reales en datos de prueba.
- Los scripts son utilidades estándar; no añadir dependencias para unas pocas líneas.
