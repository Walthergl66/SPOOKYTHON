# Evidencia CAM-056 — ventana de 15 km por lado

## Alcance

El usuario pidió reducir el encuadre de aproximadamente 50 km a 15 km por lado. La ventana vigente añade alrededor de 15 km a cada borde del rectángulo de extracción OSM del fixture. Límites WGS84: oeste `-80.890`, sur `-1.103`, este `-80.540`, norte `-0.799`.

MapLibre utiliza estos límites para encuadrar la cámara, restringir el pan y el zoom-out, y ocultar tiles exteriores. El cambio afecta solo al basemap: el fixture conserva 300 nodos y 599 aristas en la zona central. La ventana no es un límite administrativo ni representa el territorio de simulación.

## Verificación

- Build frontend: `npm run build` correcto; permanece el aviso conocido de chunk MapLibre mayor a 500 kB.
- Documentación: `python3 scripts/check_docs.py` correcto (80 Markdown y 82 archivos); `python3 scripts/check_sdd.py` correcto (ocho SPEC); ocho pruebas del checker SDD y `git diff --check` correctos.
- Inspección de `http://localhost:5173/`: mapa y atribución cargados, escala visible de 5 km y zoom-out deshabilitado en el encuadre general; la partida está pausada y el panel conectado.
- Verificación local; no se midió cobertura exhaustiva del proveedor ni se amplió el grafo.
- Commit individual en `master`: pendiente de crearse después de revisar los cambios.

## Limitaciones

El proveedor público requiere internet y no ofrece SLA. El nivel de zoom resultante puede mostrar menos edificios extruidos que el encuadre de calle. No se amplía el grafo ni se validan rutas de evacuación.
