# ADR-033 — Cierres viales aleatorios con alerta cartográfica

- Fecha: 2026-10-27.
- Estado: aceptada e implementada localmente para la demo.
- Origen: solicitud del usuario de anunciar cada incidente en el mapa, cerrar la zona y recalcular recomendaciones, con 1–10 incidentes sorteados al inicio.
- Relacionadas: [ADR-017](0017-perfiles-sinteticos-de-amenazas.md), [ADR-032](0032-incidentes-viales-siempre-activos-en-demo.md).

## Contexto

La demo local siempre generaba cierres, pero la cantidad dependía de intensidad (1, 2 o 3), el panel solo publicaba ID/turno/causa y el mapa no ubicaba ni anunciaba el incidente. El coordinador ya aplicaba el cierre antes de mover zombies y abrir decisiones; el motor y las rutas previstas consumen ese mismo snapshot. La mejora debe conservar esa autoridad y no revelar el calendario futuro.

## Decisión

1. Al crear cada partida con incidentes habilitados, el RNG privado sortea uniformemente una cantidad entre 1 y 10, acotada por el número de segmentos físicos disponibles. Muestrea segmentos sin reemplazo y agenda un cierre cada tres turnos desde el turno 2 (2, 5, …, 29). Semilla, versión, mapa y configuración idénticos reproducen cantidad, segmentos y calendario. La intensidad zombie no altera el conteo.
2. En el turno objetivo, el coordinador agrega el segmento al snapshot cerrado antes de mover zombies y antes de publicar la fase de decisiones. El planificador recalcula para esa versión y toda ruta prevista evita los cierres efectivos. El cierre persiste hasta terminar la partida.
3. `GET /panel/estado` y `WS /ws/panel` incluyen únicamente incidentes aplicados. Cada evento publica ID, turno, causa genérica, segmento y punto medio WGS84 (`lat`, `lng`). No publican cantidad ni posiciones futuras.
4. El mapa muestra el segmento cerrado con su capa de vía cerrada y añade un punto amarillo con “!”. El punto pulsa mientras el mapa está en movimiento normal y queda estático con `prefers-reduced-motion`. Al aplicarse un evento, un aviso accesible en el mapa anuncia turno y causa durante ocho segundos; el punto permanece mientras dure el snapshot/partida.
5. La regla corresponde a cierres viales sintéticos genéricos. No modela choques reales, sismos, tsunamis ni peligro de emergencia. Los generadores directos/evaluadores mantienen su parámetro explícito; el control de demo local permanece siempre activo según ADR-032.

## Alternativas consideradas

- Depender solo del color rojo de la vía: descartado porque no identifica con claridad el punto del evento ni genera una alerta.
- Enviar el calendario completo al navegador al iniciar: descartado porque anticipa eventos no aplicados.
- Elegir la cantidad según intensidad: descartado por la instrucción actual de sortear 1–10 al inicio; intensidad sigue describiendo solo la presión zombie.
- Cambiar rutas en el navegador: descartado; el backend es autoridad y ya recomputa el plan desde el snapshot que contiene el cierre.

## Consecuencias y límites

- La misma transición confirma cierre, marcador/aviso y rutas actualizadas. No se duplica una búsqueda ni se cambia el contrato `POST /paso`.
- Si un mapa tiene menos de diez segmentos disponibles, el máximo real es ese total; el mapa Manta de demo contiene más de diez.
- Los eventos siguen siendo efímeros con el snapshot en memoria y el aviso se deriva del último snapshot al reconectar. No hay historial durable ni reapertura de vías.
- La posición se representa en el punto medio de una arista OSM contraída; es un indicador del tramo del grafo, no una geocodificación de accidente real.

## Documentos propietarios

[PRD](../../producto/PRD.md), [TRD](../../producto/TRD.md), [reglas](../../dominio/reglas-juego.md), [flujo del simulador](../../dominio/flujos/simulador.md), [SPEC-001](../../metodo/especificaciones/SPEC-001-mundo-simulacion.md), [SPEC-003](../../metodo/especificaciones/SPEC-003-panel-vivo.md), [SPEC-007](../../metodo/especificaciones/SPEC-007-panel-operador-local.md), [API](../contratos/api.md), [eventos](../contratos/eventos.md), [pruebas](../../calidad/pruebas.md), CAM-082.
