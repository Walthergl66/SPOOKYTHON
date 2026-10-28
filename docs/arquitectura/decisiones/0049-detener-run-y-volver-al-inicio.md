# ADR-049 — Detener el run y volver a la entrada inicial

- Fecha: 2026-10-28.
- Estado: aceptada e implementada localmente.
- Origen: solicitud del usuario de reemplazar el control visible de reinicio con una acción que pare por completo la simulación y deje la aplicación como al entrar.
- Contexto y restricciones: el RelojSimuladorLocal serializa turnos y el panel observa el run vigente por HTTP/WebSocket. Reiniciar crea un mundo nuevo; pausar conserva el mundo. Ninguna de esas acciones equivale a abandonar y limpiar la partida actual.
- Decisión: `POST /demo/simulador/detener` señaliza el reloj actual antes de esperar el lock del turno; el turno iniciado termina, no se abre uno posterior, luego se limpia el contexto visible y se devuelve `sin_partida`. El frontend reemplaza el reinicio visible de Reto por «Detener simulación», también ofrece la acción en Simulador y Juego, limpia estado de selección y vuelve a Reto/R1. Se conserva el endpoint anterior de reinicio de Reto para compatibilidad, no como botón de UI.
- Alternativas consideradas y motivo de selección: pausar mantendría run y actores; crear una partida vacía tendría un `runId` activo y no retornaría a `sin_partida`; reiniciar seguiría creando otro mundo. La operación de cierre satisface el regreso real a la pantalla inicial.
- Consecuencias, límites y costos: perder el estado volátil es intencional y el siguiente inicio genera una partida nueva. La operación puede esperar a que concluya el turno actual. No cambia `/paso`, las reglas ni la duración de rondas oficiales.
- Supuestos y pendientes relacionados: el cierre de un mundo operador devuelve también a la entrada inicial, mientras que «Iniciar nueva partida» permanece disponible para reemplazarlo por otro mundo vacío. Verificar endpoint, WebSocket y recorrido visual mediante T-26, T-48 y T-56.
- Documentos y módulos propietarios afectados: SPEC-007, SPEC-009, SPEC-010, contrato API, flujos de modos/operador y módulos backend/frontend.
- Evidencia de implementación/verificación: CAM-136; validación automatizada y recarga local pendientes.
- Sustituye / sustituida por: el control visible de reinicio en Reto (ADR-039 sigue describiendo el endpoint de compatibilidad).
