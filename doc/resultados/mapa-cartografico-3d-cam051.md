# Evidencia CAM-051 — cartografía real y vista 3D

Fecha: 2026-10-26, Ecuador continental. Verificación de desarrollo local; no es despliegue ni validación para emergencia.

## Resultado observado

- Frontend local en `http://localhost:5173/`, con partida demo activa del fixture `manta-osm-d76772f9d9e9` en el backend de desarrollo.
- Se observó cartografía vectorial de Manta con calles y etiquetas del proveedor, controles de zoom/rotación, escala y atribución visible para MapLibre, OpenFreeMap, OpenMapTiles y OpenStreetMap.
- Al abrir la app se consultó el snapshot HTTP inicial y se recuperó el mapa de la partida pausada sin pulsar «Actualizar»; al iniciar desde el panel también apareció el mapa y sus capas tras cargar el endpoint cartográfico.
- Se comprobó en el árbol de accesibilidad que el control alternó entre `Vista 3D` y `Vista 2D`, y luego se restauró a `Vista 3D`. El estilo muestra huellas elevadas donde existen datos disponibles; las alturas son aproximaciones de la fuente, no mediciones verificadas.
- Se observa la capa de Navira sobre la cartografía: refugios, actores visibles y otros elementos se generan desde los datos del snapshot en el navegador. El proveedor de tiles no recibe snapshots ni posiciones de juego.
- Al ampliar, el basemap ofrece mayor contexto de calles/edificios, aunque la cobertura/altura de la ciudad no se comprobó exhaustivamente. Las rutas siguen uniendo intersecciones del fixture con líneas rectas y pueden diferir de las curvas reales.

## Verificaciones

- `cd frontend && npm run build`: TypeScript y Vite completaron correctamente. El build advirtió que el chunk diferido `CityMap` es 1.070,25 kB sin comprimir y 290,78 kB gzip; la aplicación inicial queda en 256,59 kB / 79,14 kB gzip y el mapa se carga bajo demanda.
- Navegador local: carga positiva de estilo/atribución; interacción 2D/3D y zoom; inspección visual del basemap con edificios elevados. No se guardó una captura como evidencia persistente.
- Estado de error: los estados WebGL/proveedor están implementados y mantienen visible el resto de UI, pero no se inyectó una caída controlada del proveedor en navegador.
- La instancia compartida del proveedor es pública, requiere red y no anuncia SLA. La revisión visual local no garantiza disponibilidad futura.

## Límites y siguiente paso

La vista 3D consiste en cámara inclinada y extrusión de huellas cartográficas, no fotogrametría ni modelos arquitectónicos. El nivel de detalle de Manta depende de los datos OSM/tile disponibles; calles curvas no se reconstruyen en las rutas del grafo actual. El mapa no es herramienta operativa ni guía de evacuación. Para completar SPEC-008 falta probar los estados de error de forma controlada y ampliar la inspección de cobertura; para alinear rutas con calles, conservar la geometría completa de los ways OSM en el contrato del grafo.
