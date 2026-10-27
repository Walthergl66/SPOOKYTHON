# Evidencia CAM-053 — recorte cartográfico y límites de navegación

Fecha: 2026-10-26, Ecuador continental. Verificación local de la interfaz; no es despliegue ni validación para emergencias.

## Resultado observado

- La cámara inicial encuadra el rectángulo usado para extraer el fixture OSM de Manta: latitudes `-0.967` a `-0.935`, longitudes `-80.755` a `-80.675`.
- Una máscara oscura cubre la cartografía exterior a ese rectángulo. La cámara limita el desplazamiento con `maxBounds`, no renderiza copias del mundo y el control de alejar queda deshabilitado en la escala de encuadre completo.
- En `http://localhost:5173/`, el estilo OSM cargó y mostró la atribución. Se observó la máscara después de arrastrar en la vista inclinada y tras alternar a 2D. Se inició una demo local de 20 sobrevivientes y el panel recibió snapshots sucesivos hasta completar el turno 9.
- El backend local quedó disponible en `127.0.0.1:8000` y Vite en `localhost:5173` al concluir.

## Verificaciones

- `cd frontend && npm run build`: correcto con TypeScript y Vite. Permanece la advertencia conocida de chunk MapLibre mayor a 500 kB.
- Recorrido visual de T-27: carga/atribución, encuadre de Manta, máscara exterior y restricción al arrastrar observados en 3D y 2D; zoom-out inhabilitado en la vista completa.
- `git diff --check`: correcto.
- `python3 scripts/check_docs.py`: correcto; 77 Markdown de `docs/` y 79 archivos comprobados.
- `python3 scripts/check_sdd.py`: correcto; ocho SPEC con trazabilidad estructural válida. SPEC-008 sigue `implementada`, no `verificada`.
- `python3 -m unittest discover -s tests -p 'test_check_sdd.py'`: ocho pruebas correctas.

## Límites

El rectángulo es la ventana de extracción OSM documentada para este fixture, no un límite administrativo oficial ni evidencia de que estén cubiertos todos los barrios de Manta. La máscara solo limita la cartografía visible; no modifica el grafo, actores, reglas ni rutas del servidor. El proveedor requiere internet. Alturas/edificios, exactitud vial, seguridad ante sismos y uso de emergencia no quedan validados.
