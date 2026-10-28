# ADR-036 — Consultar bajo demanda la ruta del habitante seleccionado

- Estado: aceptada para implementación local.
- Fecha: 2026-10-27.
- Contexto: la ficha de selección solo recibía rutas desde `rutasPrevistas`, que se publican durante `decisiones`. CAM-092 amplió la proyección a toda la población y todas las fases; el smoke de Manta mostró alto uso de CPU porque el motor repetía cálculos para cientos de habitantes en cada snapshot.
- Decisión: conservar rutas compartidas en snapshots de fase `decisiones`. En simulador automático fuera de esa fase, consultar individualmente `GET /panel/ruta/{sobreviviente_id}` para el habitante seleccionado. La respuesta identifica run, turno, versión de snapshot y sobreviviente; frontend solo acepta/reutiliza el resultado dentro del mismo run/turno/persona. Juego humano conserva la condición de fase de decisiones.
- Alternativas consideradas: mantener rutas de toda la población en todas las fases (sobrecarga observada); calcular el camino en el navegador (duplicaría política y podría usar información o reglas distintas); ocultar la ruta fuera de decisiones (no satisface selección útil durante el Reto).
- Consecuencias: snapshots generales evitan el trabajo masivo fuera de decisiones y la interacción agrega una consulta de solo lectura al seleccionar o al comenzar un nuevo turno. El endpoint debe reutilizar el mismo planificador/datos observables y nunca publicar estado de dormidos o RNG privado. La ruta es recomendación, no garantía de seguridad ni movimiento confirmado.
- Verificación: CAM-093 y T-45 cubren el caso de uso, el contrato HTTP, validación de respuesta y presentación en ficha/mapa. No acredita cadencia global ni evaluación de producción.
- Referencias: [CAM-093](../../seguimiento/cambios.md#cam-093--calcular-bajo-demanda-la-ruta-del-habitante-seleccionado), [API](../contratos/api.md), [flujo espectador](../../dominio/flujos/espectador.md).
