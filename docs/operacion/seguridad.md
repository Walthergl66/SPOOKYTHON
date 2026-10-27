# Seguridad y límites de confianza

Estado: controles parciales. El panel HTTP y `WS /ws/panel` proyectan mapas versionados, zombies activos, movimientos visibles y métricas permitidas; no publican dormidos, semillas o RNG. `POST /juego/unirse` emite token opaco en cookie HttpOnly, Secure por defecto, SameSite=Strict y solo acepta Origin del mismo host. CAM-046 añade a la demo un TTL deslizante local configurable de 30 minutos, respuesta 410 y tombstone de propiedad para impedir transferencia tras expirar; no es persistente y se pierde al reiniciar. La política productiva de revocación/recuperación y TLS/despliegue siguen pendientes (P-11/P-12). El handshake del socket exige `Origin` del mismo host y no permite mensajes entrantes. Esto reduce solicitudes browser cross-origin, pero no sustituye límites de conexiones/frecuencia, TLS, política de red o controles de producción.

## Identidades

| Identidad | Mecanismo previsto | Alcance |
|---|---|---|
| Simulador de servicio | `x-api-key` | Consultar motor/estado técnico. |
| Jugador | Sesión temporal con cookie HttpOnly/Secure/SameSite | Solo su personaje y sus órdenes. |
| Espectador | Lectura pública o sesión de observación limitada | Proyección pública, sin modificar mundo. |
| Operador | Credencial administrativa independiente | Inicio, cierre y eventos. |
| Runtime AWS | Rol IAM | Recursos precisos del entorno. |

Las claves de servicio y de operador nunca se incluyen en JavaScript público. No guardar valores reales en `.env.example`, Markdown, capturas, enlaces, historial de shell o logs. Registrar nombres de configuración, no secretos. Acceso AWS y valores deben obtenerse por mecanismos autorizados de la sesión.

El mapa base de CAM-051 carga tiles externos de OpenFreeMap para la vista visible. Esa solicitud revela al proveedor la IP y el área cartográfica consultada conforme a la operación normal del navegador; no incorpora IDs, posiciones, snapshots ni credenciales del juego. Las capas de Navira se agregan en el cliente y se consultan solo al backend Navira. La atribución permanece visible. Si se sustituye el proveedor o se añade una clave, revisar [ADR-016](../arquitectura/decisiones/0016-mapa-maplibre-openfreemap.md) y no incluir secretos privados en el bundle.

## Validaciones

- Validar cuerpos, IDs existentes, partida/turno/fase, adyacencia y propiedad en servidor.
- Aplicar idempotencia y versión en órdenes; no confiar en reloj o posición enviada por navegador.
- Validar origen/CSRF para sesiones del navegador y origen en handshake WebSocket. CORS no es autorización.
- Limitar recomendaciones, creación de sesiones y eventos; evitar que un visitante degrade `/paso`.
- No revelar estado privado mediante errores, trazas, archivos descargables o herramientas del frontend.
- Sanitizar alias si se muestran; limitar longitud. No hace falta recoger datos personales para jugar.
- Verificar TLS y permisos del origen; limitar entrada por red y validar cabecera de origen.
- CAM-036/CAM-046: cookie de unión protegida por `HttpOnly`, `Secure` por defecto, `SameSite=Strict`, `Path=/juego`; CSRF/origen controlado mediante host coincidente. No configurar `NAVIRA_COOKIE_SECURE=0` fuera de test/desarrollo local. En la demo `NAVIRA_GAME_SESSION_IDLE_SECONDS` configura el TTL deslizante (1800 s por defecto); 410 notifica expiración y el tombstone evita transferir el cupo. Sesiones/tombstones no sobreviven reinicios ni coordinan procesos; P-11/P-12/P5-02 impiden declarar el juego listo para publicación.
- CAM-037: `POST /juego/accion` repite la comprobación de `Origin` y autoriza por token de cookie comparado con la sesión propietaria. El cuerpo no otorga identidad, control ni posición; el servidor valida fase/turno/mapa y el mismo destino solo expresa espera. La clave idempotente y su secuencia residen en memoria: no cubren varios workers ni una carrera atómica contra el cierre de turno (P-16).
- Rol de ejecución y de aplicación separados según funciones; permisos limitados a tabla, logs y configuración necesarios.
- CAM-050: el control de simulador solo se ensambla con `NAVIRA_LOCAL_DEMO_CONTROL=1`, exige conexión loopback y Host local; en POST, `Origin` y Host deben pertenecer al conjunto `localhost`, `127.0.0.1`, `::1` para que el proxy Vite local pueda usar cualquiera de los alias. Orígenes externos siguen rechazados. El flag no se configura en despliegue. Esto limita la demo local y no sustituye autenticación de operador productivo.

## Comentarios y documentación

Los ejemplos usan secretos ficticios. Si se descubre exposición, retirar el valor y gestionar rotación por el mecanismo autorizado; borrar texto sin rotar no elimina una filtración. Registrar el incidente sin repetir el secreto.

Los supuestos de seguridad pendientes van a [pendientes](../seguimiento/pendientes.md). No inventar aprobación externa o controles existentes. Pruebas de permisos, ocultación de dormidos y ausencia de credenciales en frontend forman parte de [pruebas](../calidad/pruebas.md).
