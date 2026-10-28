# ADR-044 — Reemplazo explícito al iniciar otro modo

- Estado: aceptada e implementada localmente — CAM-106.
- Fecha: 2026-10-28.
- Origen: el usuario reportó que Jugar → Reto no permitía iniciar y pidió que cada modo nuevo comenzara desde cero.
- Requisitos: PRD-06; SPEC-009 CA-009-10/12 y SPEC-010 CA-010-09.

## Contexto

Navira mantiene un único run local compartido por Reto, Simulador y Juego operador. La interfaz y el endpoint de Reto impedían iniciar mientras había un run de otro modo activo o pausado. Además, el panel seguía mostrando la instantánea del modo anterior al cambiar de pestaña.

## Decisión

Cambiar de pestaña limpia selecciones, avisos y configuraciones transitorias, y oculta actores/métricas si el run vigente no corresponde al modo seleccionado. La pestaña no reemplaza ni pausa el run. Al confirmar la acción explícita de inicio del modo destino, el servidor crea un `runId` y mundo nuevos, reemplazando el run local anterior. El inicio de otro preset Reto no sustituye un Reto activo; este debe pausarse antes.

La política aplica a la demo local protegida por loopback y opt-in. No crea sesiones independientes concurrentes, no traslada estado entre modos y no amplía las rutas públicas.

## Consecuencias

- Jugar → Reto inicia el preset elegido sin que el run operador activo/pausado bloquee la petición.
- Reto → Jugar inicia un mundo vacío y habilita la paleta solo después de recibir el snapshot del run nuevo.
- Simulador inicia mediante su asistente y crea una partida según su configuración.
- El run previo deja de estar disponible en el almacenamiento local volátil tras confirmar el nuevo inicio.
- Un clic accidental en la pestaña no descarta el mundo.

## Evidencia

[CAM-106](../../seguimiento/cambios.md#cam-106-cambio-limpio-entre-modos) y T-57.
