# SPEC-008 — Mapa cartográfico real con vista 3D

ID: SPEC-008
Estado: en-revision
Requisitos: PRD-01, PRD-04, TRD-07, TRD-09, TRD-15
Tareas: P1-01, P4-04
Pruebas: T-27, T-38, T-39, T-59
Cambio: CAM-134
Evidencia: [límite jugable CAM-077](../../calidad/resultados/limite-jugable-cam077.md), [ventana urbana CAM-076](../../calidad/resultados/ventana-urbana-cam076.md), [cobertura CAM-073](../../calidad/resultados/cobertura-manta-cam073.md), [margen de navegación CAM-074](../../calidad/resultados/margen-navegacion-5km-cam074.md), [mar visible CAM-075](../../calidad/resultados/mar-visible-cam075.md), [reportes CAM-051..056](../../calidad/resultados/)

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
| CA-008-06 | Al iniciar o reiniciar una partida, la cámara abre en la ventana urbana enfocada, ofrece «Vista urbana»/«Ver partida» y el WebSocket sigue el nuevo `runId` sin exigir recarga o actualización manual. «Ver partida» enfoca actores y refugios visibles dentro de esa ventana. | T-27 |
| CA-008-07 | La cámara y la máscara del mapa principal se limitan al recorte aproximado `[-80.807, -1.082]`–`[-80.621, -0.897]`, estimado desde la referencia visual. «Vista urbana» lo encuadra y el pan/zoom no muestra tiles fuera. Este recorte es además el límite jugable definido en CA-008-10, no una frontera administrativa. | T-27, T-39 |
| CA-008-08 | El grafo del servidor cubre la zona jugable ampliada con calles públicas OSM conectadas en dirección a refugios; las fuentes/versión quedan identificadas y la cobertura/latencia tienen límites explícitos. | T-38 |
| CA-008-09 | La cartografía del proveedor permanece visible dentro del viewport urbano fijado y los polígonos/canales de agua se distinguen del terreno; el recorte opaco comienza fuera de esa ventana. La vista y el selector usan el mismo recorte. | T-27, T-39 |
| CA-008-10 | En partidas Manta, el grafo de juego excluye nodos fuera de la ventana y calles que crucen su borde; inicios, zombies, rutas y movimientos solo usan ese subgrafo. El selector encuadra la misma ventana, solo ofrece nodos internos y el endpoint rechaza una selección exterior. El fixture fuente ampliado permanece intacto. | T-39 |
| CA-008-11 | Al entrar a la app, el componente MapLibre monta el mapa vacío y la cartografía base comienza a cargar mientras se configura una partida, sin esperar al snapshot de actores. La geometría del juego se conserva en caché de módulo por `mapVersion`, limitada a las dos versiones recientes e incluida cuando un snapshot indique `sin_partida`; los actores, eventos y rutas dinámicos solo proceden del snapshot vigente. El shell y controles siguen montados durante la carga. Cambiar de modo o `runId` no debe borrar ni volver a descargar una geometría válida. Una carga fallida debe informar el estado y permitir recuperación. | T-59 |

## Plan y límites

CAM-073 amplió el fixture fuente a la envolvente OSM. CAM-077 fija la ventana estimada por el usuario como zona jugable y recorta el mapa de partida; conserva el fixture original para candidatos/contexto, pero el selector solo muestra y acepta ubicaciones dentro de la ventana. Plan de CAM-077: derivar el subgrafo en dominio, validar refugios y movimientos contra él, exponer límites al selector, probar recorte y rechazo de puntos externos y registrar la evidencia. El cambio no certifica la caja como polígono municipal ni OSM como red exhaustiva.

P4-04 sustituye la capa SVG por un componente MapLibre. Las transiciones visuales usan snapshots públicos consecutivos; no cambian el dominio, el contrato de `/paso`, el grafo versionado ni el estado autoritativo. El WebSocket vuelve a resolver el proveedor del panel durante la observación para seguir una partida local recién creada. Para calzar rutas curvas con la red real, una evolución debe conservar geometría completa OSM en el grafo público; esta versión conecta los nodos seleccionados con las coordenadas actuales.

CAM-134 monta `CityMap`/MapLibre desde la entrada de la app sobre un mapa vacío, mientras la cartografía base se carga durante la configuración. La geometría del mapa de juego queda en caché de módulo indexada por versión y limitada a las dos versiones recientes; `usePanel` la conserva al recibir `sin_partida`, sin conservar por ello capas de actores/rutas/eventos de una sesión anterior. Esta separación debe seguir asociando datos dinámicos al snapshot vigente. No se midió el tiempo hasta mapa visible, no se ejecutó smoke visual ni se comprobó recuperación del proveedor; la reducción de espera permanece sin verificar. La precarga no conserva estado de partida ni sustituye las comprobaciones de mapVersion/runId.

CAM-073 conserva la envolvente OSM amplia en el artefacto fuente. CAM-076 introdujo la ventana urbana visual; CAM-077 la aplica también a la zona jugable derivada y al selector. La caja se estima desde la referencia del usuario y no equivale a límite administrativo; los tiles siguen dependiendo de OpenFreeMap.

Validación CAM-073: suite de datos/cobertura, equivalencia del campo de rutas con Dijkstra, `npm test`, compilación, validadores documentales y recorrido local con partida iniciada; véase el [reporte](../../calidad/resultados/cobertura-manta-cam073.md). Quedan por medir el payload/cadencia objetivo y la falla controlada de tiles/WebGL; por eso esta SPEC permanece parcial. No hay herramienta de test de componentes configurada. El mapa depende de conexión a internet para tiles; el uso público de OpenFreeMap no tiene SLA. El fixture de rutas sigue siendo parcial, y los refugios no están certificados para amenaza sísmica.
