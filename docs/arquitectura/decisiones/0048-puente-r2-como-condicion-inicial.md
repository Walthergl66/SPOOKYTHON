# ADR-048 — Aplicar el puente colapsado de R2 desde el inicio

- Fecha: 2026-10-28.
- Estado: aceptada e implementada localmente.
- Origen: reporte del usuario: el incidente del puente no se habilita correctamente en R2.
- Contexto: el reto exige que R2 tenga un puente colapsado, pero no indica el turno. La implementación anterior lo programaba para el turno 50 (aprox. 100 segundos). Las rondas pueden terminar antes y el evento no aparecería ni influiría en las rutas.
- Decisión: representar el puente como condición inicial de R2 y programar su cierre en turno 0. La preparación del primer turno aplica cierres antes de exponer el mundo a la primera decisión, el movimiento de habitantes y la proyección del panel. El puente se selecciona reproduciblemente entre los segmentos Manta etiquetados como puente.
- Alternativas consideradas: mantener turno 50 (puede no ocurrir); usar un turno temprano distinto de cero (todavía depende de que la ronda siga activa); cerrar el puente directamente al crear el snapshot inicial (duplicaría el mecanismo actual de aplicación de eventos y su alerta).
- Consecuencias y límites: primera decisión/ruta ya respeta el cierre y el panel puede reportar el incidente desde el primer snapshot preparado. El turno 0 es una decisión de implementación, no un requisito confirmado por la organización. R3 mantiene cierres en vivo provisionales en turnos 50/100. El panel inicial previo a la primera preparación no debe mostrarlo como aplicado.
- Pendientes: confirmar con la organización el momento oficial del colapso y mantener T-47/CAM-130 actualizado si el criterio cambia.
- Documentos y módulos propietarios: `simulation/escenarios.py`, SPEC-009/CA-009-03, reglas de juego, T-47, P-15 y App de Reto.
- Evidencia de implementación/verificación: CAM-130; prueba `test_presets_de_reto_respetan_tipos_y_eventos_reproducibles` comprueba el objetivo turno 0 y el cierre aplicado antes de la primera decisión.
