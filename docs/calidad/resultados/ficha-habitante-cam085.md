# Ficha del habitante seleccionado en el panel lateral — CAM-085

Fecha: 2026-10-27, Ecuador continental.  
Alcance: presentación frontend de selección ya implementada en CAM-083; no cambia contratos ni decisiones del motor.

## Cambio

La ficha y ruta recomendada del habitante seleccionado ahora aparecen en la columna izquierda, debajo de controles y estado de la partida. Antes cubrían una esquina del mapa. El mapa conserva el resaltado de la ruta; la ficha conserva estado, nodo, siguiente paso, refugio/destino, lista alternativa y recorrido expandible. La fuente sigue siendo el snapshot validado del servidor y la selección es una acción local de observación.

## Verificación

- `cd frontend && npm test -- --run`: 8 archivos y 89 pruebas correctos.
- `cd frontend && npm run build`: correcto; Vite informa que el chunk cartográfico supera 500 kB (advertencia preexistente).
- Servicio local Vite en `127.0.0.1:5173`: HTTP 200.
- `/salud` de API `127.0.0.1:8001`: HTTP 200. Puerto 8000 sin listener.
- Revisión interactiva en pestaña nueva: panel conectado en vivo, turno 242; al seleccionar `S-DEMO-001` desde la lista, la ficha con nodo, siguiente paso, destino y ruta aparece en el lateral antes del mapa. Viewport 557 × 720 px.
- `git diff --check`: se ejecuta al cierre del cambio.

## Límites

La vista verificada usa un viewport estrecho y confirma el orden lateral antes del mapa en ese ancho. No se inspeccionó visualmente el breakpoint de escritorio. La partida de demo activa se observó en el turno 242; no se alteraron las reglas del motor.

Siguiente comprobación: inspeccionar la columna izquierda en el breakpoint de escritorio.
