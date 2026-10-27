# CAM-076 — Ventana urbana del mapa principal

Fecha: 2026-10-27, Ecuador continental. Estado: implementación local y pruebas de geometría/build; revisión visual del mapa principal pendiente.

## Solicitud y criterio

El usuario pidió limitar el mapa al tamaño de la captura de referencia. La imagen muestra un recorte urbano aproximadamente cuadrado con el mar al norte. Se estima la ventana con los cuatro refugios de coordenadas fijas que también aparecen en la imagen: `[-80.807, -1.082]`–`[-80.621, -0.897]`, alrededor de 20,7 × 20,6 km. Es una aproximación visual; el usuario no proporcionó coordenadas de esquina.

El límite se aplica a la cámara y máscara de `CityMap`; no recorta el grafo, posiciones, snapshots ni movimiento. `Ver partida` enfoca únicamente el rectángulo visible. El selector de refugios permanece con la vista amplia para revisar el fixture.

## Verificación ejecutada

- `cd frontend && npm test -- --run src/features/map/mapArea.test.ts`: 8/8 pruebas correctas, incluidas cotas de la ventana y recorte del foco.
- `cd frontend && npm test`: 79/79 pruebas en siete archivos correctas.
- `cd frontend && npm run build`: correcto con TypeScript/Vite. Permanece el aviso conocido de chunk de MapLibre superior a 500 kB.
- `python3 backend/scripts/check_docs.py`: correcto, 104 Markdown en `docs/` y 106 archivos comprobados.
- `python3 backend/scripts/check_sdd.py`: correcto, ocho especificaciones con trazabilidad estructural válida.
- `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'`: ocho regresiones correctas.
- `git diff --check`: correcto.
- Revisión del código confirma que `MANTA_AREA` y `mapAreaBounds()` siguen representando la cobertura jugable y que CAM-076 solo usa `MANTA_CITY_VIEW` en el mapa principal.
- El navegador no pudo mostrar una partida activa para revisar visualmente el mapa principal: el estado en memoria anterior (turno 22) ya no estaba, y la demo quedó sin partida. No se marca la revisión visual como verificada.

## Límites

La ventana se infirió de la captura y puede requerir un ajuste posterior si el encuadre visible difiere. Con la cámara limitada, actores fuera de esa ventana siguen simulándose pero no aparecen en el mapa principal. Esta caja no es un límite municipal ni una recomendación de evacuación real. No se midieron carga de tiles, payload o desempeño.
