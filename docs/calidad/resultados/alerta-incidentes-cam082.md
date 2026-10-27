# CAM-082 — Alerta cartográfica y cierres viales aleatorios

Fecha: 2026-10-27. Origen: solicitud del usuario para sortear al inicio 1–10 incidentes y, al ocurrir cada cierre, alertar en el mapa, marcar el punto en amarillo y recalcular las rutas.

## Comportamiento implementado

Cada partida local con incidentes activos usa su RNG para elegir uniformemente una cantidad entre 1 y 10, limitada por la cantidad de segmentos físicos del mapa. Selecciona segmentos únicos y los agenda cada tres turnos desde el turno 2. Intensidad zombie no altera el conteo. Mismo mapa y semilla reproducen la agenda.

El coordinador activa el cierre antes del movimiento zombie y antes de abrir decisiones. Las rutas recomendadas para ese snapshot reciben los cierres confirmados y no recorren segmentos bloqueados. El panel solo publica eventos aplicados y agrega el punto medio WGS84 de la vía afectada. El mapa dibuja un marcador amarillo con “!” que pulsa, presenta una alerta accesible durante ocho segundos y conserva el punto mientras el cierre permanece. Con `prefers-reduced-motion`, el punto queda estático. Los eventos futuros no se envían al panel.

## Verificación

Verificación local del 2026-10-27:

- Backend enfocado (`test_demo`, `test_panel`, `test_coordinador`): 34/34 pruebas correctas. Incluye cantidad entre 1 y 10, segmentos únicos, agenda determinista por semilla y variación entre semillas; ubicación solo para cierres aplicados y rutas que evitan los segmentos cerrados.
- Frontend: `npm test -- --run` — 87/87 pruebas correctas. Incluye análisis del contrato y proyección del punto GeoJSON.
- Frontend: `npm run build` — correcto; Vite mantiene la advertencia conocida de chunk de cartografía >500 kB.
- Python: `PYTHONPATH=src /tmp/navira-env/bin/python -m compileall -q src` — correcto.
- Documentación: `python3 backend/scripts/check_docs.py` — correcto (113 Markdown, 115 archivos); `python3 backend/scripts/check_sdd.py` — ocho SPEC correctas; `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'` — 8/8; `git diff --check` — correcto.
- Smoke en navegador con Vite y API locales: corrida de 20 sobrevivientes, escenario mixto, activa al turno 13. El panel HTTP devolvió cuatro incidentes aplicados (turnos 2, 5, 8 y 11), todos con segmento y coordenadas, y 19 rutas previstas. La interfaz mostró la alerta accesible «ALERTA VIAL · TURNO 11 … Vía cerrada; rutas de evacuación actualizadas». Estado del snapshot: 19 activos, 1 evacuado y 0 mordidos; no es una evaluación estadística.

La inspección funcional confirma la alerta del evento reciente y la respuesta de datos para marcadores/rutas. La capa GeoJSON y su punto están cubiertos por prueba; no se afirma verificación píxel a píxel del color/parpadeo del canvas MapLibre.

## Límites

Los cierres son eventos genéricos del prototipo; no representan accidentes viales reales ni amenazas sísmicas/tsunami. El punto medio de una arista del fixture aproxima la localización del segmento OSM. Un mapa con menos de diez segmentos tendrá un máximo menor. No se midió impacto estadístico sobre mordidas/evacuaciones, carga prolongada, AWS ni uso de emergencia.
