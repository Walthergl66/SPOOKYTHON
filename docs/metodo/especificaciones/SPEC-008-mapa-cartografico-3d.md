# SPEC-008 — Mapa cartográfico real con vista 3D

ID: SPEC-008
Estado: implementada
Requisitos: PRD-01, PRD-04, TRD-07, TRD-09
Tareas: P1-01, P4-04
Pruebas: T-27, T-38
Cambio: CAM-075
Evidencia: [cobertura CAM-073](../../calidad/resultados/cobertura-manta-cam073.md), [margen de navegación CAM-074](../../calidad/resultados/margen-navegacion-5km-cam074.md), [mar visible CAM-075](../../calidad/resultados/mar-visible-cam075.md), [reporte CAM-051](../../calidad/resultados/mapa-cartografico-3d-cam051.md), [reporte CAM-052](../../calidad/resultados/movimiento-mapa-cam052.md), [reporte CAM-053](../../calidad/resultados/limites-mapa-cam053.md), [reporte CAM-054](../../calidad/resultados/ampliacion-mapa-cam054.md), [reporte CAM-055](../../calidad/resultados/ampliacion-50km-mapa-cam055.md), [reporte CAM-056](../../calidad/resultados/reduccion-15km-mapa-cam056.md)

## Objetivo y alcance

Origen: el usuario indicó que el grafo SVG actual no le convence y pidió una base cartográfica real, con vista 3D si es posible. La cartografía base procede de OpenStreetMap mediante OpenFreeMap; MapLibre GL JS la renderiza. Navira conserva su grafo versionado y snapshots del servidor como capas de calles simuladas, rutas y actores. El mapa base no genera ni reemplaza las reglas/eventos estocásticos del mundo.

La primera implementación ofrece estilo oscuro, edificios extruidos cuando los tiles incluyen altura, inclinación 3D, cámara 2D/3D y atribución visible. No promete edificios modelados con exactitud, cobertura completa de Manta, terreno de alta resolución ni uso como guía de emergencia. La elevación derivada de OSM puede estar incompleta; OpenFreeMap declara su instancia pública como servicio sin SLA y “as-is”. No se consultan tiles durante la simulación ni se envían credenciales del motor al proveedor.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-008-01 | El mapa central carga cartografía vectorial con coordenadas de la envolvente ampliada del cantón Manta, controles de zoom/rotación y atribución legible a OpenFreeMap/OpenMapTiles/OSM. | T-27 |
| CA-008-02 | Sobre el mapa base, las capas servidoras representan calles/bloqueos, rutas previstas y movimientos confirmados, refugios, sobrevivientes y zombies visibles en sus coordenadas. Los actores se distinguen como fichas identificables. | T-27 |
| CA-008-03 | La vista inclinada presenta extrusión 3D de huellas con altura disponible y permite alternar a 2D; datos de altura ausentes no se presentan como mediciones reales. | T-27 |
| CA-008-04 | Falla del proveedor/WebGL muestra un estado comprensible y la interfaz mantiene disponibles las estadísticas/control; el build de frontend compila. | T-27 |
| CA-008-05 | Cuando llega un snapshot de una partida en curso, cada actor cuya posición confirmada cambió se interpola por el trayecto entre nodos; respeta movimiento reducido y nunca modifica el estado del servidor. | T-27 |
| CA-008-06 | Al iniciar o reiniciar una partida, la cámara encuadra el mapa completo de juego, ofrece «Todo Manta»/«Ver partida» y el WebSocket sigue el nuevo `runId` sin exigir recarga o actualización manual. | T-27 |
| CA-008-07 | La vista general y el límite de navegación cubren la caja completa del fixture OSM ampliado; «Todo Manta» la encuadra y «Ver partida» vuelve a sobrevivientes/refugios. La navegación deja hasta 5 km de margen en cada lado, sin recortar la zona jugable; no hay copias del mundo y la caja no afirma ser el límite administrativo. | T-27, T-38 |
| CA-008-08 | El grafo del servidor cubre la zona jugable ampliada con calles públicas OSM conectadas en dirección a refugios; las fuentes/versión quedan identificadas y la cobertura/latencia tienen límites explícitos. | T-38 |
| CA-008-09 | La cartografía del proveedor permanece visible hasta el límite de navegación de 5 km alrededor de la zona jugable y los polígonos/canales de agua se distinguen claramente del terreno; el recorte opaco comienza fuera de ese margen. No se altera el grafo ni el límite de movimiento de actores. | T-27, T-38 |

## Plan y límites

Ampliación autorizada CAM-073: PRD-01/04, P1-01/P4-04 y T-07/T-27. Plan: (1) ampliar el exportador y generar la red pública conectada en la envolvente del cantón documentada en `mapa-manta.md`; (2) mostrar toda esa extensión con controles «Todo Manta» y «Ver partida», compartir encuadre con el selector de refugios y evitar reconstruir índices de calles por fotograma; (3) verificar cobertura fuera del recorte anterior, caminos dirigidos hacia refugios, arranque/avance y render; (4) registrar conteos, fuentes, limitaciones y evidencia. Esta ampliación no certifica que OSM contenga todas las calles existentes.

P4-04 sustituye la capa SVG por un componente MapLibre. Las transiciones visuales usan snapshots públicos consecutivos; no cambian el dominio, el contrato de `/paso`, el grafo versionado ni el estado autoritativo. El WebSocket vuelve a resolver el proveedor del panel durante la observación para seguir una partida local recién creada. Para calzar rutas curvas con la red real, una evolución debe conservar geometría completa OSM en el grafo público; esta versión conecta los nodos seleccionados con las coordenadas actuales.

CAM-073 amplía el grafo de juego y su encuadre a la envolvente documentada en [mapa-manta.md](../../dominio/mapa-manta.md). El usuario puede alternar entre el encuadre completo y el área de la partida. CAM-074 fija el límite de pan a 5 km alrededor de la caja completa, sin cambiar nodos, calles, refugios o posiciones elegibles. CAM-075 hace que la máscara exterior respete ese mismo margen y usa un azul visible para las capas de agua del estilo oscuro. Los límites siguen al rectángulo de nodos; no equivalen al polígono administrativo. Los tiles base siguen dependiendo de OpenFreeMap.

Validación CAM-073: suite de datos/cobertura, equivalencia del campo de rutas con Dijkstra, `npm test`, compilación, validadores documentales y recorrido local con partida iniciada; véase el [reporte](../../calidad/resultados/cobertura-manta-cam073.md). Quedan por medir el payload/cadencia objetivo y la falla controlada de tiles/WebGL; por eso esta SPEC permanece parcial. No hay herramienta de test de componentes configurada. El mapa depende de conexión a internet para tiles; el uso público de OpenFreeMap no tiene SLA. El fixture de rutas sigue siendo parcial, y los refugios no están certificados para amenaza sísmica.
