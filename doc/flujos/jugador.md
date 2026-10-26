# Flujo del jugador

Estado: sesión/aparición y órdenes locales en CAM-036/037; UI inicial en CAM-038; coordinador local parcial en CAM-039. El ciclo consume órdenes, pero todavía no hay runner con deadline/reloj ensamblado y el juego no es end-to-end. Contratos: [API](../contratos/api.md). Reglas: [mundo](../reglas-juego.md).

## Entrar

1. Seleccionar «Jugar». Comprobar partida de juego habilitada y cupo de control.
2. Crear/recuperar sesión temporal segura; alias opcional. Un segundo visitante observa, no toma el personaje ocupado.
3. Registrar solicitud de aparición; incorporarla al inicio de un turno antes del movimiento zombie. Si ya pasó esa fase, esperar el siguiente turno y mostrarlo.
4. Seleccionar aleatoriamente nodo transitable, fuera de refugios, sin solapamiento zombie inicial y con camino vigente a un refugio. No garantizar que siga siendo seguro después.
5. Confirmar personaje/nodo; si no hay candidatos, informar y no inventar un punto inválido.

CAM-036 implementa `POST /juego/unirse` por inyección de aplicación, una cookie HttpOnly/Secure/SameSite estricta y una aparición aleatoria reproducible al usar el RNG privado del servidor únicamente dentro del coordinador de aparición. Solo considera sobrevivientes y zombies activos para evitar dar al jugador acceso a dormidos; requiere ruta vigente a refugio y excluye refugios/ocupación. Si la fase ya no es PREPARACION, la sesión queda pendiente; el coordinador aún debe llamar `incorporar_aparicion_pendiente()` antes de mover zombies en el siguiente turno. No hay expiración/revocación confirmadas ni persistencia durable.

CAM-037 implementa `POST /juego/accion`: la sesión se valida desde la cookie y se contrasta con run/personaje. En `DECISIONES` se acepta espera o calle vecina abierta; bloqueo de horda se rechaza, pero el riesgo de zombie activo no invalida una intención. La última orden válida de ese personaje/turno sustituye la previa; el mismo `accionId` y cuerpo devuelve el acuse original, uno distinto produce conflicto. Secuencia y estado se calculan en el servidor. El acuse no afirma movimiento confirmado. El adaptador es local y el coordinador todavía no consume órdenes ni comparte cierre atómico con el registro; el corte temporal del turno sigue pendiente en P-16.

CAM-038 ofrece entrada explícita y botones para esperar o elegir una calle dirigida abierta. Usa estado del snapshot para la posición; no permite elegir durante una fase distinta, conexión desactualizada o al ver solo modo simulador. Tras un reintento de red reutiliza el mismo `accionId`. El modo demo predeterminado no tiene sesión de juego ensamblada, así que mostrará que no hay partida jugable; la interfaz no crea ni altera una partida por sí misma.

CAM-039 incorpora `CoordinadorJuego`: confirma aparición pendiente antes de mover zombies, abre/retoma `DECISIONES`, toma la última orden humana del turno (o espera si no existe), pide decisión a los NPC y confirma todas las intenciones con el mismo resolutor y CAS. El mismo `RLock` debe inyectarse en coordinador y servicio de órdenes para serializar resolución/registro; su alcance es un proceso. El coordinador expone pasos explícitos y todavía no programa el cierre de 1,7 s ni un bucle de dos segundos. No se debe invocar `resolver()` antes del cierre temporal al añadir el runner.

## Elegir una acción

1. Recibir estado observable de la fase de decisión y hora límite del servidor.
2. Elegir vecino o espera. Mostrar peligros conocidos y sugerencia opcional de la radio.
3. Enviar orden con partida, turno, personaje e ID de acción.
4. Mostrar «enviando»; después «recibida» solo tras confirmación persistida. Permitir reemplazarla hasta el cierre.
5. Ignorar duplicados y rechazar órdenes de otro turno o sesión. El orden se resuelve mediante secuencia del servidor, no el reloj del navegador.
6. Mostrar el movimiento al recibir el resultado autoritativo. Muchos clics no producen pasos extra.

Solo se cambia destino cuando existe una nueva orden válida recibida dentro del plazo. Una orden inválida no elimina otra válida ya confirmada. Sin orden, espera; no activar control automático por sorpresa.

## Desconexión y final

El mundo continúa sin el navegador. Al reconectar se recupera la sesión y una instantánea completa: el personaje pudo esperar, llegar o morir. No volver a crear otro personaje por refrescar. La radio y el panel usan solo información observable.

Estados: `esperando_aparicion → activo → evacuado | mordido`; una interrupción de partida se comunica por separado. Un timeout del cliente no es una victoria ni una derrota por sí mismo. Al terminar mostrar motivo, turnos y distancia; regresar al selector sin reiniciar una partida ajena.

Aceptación: recorrido completo con teclado y mouse, aparición válida, órdenes idempotentes, un paso por turno, reconexión sin revivir y reglas iguales a las de NPC.
