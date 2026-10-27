# Evidencia CAM-052 — fichas visibles y movimiento entre snapshots

Fecha: 2026-10-26, Ecuador continental. Verificación local en navegador y backend; no es despliegue ni validación para emergencias.

## Resultado observado

- El usuario reportó que al iniciar el simulador el mapa no mostraba movimiento.
- Se encontró que la conexión WebSocket conservaba el `ConsultarPanel` del run existente, aunque el control local sustituía ese objeto al iniciar otra partida. Por eso el control mostraba la partida nueva mientras el mapa seguía mostrando el snapshot terminal anterior hasta una recarga o actualización manual.
- La conexión ahora resuelve el proveedor actual en cada sondeo de 250 ms. Una prueba abre el socket, reemplaza el contexto por otro `runId` y confirma que llega el snapshot nuevo con su cursor independiente.
- El mapa ahora separa la fuente GeoJSON de los actores de calles y otras capas. Sobrevivientes, zombies y hordas se distinguen como fichas; al cambiar su nodo entre snapshots públicos, la ficha recorre el segmento confirmado durante 1,6 s. Si el sistema pide movimiento reducido, la posición se actualiza sin interpolación.
- La cámara encuadra los nodos del fixture de Manta al crear el mapa, para que los actores repartidos por la extensión del grafo no queden fuera del área visible.
- En el navegador local se inició desde la misma pestaña una partida sintética de 80 sobrevivientes. Sin recargar ni pulsar «Actualizar», el panel recibió snapshots sucesivos y llegó al turno 11; la captura visual mostró las fichas azules de sobrevivientes y rojas de zombies sobre el mapa.

## Verificaciones

- `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_panel -v`: 12 pruebas correctas, incluida la regresión de cambio de contexto con un WebSocket abierto.
- `cd frontend && npm run build`: TypeScript y Vite correctos.
- Recorrido manual en `http://localhost:5173/`: iniciar 80 personajes, observar actualización automática de turnos y fichas en el mapa sin refresco manual.
- `git diff --check`: correcto.
- El bundle diferido de MapLibre supera 500 kB sin comprimir; Vite conserva su advertencia de tamaño ya descrita en CAM-051.

## Límites

La animación visualiza cambios ya confirmados por el servidor y no anticipa ni ejecuta decisiones. Los movimientos de sobrevivientes se interpolan entre posiciones consecutivas; los movimientos de zombies usan el trayecto confirmado que ya publica el snapshot. La cartografía y su proveedor externo siguen sujetos a conectividad y cobertura OSM. No se probaron fallas inyectadas de tiles/WebGL, rutas viales completas ni reglas oficiales del reto.
