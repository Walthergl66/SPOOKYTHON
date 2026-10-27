# ADR-031 — Perímetro zombie de una cuadra alrededor de refugios Manta

- Fecha: 2026-10-27.
- Estado: aceptada e implementada localmente; calibración geográfica pendiente.
- Origen: solicitud del usuario de impedir que los zombies se acerquen a las zonas seguras dentro de aproximadamente una cuadra por lado.
- Contexto: los zombies podían generarse en nodos adyacentes a los refugios y avanzar sobre ellos. La solicitud describe una distancia urbana aproximada, pero no define radio métrico por sitio.
- Decisión: en mapas Manta, considerar protegido el nodo refugio y toda intersección conectada directamente por cualquier sentido de calle. Excluir el búfer del muestreo inicial y descartar los pasos que entren a nodos protegidos. El búfer se deriva de la topología base y no se estrecha por cierres temporales. Los mapas sintéticos no geográficos conservan su comportamiento.
- Entidades ya dentro: ningún paso puede entrar más al área protegida; las entidades pueden quedarse o salir. No se altera la resolución de mordida ni se concede invulnerabilidad a sobrevivientes.
- Alternativas: radio geográfico métrico (sin parámetros validados por refugio); solo bloquear el nodo del refugio (no cubre la cuadra solicitada); aplicar el búfer a todos los mapas (fixtures sintéticos pequeños no representan cuadras reales).
- Consecuencias: caminantes y corredores reciben destinos limitados por un salto topológico; el corredor busca rutas sin atravesar nodos protegidos y usa sus salidas legales disponibles si el objetivo queda detrás del búfer. La regla afecta tanto al modo simulador como al juego porque ambos comparten el resolutor.
- Limitaciones: una arista OSM no equivale uniformemente a una cuadra. Los cuatro marcadores consultados son zonas seguras en mapas municipales de tsunami, lo que no certifica la zona ante sismos ni constituye guía de emergencia real.
- Archivos y trazabilidad: `domain/mapa.py`, `simulation/resolver.py`, `demo.py`, `test_resolver.py`, `test_demo.py`; PRD-11, TRD-16, SPEC-001 CA-001-12, T-40, CAM-078 y P-17.
- Evidencia: [reporte CAM-078](../../calidad/resultados/perimetro-refugios-cam078.md).
