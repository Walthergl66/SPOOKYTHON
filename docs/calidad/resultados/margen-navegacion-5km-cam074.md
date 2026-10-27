# Margen de navegación del mapa — CAM-074

Fecha: 2026-10-27 (Ecuador continental). Origen: solicitud del usuario de dejar una extensión de 5 km por lado para enfocar el mapa en Manta.

## Cambio

`paddedBounds` amplía los cuatro lados del rectángulo jugable con el equivalente aproximado de 5 km. Convierte latitud con 111,32 km por grado y longitud con el coseno de la latitud media. CityMap y el selector de refugios consumen la misma función.

Este ajuste limita el desplazamiento exterior. No recorta la envolvente completa de Manta del CAM-073: permanecen los 44.590 nodos, 94.146 sentidos dirigidos, cuatro refugios y los lugares de aparición/rutas de la zona jugable.

## Verificación

- `cd frontend && npm test -- src/features/map/mapArea.test.ts`: 5 pruebas correctas, incluidos los cuatro lados en km y la caja `MANTA_AREA` intacta.
- `cd frontend && npm test`: 76 pruebas correctas en 7 archivos.
- `cd frontend && npm run build`: correcto; persiste el aviso existente del bundle de MapLibre (chunk `mapArea` de 1.065 kB minificado/289 kB gzip).
- `python3 backend/scripts/check_docs.py`: correcto, 102 Markdown y 104 archivos.
- `python3 backend/scripts/check_sdd.py`: 8 SPEC válidas; `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`: 8 pruebas correctas; `git diff --check`: correcto.
- Navegador local `http://localhost:5173/`: el mapa OSM completo y snapshots de la partida siguieron cargando después de HMR, sin errores de consola. El límite se cubre con la regresión numérica; no se hizo un arrastre manual hasta los cuatro bordes.

## Límites

La conversión local es aproximada sobre coordenadas WGS84 y una caja rectangular; no representa la distancia por carretera o terreno ni un límite administrativo. La base cartográfica sigue requiriendo tiles externos.
