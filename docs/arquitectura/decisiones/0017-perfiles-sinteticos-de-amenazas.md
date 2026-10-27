# ADR-017 — Perfiles sintéticos de amenazas espaciales

Fecha: 2026-10-26  
Estado: aceptada para demo local  
Origen: el usuario pidió que el simulador presente amenazas por casi toda el área jugable para comparar evacuaciones; el perfil `mixto` actual solo creaba dos zombies.

## Contexto

La cantidad inicial de zombies estaba fija por nombre de escenario (`caminantes`, `mixto`, `horda`) y no escalaba con el grafo de Manta. El reto no especifica una densidad oficial, y P-07 deja pendiente el movimiento de hordas. Las rutas automáticas deben evitar solo amenazas visibles del snapshot confirmado; los dormidos no se publican.

## Decisión

La demo local ofrece intensidades sintéticas `baja`, `media` y `alta`, basadas en proporciones configurables del conjunto de nodos elegibles que no están ocupados al inicio. En `alta`, 25 % de nodos disponibles producen entidades zombie iniciales; `media` usa 14 % y `baja` 6 %. Los nodos se seleccionan con muestreo estratificado en una grilla geográfica para dispersar los focos y la semilla controla composición, posiciones y fases. Las proporciones por escenario preservan perfiles caminante, mixto y horda; `libre` no crea zombies.

La demo puede programar cierres viales aleatorios, con un cierre de segmento por incidente en turnos 2, 5 y 8 según intensidad. Se utiliza el `EventoCierre` existente, el snapshot versionado y la proyección pública de cierres. El panel publica metadatos solo de incidentes ya aplicados; nunca su ubicación futura ni dormidos. Estos eventos son simulaciones de cierres viales genéricos, no terremotos, tsunamis ni información oficial.

Los porcentajes y eventos son controles de dificultad del prototipo. No se extrapolan a la población ni a condiciones reales de Manta y no congelan parámetros para las rondas oficiales.

## Alternativas

- Mantener dos zombies fijos: descartada porque no estresa rutas por la red.
- Elegir nodos totalmente uniformes: sencilla, pero puede dejar grandes zonas sin amenazas; se prefiere cubrir sectores geográficos sin volver determinista la colocación.
- Anunciar terremotos/tsunamis como eventos: descartada hasta disponer de fuentes, reglas y validación competente; un cierre vial sintético es el incidente disponible.

## Consecuencias y límites

La UI permite ajustar intensidad y activar/desactivar cierres viales. Con la misma versión, mapa, perfil, intensidad, semilla y configuración de eventos se reproduce la inicialización. Cambios de algoritmo pueden alterar replay entre versiones. Las hordas siguen estáticas y pueden bloquear nodo/vecinos según la regla existente. El panel muestra únicamente los dormidos después de activarse.

Documentos propietarios: [SPEC-001](../../metodo/especificaciones/SPEC-001-mundo-simulacion.md), [reglas](../../dominio/reglas-juego.md), [demo](../../dominio/flujos/simulador.md), [contrato API](../contratos/api.md), [algoritmos](../algoritmos.md) y [pendientes](../../seguimiento/pendientes.md).
