# ADR-032 — Incidentes viales siempre activos en la demo local

- Fecha: 2026-10-27.
- Estado: aceptada e implementada localmente.
- Origen: solicitud del usuario de ocultar del menú los accidentes viales aleatorios y mantenerlos siempre activados.
- Decisión relacionada: [ADR-017](0017-perfiles-sinteticos-de-amenazas.md).

## Contexto

El control local permitía elegir si crear incidentes viales aleatorios. La persona usuaria pidió que el ajuste desaparezca de la interfaz y que los incidentes queden siempre activos. El endpoint local también debía impedir que un cliente anterior que envíe `eventosCiudad: false` los apague.

## Decisión

El tablero no ofrece selector ni guarda esa opción en `SimulatorSetup`; el frontend omite `eventosCiudad` al iniciar y reiniciar. `ControlSimuladorDemoLocal` siempre llama al generador con `eventos_ciudad=True`. El endpoint conserva el campo opcional legado para no romper clientes previos, pero no lo pasa al caso de uso y lo marca obsoleto en el esquema.

La decisión posterior [ADR-033](0033-alerta-y-cierres-aleatorios.md) fija el conteo aleatorio en 1–10, independiente de intensidad, y agrega el punto/alerta visible al aplicarse. El panel sigue ocultando todos los cierres futuros. Generadores y herramientas de evaluación que invocan directamente `crear_contexto_demo` conservan su configuración explícita.

## Alternativas

- Ocultar solo el selector y depender del valor por defecto del navegador: descartada porque una petición antigua aún podría desactivar eventos.
- Rechazar toda petición que contenga el campo legado: descartada para conservar compatibilidad con clientes locales previos.
- Forzar eventos en todos los generadores y evaluadores: descartada porque la solicitud se refiere al menú/control de la demo y la evaluación requiere configuraciones explícitas.

## Consecuencias y verificación

Los nuevos controles locales no permiten iniciar una partida sin incidentes; los clientes antiguos reciben el mismo resultado aunque envíen `false`. T-43 comprueba que iniciar/reiniciar mantienen `eventosCiudad=true` en la respuesta y que el cliente ya no envía el campo. Los tests de escenarios mantienen la posibilidad de omitir incidentes fuera del control de demo.

Documentos propietarios: [SPEC-007](../../metodo/especificaciones/SPEC-007-panel-operador-local.md), [contrato API](../contratos/api.md), [módulos frontend](../modulos/frontend.md), [pruebas](../../calidad/pruebas.md) y CAM-081. La cantidad, calendario, cierre/replanificación y alerta visual vigentes se definen en [ADR-033](0033-alerta-y-cierres-aleatorios.md).
