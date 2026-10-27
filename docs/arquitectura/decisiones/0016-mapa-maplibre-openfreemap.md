# ADR-016 — Renderizar cartografía OSM con MapLibre y OpenFreeMap

Fecha: 2026-10-26
Estado: aceptada para primera integración local
Origen: el usuario pidió reemplazar el grafo visual poco convincente con un mapa real y explorar 3D.

## Contexto

Navira ya usa un fixture de calles derivado de OSM, pero el frontend lo dibuja como líneas SVG entre 300 intersecciones seleccionadas. No muestra el fondo cartográfico, nombres, calles circundantes ni edificios; algunas vías contraídas omiten curvas de sus nodos intermedios. El panel obtiene coordenadas desde `/panel/mapa` y estado observable desde `/panel/estado`.

## Decisión

Usar MapLibre GL JS como renderer WebGL y los tiles vectoriales de OpenFreeMap sobre datos OSM. Usar el estilo oscuro como fondo, crear capas GeoJSON de Navira para grafo/bloqueos/rutas/actores/refugios y extruir polígonos de edificios solo con los atributos de altura disponibles. La inclinación inicial es 3D y un control permite regresar a 2D. Mostrar la atribución del estilo/proveedor/datos dentro del mapa.

El cliente solicita solo el viewport interactivo; no precarga ciudades ni descarga tiles masivamente. La fuente del tile y su estilo se mantienen configurables para permitir cambiar de proveedor. No se requiere una clave privada; si se incorpora después un proveedor con API key pública, restringirla por origen y cuota. No confiar en la instancia pública para SLA de producción.

## Alternativas

- Mantener SVG: no presenta el mapa base y tiene la limitación visual reportada.
- Usar directamente `tile.openstreetmap.org`: ofrece ráster 2D, no las capas vectoriales para extrusión; sus tiles estándar tienen política de uso y servicio best-effort.
- MapTiler Cloud: alternativa administrada para estilos/tiles/relieve; requiere key y control de quota/plan.
- CesiumJS/3D Tiles: útil para escenas geoespaciales extensas o modelos fotogramétricos, pero sobredimensionado para los ~300 nodos del prototipo y depende de disponibilidad de assets 3D de la zona.

## Consecuencias y límites

La visualización usa una base real y puede ofrecer volumen 3D, pero una extrusión es una representación aproximada basada en huella/altura cartográfica, no un modelo arquitectónico. Cobertura de edificios/alturas en Manta debe comprobarse visualmente y documentarse; lo desconocido no se inventa. Las rutas se conectan con nodos del fixture y aún pueden cortar curvas porque el exportador no conserva geometría completa entre nodos. Mapa base y mundo de juego siguen siendo conceptos separados: el proveedor aporta contexto cartográfico, el servidor de Navira sigue determinando eventos y rutas. CAM-053 limita cámara y máscara al recorte declarado; CAM-054 añadió 1,7 km por lado, CAM-055 llevó la vista a ~50 km por lado y CAM-056 la ajusta a ~15 km por lado. La extensión visual no amplía el grafo. No se dispone de un polígono administrativo oficial y la ventana no se describe como límite municipal.

Documentos propietarios: [SPEC-008](../../metodo/especificaciones/SPEC-008-mapa-cartografico-3d.md), [mapa Manta](../../dominio/mapa-manta.md), [frontend](../modulos/frontend.md), [API](../contratos/api.md) y [trazabilidad](../../metodo/trazabilidad.md).
