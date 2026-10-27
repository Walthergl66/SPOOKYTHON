# CAM-073 — Cobertura jugable ampliada de Manta

Fecha: 2026-10-27 (Ecuador continental). Origen: solicitud del usuario de ampliar el mapa completo y la zona jugable, confirmada para incluir parroquias rurales.

## Implementación y procedencia

Se sustituyó el recorte urbano de 300 nodos/599 sentidos por una extracción vial OSM de Overpass para la caja WGS84 sur `-1.140`, oeste `-80.920`, norte `-0.920`, este `-80.650`. Es una envolvente rectangular con margen respecto a la caja de la relación OSM del cantón 112895; puede incluir territorio vecino y no constituye límite administrativo oficial. La consulta eligió vías públicas de categorías viales motorizadas documentadas por el exportador, respetando sentidos únicos. Conservó vértices OSM, geometría de calles, y nodos con un camino dirigido a uno de cuatro refugios.

- Fixture: `manta-osm-df97a2f3a878`; 44.590 nodos, 94.146 sentidos dirigidos, cuatro refugios.
- Respuesta archivada: 6.222.751 bytes, SHA-256 `d9a455055ca3e49d630ad0d2fc7fd4a6256fc5002af99d3e497acf82e0b778f8`.
- 581 nodos de la caja original sin camino dirigido a refugio se excluyeron. El conteo final solo conserva la red que puede evacuar hacia al menos un refugio.
- Cinco referencias aproximadas de muestra (San Mateo, Santa Marianita, San Lorenzo, Eloy Alfaro y aeropuerto) tienen nodo OSM dentro de 1 km; estas coordenadas son chequeos de cobertura, no puntos oficiales de interés.
- Las fuentes de los cuatro refugios y su calificación para amenaza sísmica permanecen descritas en [mapa-manta.md](../../dominio/mapa-manta.md).

## Cambios de simulación y mapa

El grafo ampliado alimenta las mismas reglas de movimientos, rutas, peligros y aparición de personajes. El cálculo conjunto usa un campo inverso Dijkstra compartido por objetivo, cierres y peligros de un snapshot; los cierres de cruces del turno actual no se mezclan con los trayectos futuros. El campo se reconstruye por snapshot y no revela zombies dormidos. Pronóstico observable cachea destinos de corredor durante el mismo cálculo y el grafo reutiliza listas de salidas/entradas.

MapLibre encuadra toda la caja del mapa, la limita con margen y ofrece «Todo Manta» y «Ver partida». El selector de refugios usa el mismo encuadre. La indexación de posiciones y las capas estáticas se memoizan por versión/estado, evitando rehacer índices para cada fotograma de interpolación. La UI aclara que el fixture OSM y la seguridad sísmica no están certificados y que no es para emergencias reales.

## Verificación

- Fuente y generador: [exportar_mapa_manta.py](../../../backend/scripts/exportar_mapa_manta.py); fixture y sidecar versionados en `backend/data/maps/`.
- Cobertura/conteos/rutas y extensión espacial: `backend/tests/test_mapa_manta.py`.
- Parser y preservación de vértices: `backend/tests/test_exportar_cobertura.py`.
- Equivalencia de rutas inversas contra Dijkstra: `backend/tests/test_dijkstra.py`; la clase focalizada obtuvo 10 pruebas correctas, incluyendo 25 grafos dirigidos aleatorios deterministas.
- Frontend: `npm test` pasó 75 pruebas en siete archivos. `npm run build` se ejecutó antes de la revisión final del texto UI; se debe repetir después de la edición.
- Navegador local: inició una partida, recibió versión `manta-osm-df97a2f3a878`, cargó cuatro refugios, 20 personajes y controles «Todo Manta»/«Ver partida»; se pausó el simulador después de la comprobación. Vite/MapLibre mostró calles y actores sobre la caja ampliada.
- `GET /panel/mapa`: 200; JSON sin comprimir de 20.082.198 bytes. Con middleware GZip y `Accept-Encoding: gzip`, una descarga loopback entregó 1.910.769 bytes (−90,5 %) en 5,15 s total. Es una sola muestra que incluye serialización/compresión; no es p95 ni mide transferencia de red real.
- Suite backend completa antes del último ajuste de GZip: 206 pruebas correctas (unittest, 219,1 s). Tras agregar compresión, las 7 pruebas HTTP focalizadas pasaron. Casos de exportador 2/2, cobertura del fixture 3/3 y campo compartido 10/10 correctos.
- Frontend: `npm test` 75 pruebas en siete archivos; `npm run build` correcto. Vite conserva advertencia de chunk de mapa grande (1,065 kB minificado/289 kB gzip).
- Documentación: `check_docs.py` comprobó 101 Markdown/103 archivos; `check_sdd.py` validó trazabilidad estructural de 8 SPEC. `git diff --check` correcto. Estos validadores no comprueban comportamiento/rendimiento.

## Límites pendientes

OpenStreetMap puede omitir caminos peatonales y calles privadas o incompletas; no se auditó cada calle. La extensión usa caja rectangular aproximada, no el polígono catastral del GAD. No hay validación de rutas vigentes ni de seguridad de refugios ante sismos. Tiles dependen de internet y proveedor público sin SLA. El tamaño HTTP del mapa puede afectar la primera carga y requiere medir compresión, memoria y cadencia.

Siguiente: medir transferencia comprimida, memoria de navegador y cadencia de `GET /panel/mapa`; medir y, si incumple límites de carga, reducir o partir el payload. Auditar cobertura vial/peatonal y probar modo de falla de proveedor/WebGL antes de cerrar SPEC-008.
