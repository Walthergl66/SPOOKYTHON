# Mar visible en el mapa — CAM-075

Fecha: 2026-10-27 (Ecuador continental). Origen: el usuario reportó que el mapa se veía igual y que el mar no aparecía en el lado derecho.

## Diagnóstico y cambio

El estilo `dark` de OpenFreeMap carga una capa `water` con `fill-color` `rgb(27,27,29)`, casi del mismo tono que el fondo terrestre oscuro. Además, aunque MapLibre permitía navegar 5 km más allá de la caja jugable mediante `paddedBounds`, la máscara opaca se calculaba con la caja sin ampliar y cubría los tiles del proveedor dentro de ese margen.

`CityMap` ahora aplica azul legible a las capas de agua/canales y sus etiquetas. La máscara usa `outsideBoundsMask(paddedBounds(area))`, por lo que se conserva la cartografía (incluido el mar) dentro de los 5 km navegables y el exterior se oculta fuera de ellos. `outsideBoundsMask` quedó como función pura en `mapArea.ts`, con cobertura focalizada. No cambia el grafo, los actores, las rutas ni el área jugable.

## Verificación

- `cd frontend && npm test`: 77 pruebas correctas en 7 archivos; incluye regresión de la geometría y límites de la máscara.
- `cd frontend && npm run build`: correcto; se conserva el aviso existente del chunk de MapLibre mayor a 500 kB.
- El estilo remoto se consultó en `https://tiles.openfreemap.org/styles/dark`: confirma las capas `water` (fill) y `waterway` (line), con color original casi negro.
- Inspección visual en `http://localhost:5173/`: se levantó la demo Manta usando el entorno disponible `/tmp/navira-env`, se cargó la versión `manta-osm-df97a2f3a878` y se encuadró «Todo Manta». El mar aparece en azul al oeste de la costa y contrasta con el terreno y las calles. La simulación se dejó pausada en el turno 22. El océano no debe aparecer en el este porque Manta limita allí con terreno continental.
- `python3 backend/scripts/check_docs.py`: correcto, 103 Markdown/105 archivos.
- `python3 backend/scripts/check_sdd.py`: correcto, ocho SPEC estructuralmente válidas.
- `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`: ocho pruebas correctas.
- `git diff --check`: correcto después de quitar un espacio final detectado en la primera pasada.

## Límites y continuación

El azul es solo una decisión de representación visual sobre las entidades de agua que el proveedor cartográfico entregue. No agrega ni modifica datos geográficos ni acredita una línea de costa más precisa. Tiles requieren conexión y OpenFreeMap no ofrece SLA. La verificación cubrió la vista «Todo Manta» en el navegador local, no una auditoría de exactitud de costa.
