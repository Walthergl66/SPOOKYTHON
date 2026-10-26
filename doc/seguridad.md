# Seguridad y límites de confianza

Estado: requisitos de implementación, no controles ya verificados.

## Identidades

| Identidad | Mecanismo previsto | Alcance |
|---|---|---|
| Simulador de servicio | `x-api-key` | Consultar motor/estado técnico. |
| Jugador | Sesión temporal con cookie HttpOnly/Secure/SameSite | Solo su personaje y sus órdenes. |
| Espectador | Lectura pública o sesión de observación limitada | Proyección pública, sin modificar mundo. |
| Operador | Credencial administrativa independiente | Inicio, cierre y eventos. |
| Runtime AWS | Rol IAM | Recursos precisos del entorno. |

Las claves de servicio y de operador nunca se incluyen en JavaScript público. No guardar valores reales en `.env.example`, Markdown, capturas, enlaces, historial de shell o logs. Registrar nombres de configuración, no secretos. Acceso AWS y valores deben obtenerse por mecanismos autorizados de la sesión.

## Validaciones

- Validar cuerpos, IDs existentes, partida/turno/fase, adyacencia y propiedad en servidor.
- Aplicar idempotencia y versión en órdenes; no confiar en reloj o posición enviada por navegador.
- Validar origen/CSRF para sesiones del navegador y origen en handshake WebSocket. CORS no es autorización.
- Limitar recomendaciones, creación de sesiones y eventos; evitar que un visitante degrade `/paso`.
- No revelar estado privado mediante errores, trazas, archivos descargables o herramientas del frontend.
- Sanitizar alias si se muestran; limitar longitud. No hace falta recoger datos personales para jugar.
- Verificar TLS y permisos del origen; limitar entrada por red y validar cabecera de origen.
- Rol de ejecución y de aplicación separados según funciones; permisos limitados a tabla, logs y configuración necesarios.

## Comentarios y documentación

Los ejemplos usan secretos ficticios. Si se descubre exposición, retirar el valor y gestionar rotación por el mecanismo autorizado; borrar texto sin rotar no elimina una filtración. Registrar el incidente sin repetir el secreto.

Los supuestos de seguridad pendientes van a [pendientes](pendientes.md). No inventar aprobación externa o controles existentes. Pruebas de permisos, ocultación de dormidos y ausencia de credenciales en frontend forman parte de [pruebas](pruebas.md).
