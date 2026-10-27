# ADR-017 — Perfiles sintéticos de amenazas espaciales

Fecha: 2026-10-26  
Estado: aceptada para demo local  
Origen: el usuario pidió que el simulador presente amenazas por casi toda el área jugable para comparar evacuaciones; el perfil `mixto` actual solo creaba dos zombies.

## Contexto

La cantidad inicial de zombies estaba fija por nombre de escenario (`caminantes`, `mixto`, `horda`) y no escalaba con el grafo de Manta. El reto no especifica una densidad oficial, y P-07 deja pendiente el movimiento de hordas. Las rutas automáticas deben evitar solo amenazas visibles del snapshot confirmado; los dormidos no se publican.

## Decisión

La demo local ofrece intensidades sintéticas `baja`, `media` y `alta`, basadas en proporciones configurables del conjunto de nodos elegibles que no están ocupados al inicio. En `alta`, 25 % de nodos disponibles producen entidades zombie iniciales; `media` usa 14 % y `baja` 6 %. Los nodos se seleccionan con muestreo estratificado en una grilla geográfica para dispersar los focos y la semilla controla composición, posiciones y fases. Las proporciones por escenario preservan perfiles caminante, mixto y horda; `libre` no crea zombies.

La decisión original permitía activar o desactivar cierres viales aleatorios desde el control local. CAM-081 sustituye esa parte: en la demo operada desde el tablero los cierres se generan siempre y el usuario ya no puede desactivarlos. Se conserva `EventoCierre`, el snapshot versionado y la proyección pública; el panel publica metadatos solo tras aplicar cada incidente, nunca ubicaciones futuras ni dormidos. Los cierres son simulaciones genéricas, no terremotos, tsunamis ni información oficial. Los generadores de escenarios y evaluaciones fuera de este control local conservan sus parámetros explícitos.

Los porcentajes son controles de dificultad del prototipo. La demo local mantiene incidentes siempre activos, pero cantidad, posición y calendario se sortean por partida con el RNG privado; el conteo de 1–10 es independiente de la intensidad zombie y está detallado en [ADR-033](0033-alerta-y-cierres-aleatorios.md). No se extrapola a la población ni a condiciones reales de Manta y no congela parámetros para las rondas oficiales.

## Alternativas

- Mantener dos zombies fijos: descartada porque no estresa rutas por la red.
- Elegir nodos totalmente uniformes: sencilla, pero puede dejar grandes zonas sin amenazas; se prefiere cubrir sectores geográficos sin volver determinista la colocación.
- Anunciar terremotos/tsunamis como eventos: descartada hasta disponer de fuentes, reglas y validación competente; un cierre vial sintético es el incidente disponible.

## Consecuencias y límites

La UI permite ajustar intensidad; los incidentes viales de la demo están siempre activos. Con la misma versión, mapa, perfil y semilla se reproduce la inicialización. La regla de cantidad/calendario de cierres fue ampliada por ADR-033. Cambios de algoritmo pueden alterar replay entre versiones. Las hordas siguen estáticas y pueden bloquear nodo/vecinos según la regla existente. El panel muestra únicamente los dormidos después de activarse.

Documentos propietarios: [SPEC-001](../../metodo/especificaciones/SPEC-001-mundo-simulacion.md), [reglas](../../dominio/reglas-juego.md), [demo](../../dominio/flujos/simulador.md), [contrato API](../contratos/api.md), [algoritmos](../algoritmos.md) y [pendientes](../../seguimiento/pendientes.md).

Alcance actualizado: [ADR-032](0032-incidentes-viales-siempre-activos-en-demo.md) sustituye la configuración visible; [ADR-033](0033-alerta-y-cierres-aleatorios.md) sustituye el conteo/calendario ligados a intensidad y define la alerta cartográfica. El parámetro HTTP legado se ignora.
