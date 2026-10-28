# Seguridad y límites de confianza

Estado: controles parciales. El panel HTTP y `WS /ws/panel` proyectan mapas versionados, zombies activos, movimientos visibles y métricas permitidas; no publican dormidos, semillas o RNG. `POST /juego/unirse` emite token opaco en cookie HttpOnly, Secure por defecto, SameSite=Strict y solo acepta Origin del mismo host. CAM-046 añade a la demo un TTL deslizante local configurable de 30 minutos, respuesta 410 y tombstone de propiedad para impedir transferencia tras expirar; no es persistente y se pierde al reiniciar. La demo temporal Lightsail tiene HTTPS en Nginx/Certbot; la revisión `ddfa843f81c9cb87732d56b4a1f5b59cf0ee4665` fue desplegada por SSH administrativo y `/` y `/salud` respondieron 200. GitHub Actions #50 no alcanzó SSH desde el runner hospedado; no se amplió el firewall. Dominio propio, política productiva de revocación/recuperación y CD automatizado siguen pendientes (P-11/P-12/P-21). El handshake del socket exige `Origin` del mismo host y no permite mensajes entrantes. Esto reduce solicitudes browser cross-origin, pero no sustituye límites de conexiones/frecuencia, política de red o controles de producción.

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
- CAM-036/CAM-046: cookie de unión protegida por `HttpOnly`, `Secure` por defecto, `SameSite=Strict`, `Path=/juego`; CSRF/origen controlado mediante host coincidente. No configurar `NAVIRA_COOKIE_SECURE=0` fuera de test/desarrollo local. En la demo local `NAVIRA_GAME_SESSION_IDLE_SECONDS` configura TTL deslizante (1800 s por defecto); 410 notifica expiración y tombstone evita transferir cupo. Sesiones/tombstones no sobreviven reinicios ni coordinan procesos.
- CAM-037: `POST /juego/accion` repite la comprobación de `Origin` y autoriza por token de cookie comparado con la sesión propietaria. El cuerpo no otorga identidad, control ni posición; el servidor valida fase/turno/mapa y el mismo destino solo expresa espera. La clave idempotente y su secuencia residen en memoria: no cubren varios workers ni una carrera atómica contra el cierre de turno (P-16).
- Rol de ejecución y de aplicación separados según funciones; permisos limitados a tabla, logs y configuración necesarios.
- CAM-050: el control de simulador solo se ensambla con `NAVIRA_LOCAL_DEMO_CONTROL=1`, exige conexión loopback y Host local; en POST, `Origin` y Host deben pertenecer al conjunto `localhost`, `127.0.0.1`, `::1` para que el proxy Vite local pueda usar cualquiera de los alias. Orígenes externos siguen rechazados. El flag no se configura en despliegue. Esto limita la demo local y no sustituye autenticación de operador productivo.
- CAM-113/ADR-045: staging privado restringe el origen por red y `/paso` exige API key. Los controles locales permanecen apagados; la tarea efímera de evaluación no recibe permiso para modificar staging ni acepta tráfico entrante público. El diseño debe materializarse y probarse en CloudFormation/AWS.
- CAM-126/127/ADR-046: la demo pública temporal se habilita con `NAVIRA_PUBLIC_DEMO_CONTROL=1`, fuera del flag local. Cookie por navegador `HttpOnly`, `SameSite=Strict`, `Secure` en HTTPS y token aleatorio guardado como hash; máximo tres sesiones por instancia por defecto, TTL deslizante de tres horas, cookie como máximo 24 horas, estado efímero. Mutaciones y WebSocket exigen origen same-host; Nginx limita rutas públicas a 5 solicitudes/segundo/IP con ráfagas acotadas. No inyectar `NAVIRA_API_KEY` al bundle y mantener `/paso` protegido. Esta superficie permite a cualquiera operar su mundo temporal; no es autenticación/antibot productiva y el límite por IP puede afectar usuarios detrás de NAT. Supervisar métricas/logs y eliminar la instancia al cerrar el evento.
- CAM-129/131/ADR-047: GitHub Actions solo intenta desplegar desde `master` después de pasar suites y build. El run #50 confirmó checks, construcción de imágenes y validación de host key, pero el runner hospedado agotó el tiempo al conectar por SSH porque Lightsail solo admite el origen administrativo. La revisión `ddfa843f81c9cb87732d56b4a1f5b59cf0ee4665` se instaló manualmente desde ese origen; no se abrió SSH a `0.0.0.0/0`. La clave privada SSH y `known_hosts` fijado se guardan como Actions secrets; la API key de servicio permanece en `/etc/navira/public.env` con permisos `0600`, no se imprime ni transfiere al runner. CD automático sigue bloqueado hasta establecer conectividad restringida (P-21).

## Comentarios y documentación

Los ejemplos usan secretos ficticios. Si se descubre exposición, retirar el valor y gestionar rotación por el mecanismo autorizado; borrar texto sin rotar no elimina una filtración. Registrar el incidente sin repetir el secreto.

Los supuestos de seguridad pendientes van a [pendientes](../seguimiento/pendientes.md). No inventar aprobación externa o controles existentes. Pruebas de permisos, ocultación de dormidos y ausencia de credenciales en frontend forman parte de [pruebas](../calidad/pruebas.md).
