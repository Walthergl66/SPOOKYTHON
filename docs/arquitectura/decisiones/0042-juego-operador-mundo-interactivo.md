# ADR-042 — «Jugar» como modo de operador en un mundo vivo

- Estado: aceptada para la demo local.
- Fecha: 2026-10-27.
- Origen: el usuario confirmó que la nueva experiencia de «Jugar» debe ser de operador: elegir herramientas y colocarlas en el mapa mientras el mundo avanza.
- Requisitos: PRD-06, PRD-12, TRD-18.
- Especificación: [SPEC-010](../../metodo/especificaciones/SPEC-010-juego-operador.md).

## Contexto

La navegación tenía Reto, Simulador y Jugar humano. La solicitud del usuario redefine la tercera experiencia como operación interactiva. Las reglas del reto exigen mantener sus rondas automáticas separadas; las entidades, fases y resolutor ya pertenecen a un dominio con dos modos (`simulador`, `juego`).

## Decisión

«Jugar» presenta un modo operador que controla un mundo automático local: iniciar/pausar/continuar, escoger habitante, caminante, corredor, horda, dormido, refugio o incidente y colocarlo con un clic en nodo/calle. El servidor valida la acción y actualiza el snapshot; los incidentes cierran la vía para que el motor comparta el nuevo estado. Las acciones se bloquean en Reto y en partidas pausadas.

Se conservan los dos modos de dominio. La demo de operador se ejecuta en `simulador`; Reto es un flujo de evaluación sobre el mismo modo automático. El modo de dominio `juego` y sus API humanas no se borran en esta fase, pero dejan de ser la experiencia principal vinculada a «Jugar».

La implementación local sigue protegida por `NAVIRA_LOCAL_DEMO_CONTROL=1`, loopback y Origin same-host. No es un control productivo. Intervenciones de zombies respetan nodo y vecinos de refugio; un refugio nuevo crea una versión de mapa, y una calle con incidente se cierra en el snapshot.

## Alternativas consideradas

- Mantener a «Jugar» como control de personaje: no responde a la confirmación actual del usuario.
- Crear un tercer modo de dominio: duplicaría el motor automático sin necesidad; el cambio es una experiencia de operación encima de `simulador`.
- Aplicar colocaciones solo en el navegador: podría mostrar entidades que no existen para el servidor y rompería la autoridad del snapshot.

## Consecuencias y límites

- Reto, Simulador y Jugar tienen objetivos de interfaz separados; las reglas/resolución automática siguen compartidas.
- El reloj y el endpoint local deben serializar la intervención con el turno y confirmar por CAS.
- Intervenciones son locales, volátiles y no aptas para publicar en AWS.
- Las sesiones/API humanas existentes quedan sin enlace principal hasta que se decida retirarlas o recuperarlas en una experiencia futura.
- La colocación y la evolución de la ciudad no equivalen a una recomendación real de emergencia.

## Evidencia

Implementación y verificación parcial en CAM-101; véanse [pruebas](../../calidad/pruebas.md) y [estado actual](../../seguimiento/estado-actual.md).
