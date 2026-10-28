# SPEC-011 — Demo pública multisesión

ID: SPEC-011  
Estado: en-revision  
Requisitos: PRD-13, TRD-19  
Tareas: P4-07, P5-02  
Pruebas: T-58  
Cambio: CAM-127  
Decisión: [ADR-046](../../arquitectura/decisiones/0046-demo-publica-multisesion.md)
Evidencia: [CAM-126 y CAM-127](../../seguimiento/cambios.md#cam-127-habilitar-los-tres-modos-en-la-demo-pública-y-publicar-la-revisión); suite externa completa pendiente.

## Objetivo y alcance

Permitir que una URL pública temporal deje a cualquier visitante usar Reto, Simulador y Jugar como operador, cada uno con un mundo aislado por cookie anónima. El backend conserva un único proceso/coordinador; la multisesión significa varios mundos independientes dentro del mismo proceso, no varias réplicas ni multijugador.

Las sesiones se guardan en memoria, con máximo por instancia, expiración tras tres horas inactivas y límites adicionales del proxy. Reinicio o despliegue elimina las partidas. No hay cuentas, persistencia, recuperación, escalado horizontal, SLA ni protección absoluta contra abuso automatizado. `/paso` conserva su API key y no se inserta una clave en el frontend.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-011-01 | Cada navegador recibe un token opaco distinto en cookie `HttpOnly`, `Secure` por HTTPS, `SameSite=Strict`; no se guarda en localStorage ni se retorna en JSON. | T-58 |
| CA-011-02 | Reto, Simulador y Jugar resuelven controles/panel/decisiones con el mundo asociado a esa cookie. Un visitante no puede reemplazar, pausar, leer ni colocar sobre el mundo de otro. | T-58 |
| CA-011-03 | Las operaciones mutables del navegador exigen `Origin` same-host; falta o discordancia se rechaza. El WebSocket de panel valida origen y resuelve sesión desde cookie. | T-58 |
| CA-011-04 | El límite concurrente por instancia es configurable y por defecto 3. Sin cupo, el bootstrap devuelve 429 con `Retry-After`; la sesión más antigua no se expulsa. | T-58 |
| CA-011-05 | El registro elimina y cierra controles inactivos tras 10.800 s. La cookie dura como máximo 24 h y es opaca; después de expirar el estado no se recupera. | T-58 |
| CA-011-06 | En Lightsail, frontend y backend se comunican internamente; solo el frontend expone HTTPS. Nginx limita peticiones de demo/panel por IP y conserva Upgrade para WebSocket. | T-58 |
| CA-011-07 | Dos sesiones simultáneas pueden iniciar mundos de Juego distintos y cada una sigue leyendo su propio `runId`. | T-58 |
| CA-011-08 | Se documenta la volatilidad, concurrencia limitada, costos temporales y eliminación del servicio AWS tras la demostración. | T-58 |

## Implementación y límites

El adaptador `RegistroSesionesDemoMemoria` guarda SHA-256 del token y asocia cada sesión con un coordinador compuesto; controles/dominio no reciben el token. El control automático y el juego humano usan mundos distintos dentro de la misma cookie; los endpoints de panel y órdenes resuelven servicios desde esa sesión. El contexto humano se crea de forma diferida al entrar a Jugar, y su reloj arranca después de la aparición del jugador. Cambiar a Simulador o Reto detiene el reloj humano para evitar que dos modos compitan dentro de la sesión. Middleware HTTP fija o renueva actividad para `/panel/`, `/demo/`, `/reto/`, `/juego/` y `/paso`; la cookie se emite al crear sesión. El frontend público espera el bootstrap `/demo/sesion` antes de montar el dashboard para evitar solicitudes iniciales sin identidad.

El perfil público se activa solo con `NAVIRA_PUBLIC_DEMO_CONTROL=1`. `NAVIRA_PUBLIC_MAX_SESSIONS` y `NAVIRA_PUBLIC_SESSION_IDLE_SECONDS` acotan recursos. En la implementación temporal vigente, Lightsail ejecuta backend y frontend como contenedores Docker con red host; Nginx del host termina TLS y proxifica a la interfaz en loopback, que enruta al backend. La instancia debe permanecer única porque coordinador y sesiones están en memoria. La URL usa `nip.io`, un nombre temporal de terceros, no un dominio propiedad del proyecto. Revisar [seguridad](../../operacion/seguridad.md), [infraestructura](../../operacion/infraestructura.md) y [costos](../../operacion/costos.md).

## Verificación y estado

T-58 valida aislamiento por cookie, inicio de mundos distintos, origen, capacidad, expiración y limpieza; una prueba ASGI del perfil público recorre Juego → Reto para un navegador, Simulador para otro y confirma `runId` distintos. La integración local de Podman con dos clientes y `nginx -t` pasan. La primera instancia de Lightsail responde en HTTPS y se verificaron salud, bootstrap, inicio humano y la carga de la interfaz. Tras reconstruir y publicar el backend con el enrutamiento de Jugar y la selección optimizada de aparición, falta repetir el smoke externo, probar WebSocket y completar revisión visual/carga; AWS no permite consultar el estado de recursos con el perfil CLI actual. No marcar esta SPEC verificada por builds o pruebas locales solamente.
