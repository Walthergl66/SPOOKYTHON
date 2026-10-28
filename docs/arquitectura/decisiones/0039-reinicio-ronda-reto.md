# ADR-039 — Reinicio explícito de la ronda Reto actual

- Estado: aceptada para implementación local.
- Fecha: 2026-10-27.
- Contexto: el panel Reto permitía iniciar presets, pero no reiniciar la partida como el control de demo libre. Reutilizar `POST /demo/simulador/reiniciar` perdería el identificador `ronda_reto` y convertiría la ronda en demo.
- Decisión: agregar botón “Reiniciar Rn” cuando el estado del operador contiene una ronda Reto y `runId`, y exponer `POST /reto/reiniciar` bajo la misma protección de loopback/origen. El servidor conserva ronda, población, perfil e intensidad provisionales, detiene el reloj anterior y crea una instancia de partida/semilla aleatoria con `runId` nuevo. Puede reiniciar una ronda activa, pausada o finalizada; sin una ronda Reto vigente devuelve HTTP 409. La selección y reporte de la ronda se sincronizan con `rondaReto` devuelta por el servidor.
- Alternativas: reutilizar el endpoint de demo, que pierde el preset; añadir parámetro opcional al contrato de inicio, mezclando inicio y reinicio; exigir que la ronda esté pausada, que añade pasos al usuario sin proteger un recurso externo.
- Consecuencias: `/reto/iniciar` sigue rechazando sustituir partidas activas/pausadas; el endpoint nuevo queda en el control local opt-in y no forma parte del API público. Reiniciar crea un mundo aleatorio nuevo; no implica replay del estado previo ni campaña de quince minutos.
- Verificación: T-47/CAM-095 prueba reinicio desde R2 pausada, nuevo `runId`, preset 80 y conflicto sin partida Reto; prueba de cliente verifica endpoint.
- Referencias: [SPEC-009](../../metodo/especificaciones/SPEC-009-modo-reto.md), [API](../contratos/api.md), [modos](../../dominio/modos.md).
