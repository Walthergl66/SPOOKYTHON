# ADR-014 — Expiración local de sesión humana

- Estado: aceptada para la demo local; no es política de producción.
- Fecha: 2026-10-26.
- Origen: cierre parcial de P-12 en SPEC-004, por continuación autorizada del usuario.
- Decisión anterior relacionada: [ADR-013](0013-sesion-y-aparicion-humana-local.md).

## Contexto

CAM-043 recupera una sesión por cookie dentro del proceso, pero la sesión no caduca. P-12 exige limitar la vida inactiva sin permitir que un visitante distinto controle al personaje ya aparecido. El adaptador actual es en memoria, sirve solo al juego sintético y se pierde al reiniciar.

## Decisión

En `RepositorioSesionesMemoria`, aplicar un plazo deslizante de inactividad de 30 minutos, configurable en el ensamblaje demo mediante `NAVIRA_GAME_SESSION_IDLE_SECONDS`. Usar reloj monotónico. Una lectura/autorización válida renueva el plazo; la sesión se marca vencida al alcanzar el límite. Las rutas de unión, recuperación y acción responden HTTP 410 para la cookie vencida.

Al expirar, retirar el secreto verificable y la sesión activa, pero conservar una reserva local por partida como tombstone: ni la cookie vieja puede crear otro personaje ni una cookie nueva puede apropiarse del sobreviviente o liberar su cupo. La reserva solo se limpia cuando el proceso/libro de sesiones termina explícitamente; la demo no expone revocación ni transferencia.

## Alternativas consideradas

- No expirar: conserva la propiedad, pero deja sesiones abandonadas activas indefinidamente.
- Liberar el personaje automáticamente: permite que otra cookie reciba un segundo sobreviviente y puede dejar un personaje humano sin dueño.
- Guardar expiración durable compartida: sería el destino productivo correcto, pero DynamoDB, recuperación y coordinación entre procesos aún no existen.

## Consecuencias y límites

- El plazo configurable y la respuesta 410 dan un comportamiento local comprobable y renovable por actividad.
- El tombstone preserva el límite de un humano por partida incluso tras la expiración.
- Un reloj monotónico solo tiene sentido dentro del proceso. La expiración y el tombstone se pierden al reiniciar; no hay restauración, revocación administrativa ni transferencia segura.
- No desplegar el juego basándose en esta política. Antes de publicación se requieren persistencia durable, ciclo de vida/revocación explícitos, TLS/origen y pruebas multi-proceso.

## Evidencia

Implementación y pruebas locales T-25: [CAM-046](../../seguimiento/cambios.md#cam-046-expiración-local-de-sesión-humana).
