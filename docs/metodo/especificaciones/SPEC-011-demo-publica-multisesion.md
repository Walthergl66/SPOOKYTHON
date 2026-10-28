# SPEC-011 — Demo pública multisesión

ID: SPEC-011  
Estado: en-revision  
Requisitos: PRD-13, TRD-19  
Tareas: P4-07, P5-02  
Pruebas: T-58  
Cambio: CAM-126  
Decisión: [ADR-046](../../arquitectura/decisiones/0046-demo-publica-multisesion.md)

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

El adaptador `RegistroSesionesDemoMemoria` guarda SHA-256 del token y asocia cada sesión con su `ControlSimuladorDemoLocal`; controles/dominio no reciben el token. Middleware HTTP fija o renueva la actividad por solicitud para `/panel/`, `/demo/`, `/reto/` y `/paso`; la cookie se emite al crear sesión. El frontend público espera el bootstrap `/demo/sesion` antes de montar el dashboard para evitar solicitudes iniciales sin identidad.

El perfil público se activa solo con `NAVIRA_PUBLIC_DEMO_CONTROL=1`. `NAVIRA_PUBLIC_MAX_SESSIONS` y `NAVIRA_PUBLIC_SESSION_IDLE_SECONDS` acotan recursos. La imagen Nginx escucha en 8080 y enruta a `localhost:8000` dentro del mismo Container Service. El servicio debe permanecer en una sola réplica porque coordinador y sesiones están en memoria. Revisar [seguridad](../../operacion/seguridad.md), [infraestructura](../../operacion/infraestructura.md) y [costos](../../operacion/costos.md).

## Verificación y estado

T-58 valida aislamiento por cookie, inicio de mundos distintos, origen, capacidad, expiración y limpieza; Vitest/build comprueban la interfaz y la imagen. La integración local de Podman con dos clientes comprueba dos `runId` independientes. La publicación en Lightsail, TLS público real, smoke externo, comportamiento bajo carga/abuso, visual completo, métricas AWS y eliminación de recursos son criterios pendientes hasta que exista evidencia. No marcar esta SPEC verificada por builds o pruebas locales solamente.
