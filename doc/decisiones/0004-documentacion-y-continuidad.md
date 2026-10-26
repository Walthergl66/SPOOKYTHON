# ADR-004 — Documentación modular y continuidad obligatoria

Fecha: 2026-10-26. Estado: adoptada en la documentación; verificación mediante comprobador local.

## Contexto

El usuario pide conservar todo el contexto por área, registrar cambios y permitir que un agente nuevo retome trabajo tras revisar los Markdown de `doc/`.

## Decisión

`doc/` es la ubicación canónica, con índice y documento propietario por asunto. `AGENTS.md` raíz ordena lectura inicial de los `.md`, inspección del repositorio y actualización de documentación al cerrar. Contexto recoge intención; estado actual recoge evidencia; cambios conserva historial; ADR explica decisiones; pendientes conserva incertidumbres.

Preservar texto del reto y plan anterior como referencias identificadas. Mantener en la antigua ruta del plan un enlace de compatibilidad, sin una segunda copia editable. Añadir plantillas y un comprobador de enlaces/inventario.

## Alternativas y consecuencias

Un único documento grande dificulta localizar responsabilidad y se desactualiza por duplicación. Guardar todo solo en chats impide continuidad sin historial. La modularización exige actualizar enlaces/índice, pero permite verificar documentación y reanudar desde un resumen comprobable.

Los históricos no prevalecen sobre instrucciones actuales. El registro incluye motivos y resultados, no deliberación interna, secretos o datos privados. Un cambio de documentación no constituye una implementación de la app.

Documentos propietarios: [índice](../README.md), [continuidad](../continuidad.md), [cambios](../cambios.md) y [AGENTS.md](../../AGENTS.md).
