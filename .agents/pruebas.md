# Pruebas de Navira

Reglas generales en [`../AGENTS.md`](../AGENTS.md). Catálogo de escenarios: [`../docs/calidad/pruebas.md`](../docs/calidad/pruebas.md). Comandos: [`../docs/metodo/SDD.md`](../docs/metodo/SDD.md).

## Comandos
- Dependencias de API: `cd backend && python -m pip install -e '.[test]'` (entorno `backend/.venv`).
- Todo el backend: `cd backend && python -m unittest discover -s tests -p 'test_*.py' -v`
- Solo documentación SDD: `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`

## Convenciones
- Se usa `unittest`, no pytest. Archivos `test_*.py`.
- Toda lógica no trivial tiene prueba; una regresión por bug corregido.
- Reloj controlado (parches, relojes inyectados, semillas fijas); nunca depender del tiempo real.
- Las pruebas de `/paso` y del panel no deben filtrar zombis dormidos ni estado aleatorio privado (T-04).
- Identificar escenarios con los IDs `T-NN` de `docs/calidad/pruebas.md`.
- Las pruebas de documentación van en `test_check_sdd.py`, con fixtures aislados.

## Archivos
- `test_api_http.py`: salud, autenticación y contrato HTTP de `POST /paso`.
- `test_api_planner_integration.py`: contrato HTTP con estado y grafo ensamblados.
- `test_carga_http.py`: métricas y validación del cliente de ráfagas.
- `test_check_sdd.py`: validador SDD con fixture aislado.
- `test_control_simulador_demo.py`: control local del simulador y publicación de snapshots.
- `test_coordinador_juego.py`: ciclo humano con snapshot y resolutor compartidos.
- `test_coordinador.py`: versionado, eventos y avance de turno.
- `test_decidir_paso.py`: caso de uso de rutas contra snapshot activo.
- `test_demo.py`: arranque local con mapa sintético.
- `test_dijkstra.py`: rutas dirigidas, ponderadas y con peligros.
- `test_evaluacion_local.py`: evaluación HTTP multi-turno en Manta.
- `test_evaluacion_rutas.py`: reproducibilidad del comparador temporal vs Dijkstra.
- `test_juego_sesion.py`: sesión propietaria y aparición segura del humano.
- `test_mapa_manta.py`: integridad del fixture de Manta.
- `test_mapa.py`: validación de mapa y cierres.
- `test_modelo.py`: invariantes de partida e intenciones.
- `test_ordenes_juego.py`: propiedad, validación e idempotencia de órdenes.
- `test_panel.py`: proyecciones públicas del panel y WebSocket.
- `test_prediccion_rutas.py`: frontera de información y pronósticos.
- `test_resolver.py`: movimiento zombi y resolución conjunta del turno.
- `test_ruta_temporal.py`: búsqueda temporal acotada y espera.
- `test_simulacion_automatica.py`: rondas automáticas reanudables.
- `test_simulacion_mapa_manta.py`: generador estocástico sobre el fixture de Manta.
- `test_simulador_demo.py`: CLI local de rondas automáticas.
- `test_snapshots_persistidos.py`: puerto CAS y adaptador local de snapshots.
- `fixtures/`: datos de prueba (p. ej. `mapa-minimo.json`).
