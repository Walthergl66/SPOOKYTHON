# ADR-035 — Flujo de evaluación separado de la demo libre

Fecha: 2026-10-27. Estado: aceptada para diseño.

## Origen y contexto

El usuario pidió una opción específica para cumplir la prueba de fuego y mantener el simulador como demo libre. Hoy hay dos modos de dominio —automático y humano— y un control local de demo. La prueba de fuego, sin embargo, necesita tres configuraciones de población/tipos/eventos propias y métricas distintas del juego.

## Decisión

Agregar un flujo de interfaz «Reto» que configura la campaña de evaluación sobre el modo automático existente. No crear otro modo de partida, motor, API pública ni resolver. Mantener «Simulador» como demo libre y «Jugar» como experiencia humana. Identificar los valores de densidad/eventos no definidos por el enunciado como supuestos reproducibles, configurables por versión/semilla y pendientes de confirmación.

## Alternativas consideradas

- Reutilizar el formulario de demo: mezclaría presets y métricas, y permitiría configuraciones que no corresponden a cada ronda.
- Crear un tercer modo de dominio: duplicaría reglas y contradice el contrato de modos compartidos de ADR-002.
- Fijar cantidades zombies/eventos como oficiales: el texto del reto no proporciona esos valores.

## Consecuencias y límites

El frontend necesita estado/controles de campaña separados. Backend debe preparar presets y eventos por ronda reproducibles. Un run local en memoria no es la ejecución oficial en AWS; duración objetivo, latencia y disponibilidad solo pueden afirmarse con mediciones verificadas. No se cambia `POST /paso`.

## Documentos propietarios

[PRD](../../producto/PRD.md), [modos](../../dominio/modos.md), [SPEC-009](../../metodo/especificaciones/SPEC-009-modo-reto.md), [SPEC-005](../../metodo/especificaciones/SPEC-005-aws-evaluacion.md).
