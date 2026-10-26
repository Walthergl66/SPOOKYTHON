# Dataset geográfico de Manta

Estado: fixture de simulación exportado y probado; cobertura representativa de toda la zona de juego aún pendiente. Última actualización: 2026-10-26. Código de exportación: [`scripts/exportar_mapa_manta.py`](../scripts/exportar_mapa_manta.py). Artefactos: [`manta-hackathon-v1.json`](../data/maps/manta-hackathon-v1.json) y [metadatos de fuentes](../data/maps/manta-hackathon-v1.fuentes.json).

## Procedencia y alcance

Las calles parten de la API de datos de OpenStreetMap, recortada al rectángulo WGS84 sur `-0.967`, oeste `-80.755`, norte `-0.935`, este `-80.675`. El artefacto generado contiene 300 nodos y 599 sentidos dirigidos de calle; la geometría conserva intersecciones, extremos y anclas. La licencia y atribución ODbL se guardan junto al archivo. Los límites de velocidad ausentes en OSM se sustituyen con valores internos de juego del exportador; no son mediciones ni límites oficiales de tránsito.

Cuatro destinos se transcribieron de las capas “Zonas Seguras” de los mapas de evacuación por tsunami publicados por la Dirección de Ambiente y Riesgos del GAD Manta:

| ID | Lugar | Parroquia | Ajuste a red vial |
|---|---|---|---:|
| R-01 | Parque y cancha municipal Cristo Rey | Tarqui | 37,3 m |
| R-02 | Parque Colinas de Rocafuerte | Los Esteros | 43,4 m |
| R-03 | Parque La Dolorosa | Manta | 32,9 m |
| R-04 | Plaza del Sol | Manta | 35,1 m |

Fuentes oficiales del mapa de evacuación: [parroquia Manta](https://darf-manta.github.io/evacuacion-tsunami/parroquia-manta.html), [Tarqui](https://darf-manta.github.io/evacuacion-tsunami/parroquia-tarqui.html) y [Los Esteros](https://darf-manta.github.io/evacuacion-tsunami/parroquia-los-esteros.html). La publicación municipal describe GeoManta como herramienta de cartografía e infraestructura local: [GAD Manta](https://manta.gob.ec/geomanta-una-herramienta-para-la-formacion-academica/). La selección del fixture se limita a marcadores publicados como zonas seguras para tsunami; los puntos de encuentro no se intercambian con destinos finales.

## Amenazas y uso

La evidencia consultada sustenta que estos cuatro puntos aparecen como “Zona Segura” en los mapas oficiales de evacuación por tsunami. No prueba vigencia operativa, accesibilidad en una emergencia, capacidad, rutas actualmente transitables ni seguridad ante terremotos. **La seguridad sísmica no está evaluada**: falta una fuente local de microzonificación, condiciones del suelo y validación estructural de cada ubicación. Navira no debe presentar el fixture como instrucción real de evacuación ni como recomendación de refugio ante un sismo.

El selector del exportador parte de los cuatro refugios y amplía en dirección inversa sobre la red dirigida, por lo que cada uno de los 300 nodos incluidos tiene al menos un camino dirigido al refugio. Esto es una propiedad del grafo exportado, no una garantía de ruta real, seguridad, conectividad peatonal ni acceso durante una amenaza. Caminos peatonales no etiquetados como vías motorizadas pueden no estar incluidos. La prueba de integridad está en [`tests/test_mapa_manta.py`](../tests/test_mapa_manta.py).

Regenerar con `python3 scripts/exportar_mapa_manta.py` requiere acceso de red a la API pública de OSM. Cada exportación cambia el timestamp y puede cambiar la versión del mapa si los datos fuente cambian; revisar los dos artefactos y sus pruebas antes de sustituir el fixture.

El fixture también alimenta una ejecución exploratoria del simulador automático con perfiles sintéticos y cohortes de 20/80/200; resultados y límites de esa ejecución constan en [CAM-025](resultados/simulacion-manta-cam025.md). Esto prueba compatibilidad técnica del grafo con Dijkstra/resolutor, no exactitud de la cartografía ni seguridad de los refugios.
