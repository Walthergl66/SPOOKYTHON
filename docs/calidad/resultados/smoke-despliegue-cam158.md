# Smoke del despliegue y cupos públicos — CAM-158

Fecha: 2026-10-28 (America/Guayaquil)  
Release: `7046ebcf89e7550569ecb8a2bcf1fa7d081ae1ee`  
URL: <https://3.17.253.59.nip.io>  
Infraestructura: Lightsail `us-east-2`, instancia `navira-public-demo`.

## Configuración confirmada

La configuración del host `/etc/navira/public.env` y el entorno efectivo del contenedor `navira-backend` indican `NAVIRA_PUBLIC_MAX_SESSIONS=4` y `NAVIRA_PUBLIC_SESSION_IDLE_SECONDS=900`. El archivo mantiene permisos `0600`. El código no cambió; sus defaults siguen siendo tres sesiones y 10.800 segundos. La cookie pública conserva `Secure`, `HttpOnly`, `SameSite=Strict` según el código de emisión; las pruebas locales cubren el atributo `HttpOnly`.

## Pruebas

| Comprobación | Resultado |
|---|---|
| Backend y frontend desplegados con el SHA | Sí; ambos contenedores en estado `Up` |
| `GET /salud` | HTTP 200, muestra externa única: 562,3 ms |
| `GET /` | HTTP 200, muestra externa única: 612,9 ms |
| Bootstrap de sesiones nuevas | Tres cookies distintas recibieron HTTP 200; tiempos observados: 1.895,5 ms, 8.081,5 ms y 4.969,9 ms |
| Intento de siguiente cupo | HTTP 429, cuerpo de capacidad llena, `Retry-After: 30` |
| Prueba local `test_public_demo.py` | 5/5 correctas; incluye cookie/aislamiento, límite y expiración con reloj controlado |

Un cupo estaba ocupado antes de crear las tres sesiones de smoke, por lo que no fue posible completar cuatro clientes nuevos desde cero. La saturación observada demuestra que el servicio rechaza clientes sobre su capacidad con 429, pero no identifica al cliente que ya ocupaba el cupo. No se expulsó ninguna sesión ni se reinició el backend después del smoke. Las tres sesiones de prueba se dejaron inactivas y deben vencer luego de 900 s; hasta entonces consumen cupos.

## Límites

No se esperaron 900 segundos para comprobar la expiración de producción ni se ejecutó una campaña de carga sostenida. Los tiempos HTTP incluyen red y TLS desde el entorno de prueba, no miden solo procesamiento del backend. Una muestra aislada de `/` y `/salud` excede 150 ms extremo a extremo, y el bootstrap público tardó de 1,9 a 8,1 s; esto no es un p95 válido, pero indica que el inicio de sesión/mundo merece un diagnóstico dedicado. No declarar el objetivo de latencia cumplido con estos datos.

El release se desplegó por SSH administrativo; la publicación automática desde GitHub Actions sigue pendiente de completar conectividad/rol según P-21. Las partidas y sesiones continúan en memoria, no sobreviven al despliegue o reinicio.
