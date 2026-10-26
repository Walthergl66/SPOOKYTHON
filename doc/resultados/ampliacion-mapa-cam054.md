# Evidencia CAM-054 — ventana cartográfica ampliada

Fecha: 2026-10-26, Ecuador continental. Verificación local del mapa; no es despliegue ni guía de emergencia.

## Resultado observado

- El usuario pidió ampliar un poco el área porque el mapa no cargaba correctamente.
- La ventana de cámara/máscara se amplió `0.015°` por lado (aprox. 1,7 km), desde el rectángulo de extracción `[-80.755, -0.967]`–`[-80.675, -0.935]` hasta longitudes `-80.770`–`-80.660` y latitudes `-0.982`–`-0.920`.
- La demo local cargó los tiles vectoriales en `http://localhost:5173/`. La captura del navegador muestra más contexto de calles alrededor de Manta y los cuatro marcadores de refugio visibles simultáneamente. La máscara y el límite de navegación permanecen activos.
- No se alteraron el grafo, las rutas ni las coordenadas de simulación.

## Verificaciones

- `cd frontend && npm run build`: correcto con TypeScript y Vite; persiste la advertencia conocida de chunk MapLibre superior a 500 kB.
- `python3 scripts/check_docs.py`: correcto; 78 Markdown de `doc/` y 80 archivos comprobados.
- `python3 scripts/check_sdd.py`: correcto; ocho SPEC con trazabilidad estructural válida. SPEC-008 permanece `implementada`.
- `python3 -m unittest discover -s tests -p 'test_check_sdd.py'`: ocho pruebas correctas.
- `git diff --check`: correcto.
- La partida sintética se dejó pausada en el turno 1 para que el mapa permanezca abierto en la pestaña local.
- Comprobación manual dependiente de OpenFreeMap/OSM; no mide su SLA ni garantiza disponibilidad futura de tiles.

## Límites

El margen visual no agrega cobertura al fixture de 300 nodos y no es el límite administrativo oficial de Manta. No valida exactitud cartográfica, seguridad de refugios ni rutas de emergencia. El servicio de tiles requiere internet.
