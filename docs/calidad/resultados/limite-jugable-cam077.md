# Evidencia CAM-077 — Límite jugable y selector de refugios

Fecha: 2026-10-27, Ecuador continental. Estado: pruebas automatizadas y verificación local con partida activa correctas; revisión interactiva de clic de colocación pendiente.

## Implementación

La caja que el usuario aprobó como recorte común es `[-80.807, -1.082]`–`[-80.621, -0.897]` en longitud/latitud WGS84. El dominio filtra inclusivamente los nodos y conserva solo calles con ambos extremos dentro. La proyección de `manta-osm-df97a2f3a878` queda en 35.518 nodos y 75.548 sentidos, frente al fixture fuente de 44.590 y 94.146. Los cuatro refugios base sobreviven. Se conservó el JSON original.

Las partidas Manta construyen `Grafo` sobre la proyección. Por ello, el generador de apariciones y amenazas y los resolutores de ruta/movimiento solo pueden usar nodos internos. Refugios personalizados se validan contra esa misma proyección; un nodo fuera no existe en el mapa de la partida y el endpoint de inicio responde 422. El endpoint de candidatos comparte las cotas con el selector; el frontend encuadra la caja y filtra/rechaza el exterior.

## Verificación ejecutada

- `cd backend && PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_mapa_manta tests.test_demo tests.test_control_simulador_demo -v`: 25 pruebas correctas. Comprueba el recorte, nodos/calles internos, posiciones iniciales de personajes/amenazas, metadatos de límites en candidatos y rechazo HTTP de refugio exterior.
- `cd frontend && npm test -- --run`: 80 pruebas correctas en siete archivos. Incluye esquema de límites válido/inválido y rechazo de punto/nodo exterior.
- `cd frontend && npm run build`: correcto con TypeScript/Vite; queda el aviso preexistente del chunk MapLibre de 1.066 kB.
- `python3 backend/scripts/check_docs.py`: correcto, 106 Markdown/108 archivos; `python3 backend/scripts/check_sdd.py`: ocho SPEC con trazabilidad estructural válida; `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`: 8/8; `git diff --check`: correcto.
- Prueba inicial del lote completo frontend: 79 correctas y 1 fallida porque el fixture HTTP de candidatos no incluía el nuevo campo obligatorio. Se actualizó el fixture y la repetición completa pasó.
- Navegador local: el selector abrió en el recorte urbano y mostró su cartografía; API reiniciada y partida nueva `manta-osm-df97a2f3a878+zona-urbana`. `GET /panel/mapa` devolvió 35.518 nodos; el snapshot tuvo 20 sobrevivientes y 159 zombies, con 0 actores fuera de los nodos del mapa. La app quedó activa en turno 13 al último chequeo.

## Pendiente / límites

La revisión visual confirmó el encuadre, pero no se completó un clic sobre una intersección para colocar un refugio. La ronda anterior en turno 147 se perdió al reiniciar el backend para aplicar la zona nueva; la partida actual está activa y utiliza el subgrafo. Falta medir payload/cadencia objetivo y probar el fallback de cartografía.

La caja proviene de la estimación visual solicitada, no de un polígono administrativo. El fixture OSM fuente es reutilizable y continúa cubriendo su extensión amplia; las partidas Manta locales usan el subgrafo urbano. Esto no certifica la cobertura de calles, refugios ni uso real para evacuación.
