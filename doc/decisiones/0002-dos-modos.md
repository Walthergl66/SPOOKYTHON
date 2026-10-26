# ADR-002 — Dos modos sobre un único mundo

Fecha: 2026-10-26. Estado: alcance solicitado por el usuario; diseño inicial adoptado, sin código.

## Contexto

Además del simulador exigido, el usuario quiere entrar como personaje, aparecer aleatoriamente y llegar a un refugio, manteniendo la posibilidad de ejecutar solo simulación.

## Decisión

Selector «Simulador / Jugar». En simulador todos los sobrevivientes son automáticos. En juego, uno usa órdenes humanas y los demás el motor. Ambas políticas generan intenciones validadas por el mismo resolutor, grafo y reloj. Modos fijos por partida, reportes separados y ningún jugador en rondas oficiales.

Primera versión: un personaje humano por partida, sesión temporal, un paso por turno, espera, ayuda opcional de radio y resultado. La aparición se valida y se incorpora antes de fase zombie. El mundo continúa al desconectar.

## Alternativas y motivo

Duplicar un juego independiente haría divergir reglas y duplicaría pruebas. Movimiento libre continuo cambiaría las reglas del grafo. Multijugador simultáneo aumenta propiedad, sesiones y carga; queda para ampliación solicitada.

## Consecuencias

Se necesitan órdenes idempotentes, cierre humano y recuperación de sesión. El p95 del motor se mide separado del plazo de entrada humana. El modo juego no sustituye la demostración automática del reto.

Documentos propietarios: [modos](../modos.md), [jugador](../flujos/jugador.md) y [API](../contratos/api.md). Pendiente P-12.
