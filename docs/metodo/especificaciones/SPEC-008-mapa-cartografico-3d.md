# SPEC-008 — Mapa cartográfico real con vista 3D

ID: SPEC-008
Estado: implementada
Requisitos: PRD-01, PRD-04, TRD-07, TRD-09
Tareas: P4-04
Pruebas: T-27
Cambio: CAM-056
Evidencia: [reporte CAM-051](../../calidad/resultados/mapa-cartografico-3d-cam051.md), [reporte CAM-052](../../calidad/resultados/movimiento-mapa-cam052.md), [reporte CAM-053](../../calidad/resultados/limites-mapa-cam053.md), [reporte CAM-054](../../calidad/resultados/ampliacion-mapa-cam054.md), [reporte CAM-055](../../calidad/resultados/ampliacion-50km-mapa-cam055.md), [reporte CAM-056](../../calidad/resultados/reduccion-15km-mapa-cam056.md)

## Objetivo y alcance

Origen: el usuario indicó que el grafo SVG actual no le convence y pidió una base cartográfica real, con vista 3D si es posible. La cartografía base procede de OpenStreetMap mediante OpenFreeMap; MapLibre GL JS la renderiza. Navira conserva su grafo versionado y snapshots del servidor como capas de calles simuladas, rutas y actores. El mapa base no genera ni reemplaza las reglas/eventos estocásticos del mundo.

La primera implementación ofrece estilo oscuro, edificios extruidos cuando los tiles incluyen altura, inclinación 3D, cámara 2D/3D y atribución visible. No promete edificios modelados con exactitud, cobertura completa de Manta, terreno de alta resolución ni uso como guía de emergencia. La elevación derivada de OSM puede estar incompleta; OpenFreeMap declara su instancia pública como servicio sin SLA y “as-is”. No se consultan tiles durante la simulación ni se envían credenciales del motor al proveedor.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-008-01 | El mapa central carga cartografía vectorial con coordenadas de Manta, controles de zoom/rotación y atribución legible a OpenFreeMap/OpenMapTiles/OSM. | T-27 |
| CA-008-02 | Sobre el mapa base, las capas servidoras representan calles/bloqueos, rutas previstas y movimientos confirmados, refugios, sobrevivientes y zombies visibles en sus coordenadas. Los actores se distinguen como fichas identificables. | T-27 |
| CA-008-03 | La vista inclinada presenta extrusión 3D de huellas con altura disponible y permite alternar a 2D; datos de altura ausentes no se presentan como mediciones reales. | T-27 |
| CA-008-04 | Falla del proveedor/WebGL muestra un estado comprensible y la interfaz mantiene disponibles las estadísticas/control; el build de frontend compila. | T-27 |
| CA-008-05 | Cuando llega un snapshot de una partida en curso, cada actor cuya posición confirmada cambió se interpola por el trayecto entre nodos; respeta movimiento reducido y nunca modifica el estado del servidor. | T-27 |
| CA-008-06 | Al iniciar o reiniciar una partida, la cámara encuadra el fixture y el WebSocket sigue el nuevo `runId` sin exigir recarga o actualización manual. | T-27 |
| CA-008-07 | El mapa encuadra y limita la navegación a una ventana ampliada alrededor del recorte OSM del fixture Manta; cartografía fuera de esa ventana se oculta, no hay copias del mundo y no se puede alejar más que la vista general. La extensión es visual y no afirma ser el límite administrativo de Manta. | T-27 |

## Plan y límites

P4-04 sustituye la capa SVG por un componente MapLibre. Las transiciones visuales usan snapshots públicos consecutivos; no cambian el dominio, el contrato de `/paso`, el grafo versionado ni el estado autoritativo. El WebSocket vuelve a resolver el proveedor del panel durante la observación para seguir una partida local recién creada. Para calzar rutas curvas con la red real, una evolución debe conservar geometría completa OSM en el grafo público; esta versión conecta los nodos seleccionados con las coordenadas actuales.

La cámara, el límite de arrastre y la máscara visual usan la ventana descrita en [mapa-manta.md](../../dominio/mapa-manta.md), extendida aproximadamente 15 km por lado respecto del rectángulo de extracción OSM. El recorte evita mostrar tiles exteriores al área cartográfica seleccionada para la demo. La ventana no extiende el fixture de calles ni el territorio simulado. No es un polígono administrativo ni prueba que el fixture cubra todo Manta.

Validación manual en navegador con el proveedor de tiles accesible, compilación Vite/TypeScript y regresiones backend del canal de snapshots. No hay herramienta de test de componentes configurada. El mapa depende de conexión a internet para tiles; el uso público de OpenFreeMap no tiene SLA. El fixture de rutas sigue siendo parcial, y los refugios no están certificados para amenaza sísmica.
