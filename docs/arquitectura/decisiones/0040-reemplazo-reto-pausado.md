# ADR-040 — Reemplazar una ronda Reto pausada al iniciar otro preset

- Estado: Sustituida por [ADR-044](0044-reemplazo-explicito-al-cambiar-de-modo.md) — CAM-106.
- Fecha: 2026-10-27.
- Contexto: el panel debe permitir continuar o sustituir una ronda Reto pausada por otro preset seleccionado. Una ronda activa no debe ser interrumpida y un simulador libre pausado no debe desaparecer al iniciar Reto.
- Decisión: `POST /reto/iniciar` puede reemplazar una partida previa únicamente si pertenece al modo Reto y está pausada. La operación crea un mundo y `runId` nuevos para el preset solicitado. Si hay una partida activa o una demo libre pausada, responde HTTP 409. `POST /reto/reiniciar` mantiene su función de recrear el mismo preset.
- Consecuencias: el panel conserva un botón primario según estado (iniciar/pausar/continuar), expone «Nueva simulación Rn» solo mientras el Reto actual está pausado y conserva «Reiniciar Rn». Una vez iniciada la nueva ronda, el mundo anterior queda sustituido en el almacén local volátil.
- Evidencia: [CAM-097](../../calidad/resultados/reto-nueva-simulacion-pausada-cam097.md); esta decisión aplica solo al control local opt-in/loopback y no amplía la API pública.
