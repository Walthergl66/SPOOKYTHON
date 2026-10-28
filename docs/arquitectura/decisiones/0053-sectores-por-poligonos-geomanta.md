# ADR-053 — Asignar sectores de refugios mediante polígonos GeoManta

- Fecha: 2026-10-28, America/Guayaquil.
- Estado: aceptada e implementada localmente; T-66 e inspección visual pendientes.
- Origen: el usuario pidió asignar a cada refugio el nombre real del sector según su ubicación, en vez del punto oficial más cercano.
- Requisitos: PRD-01/04, SPEC-008 CA-008-02, P4-04, T-66.

## Contexto

CAM-145/146 asociaban nombres a cuatro anclajes oficiales o al anclaje más cercano. Esa distancia no identifica el límite real de un barrio y podía presentar un nombre territorial incorrecto para un refugio personalizado. GeoManta expone públicamente por WFS capas poligonales de barrios y parroquias, con CRS de origen EPSG:32717 y nombres/códigos.

## Decisión

Usar un snapshot local versionado de las capas GeoManta `workspace_geomanta:geo_barrio`/`geo_parroquia` y seis límites parroquiales CONALI del Geoportal EEQ, transformados a EPSG:4326. El cliente compara coordenadas de refugio con polígonos: muestra el barrio nombrado que contiene el punto y la parroquia asociada; si el barrio no tiene nombre o no existe, recurre primero a parroquia GeoManta y después a parroquia CONALI. Si ninguna geometría contiene el punto, muestra «Sector no identificado». No inferir por distancia a otro refugio.

El archivo se carga desde el mismo origen de Navira una vez que hay un mapa Manta con refugios. No se consulta el GeoServer en cada snapshot y las fronteras no se añaden como capa visual; el snapshot se usa solo para clasificar coordenadas.

## Alternativas consideradas

- Consultar GeoServer en cada carga: descartada por disponibilidad externa, latencia y dependencia durante la operación.
- Mantener cuatro anclajes y calcular el más próximo: descartada porque la cercanía no prueba pertenencia territorial.
- Mostrar solo parroquia: válida como respaldo, pero pierde el nombre del barrio disponible en GeoManta.

## Consecuencias y límites

- Los refugios oficiales y personalizados reciben un nombre por ubicación dentro del snapshot; los 231 polígonos de barrio tienen 221 nombres y los restantes usan la parroquia.
- El snapshot contiene 231 polígonos de barrio (221 nombrados), 10 de parroquia GeoManta y seis de parroquia CONALI. El cruce con el fixture cuenta 35.480/35.518 nodos jugables (99,89 %) dentro de al menos un polígono parroquial; 38 puntos quedan fuera.
- Fuentes: [GeoManta WFS](https://geo.manta.gob.ec/geoserver-proxy/workspace_geomanta/wfs) y [capa parroquial CONALI](https://geoportal.eeq.com.ec/arcgis/rest/services/WEBGIS/Visor_cartografia/MapServer/24), consultadas el 2026-10-28; copia local en `frontend/public/data/manta-sectores-2026-10-28.geojson`.
- La fuente no declara licencia abierta en los metadatos consultados. Se conserva atribución al GAD y se debe confirmar autorización antes de redistribuir estos límites fuera del proyecto.
- La clasificación no certifica vigencia legal, dirección postal, seguridad del refugio ni exactitud catastral. Fuera de las geometrías no se inventa un sector.
- El asset tiene 1.648.942 bytes sin comprimir y 468.825 bytes con gzip local; medir transferencia comprimida en el servidor objetivo. La carga ocurre en segundo plano al disponer de refugios.

## Documentos y evidencia

SPEC-008 CA-008-02, prueba T-66, [dataset Manta](../../dominio/mapa-manta.md), [módulo frontend](../modulos/frontend.md), [cambio CAM-147](../../seguimiento/cambios.md). Build TypeScript/Vite correcto; validación territorial automatizada y visual pendiente.
