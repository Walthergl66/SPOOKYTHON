# ADR-030 — Ventana urbana como zona jugable

- Fecha: 2026-10-27.
- Estado: aceptada e implementada localmente; revisión visual interactiva pendiente.
- Origen: solicitud del usuario de que el área fuera del límite mostrado deje de ser jugable y respuesta expresa de que el selector de refugios también se limite al recorte.
- Contexto: CAM-076 limitaba la cámara a `[-80.807, -1.082]`–`[-80.621, -0.897]`, pero las partidas aún usaban la red OSM completa; actores podían aparecer y moverse fuera de la vista. El selector admitía candidatos en toda la envolvente fuente.
- Decisión: para mapas `manta-osm-*`, derivar un mapa con nodos dentro de la caja WGS84 inclusiva y calles solo si sus dos extremos están dentro. Partidas, apariciones, amenazas, rutas y movimientos usan ese subgrafo; los refugios base deben sobrevivir al recorte y refugios personalizados exteriores se rechazan. El endpoint de candidatos publica los límites; el selector encuadra/muestra/acepta solo ubicaciones internas. El fixture OSM original se conserva completo e inmutable.
- Alternativas: dejar el recorte en presentación (no evitaría actores invisibles); borrar nodos fuera del archivo fuente (perdería cobertura reutilizable); mantener el selector amplio con validación solo al iniciar (mala retroalimentación visual).
- Consecuencias: el subgrafo tiene 35.518 nodos y 75.548 sentidos según el fixture comprobado; rutas exteriores ya no forman parte de partidas Manta. El borde es una caja aproximada derivada de la captura, no una frontera municipal certificada. Falta inspección visual del selector y la simulación en navegador.
- Documentos y módulos: `domain/mapa.py`, `demo.py`, endpoint local de candidatos, dominio frontend del selector, SPEC-008, PRD-01, TRD-15 y CAM-077.
- Referencias: [mapa Manta](../../dominio/mapa-manta.md), [SPEC-008](../../metodo/especificaciones/SPEC-008-mapa-cartografico-3d.md), [CAM-077](../../seguimiento/cambios.md#cam-077-ventana-urbana-como-limite-jugable).
