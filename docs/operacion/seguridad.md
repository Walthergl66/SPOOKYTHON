# Seguridad y límites de confianza

Infraestructura activa: Vercel + Render según ADR-054/055. Las referencias AWS de esta página son antecedentes de seguridad de despliegues previos; no son procedimientos vigentes. CAM-161 retiró el workflow/artefactos AWS del repositorio. No hay evidencia sobre eliminación de cuentas, recursos, llaves o cargos remotos.

Estado: controles parciales. El panel HTTP y `WS /ws/panel` proyectan mapas versionados, zombies activos, movimientos visibles y métricas permitidas; no publican dormidos, semillas o RNG. `POST /juego/unirse` emite token opaco en cookie HttpOnly, Secure por defecto, SameSite=Strict y valida `Origin`. La demo pública usa cookie por navegador, TTL y sesiones efímeras; una reinicialización pierde los mundos. CAM-160 verificó en Producción Vercel `/salud` JSON 200; `/demo/sesion` y `/panel/estado` devolvieron 429 por el límite de una sesión ocupada, así que no se verificaron bootstrap/cookie, REST autenticado ni WebSocket. Mantener el límite y no reiniciar para desalojar una sesión activa; reintentar al liberar el cupo normalmente. El origen exacto está configurado y el socket exige same-host/allowlist, sin mensajes entrantes. Dominio propio, revocación/recuperación durable y smoke integrado siguen pendientes. Los despliegues Lightsail y sus reglas de seguridad son históricos; no se afirma su estado remoto actual. CAM-161 eliminó su pipeline del repo; ver P-25 para inventario AWS autorizado.

## Identidades

| Identidad | Mecanismo previsto | Alcance |
|---|---|---|
| Simulador de servicio | `x-api-key` | Consultar motor/estado técnico. |
| Jugador | Sesión temporal con cookie HttpOnly/Secure/SameSite | Solo su personaje y sus órdenes. |
| Espectador | Lectura pública o sesión de observación limitada | Proyección pública, sin modificar mundo. |
| Operador | Credencial administrativa independiente | Inicio, cierre y eventos. |
| Hosting de aplicación | Configuración gestionada en Vercel y Render | Proxy Vercel same-origin y backend Render de un proceso. |

Las claves de servicio y de operador nunca se incluyen en JavaScript público. No guardar valores reales en `.env.example`, Markdown, capturas, enlaces, historial de shell o logs. Registrar nombres de configuración, no secretos.

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
- **Historial AWS (CAM-113/ADR-045, CAM-126..131/ADR-046/047/050, CAM-158):** staging y evaluación Fargate, más demo Lightsail, se ejecutaron en el pasado. Los reportes registran límites de red, API key, cookie, TLS y smoke de esa topología. CAM-161 retiró su pipeline/artefactos del repo; no asumir que los servicios, secretos o reglas remotas fueron eliminados.
- CAM-159/160/ADR-054: `origen_mismo_host` acepta `Origin` same-host o URL HTTP(S) normalizada que coincida exactamente con `NAVIRA_ALLOWED_ORIGINS`; no admite prefijos ni comodines. Render está configurado con `https://navira-two.vercel.app`. El proxy same-origin permite que la cookie `SameSite=Strict` siga siendo first-party; no abrir CORS amplio. Prueba focalizada valida allowlist exacta localmente. En producción, `/salud` por Vercel dio 200, pero bootstrap/cookie y REST autenticado dieron 429 por cupo ocupado; WebSocket aún no se probó.

## Comentarios y documentación

Los ejemplos usan secretos ficticios. Si se descubre exposición, retirar el valor y gestionar rotación por el mecanismo autorizado; borrar texto sin rotar no elimina una filtración. Registrar el incidente sin repetir el secreto.

Los supuestos de seguridad pendientes van a [pendientes](../seguimiento/pendientes.md). No inventar aprobación externa o controles existentes. Pruebas de permisos, ocultación de dormidos y ausencia de credenciales en frontend forman parte de [pruebas](../calidad/pruebas.md).
