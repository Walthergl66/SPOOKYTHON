# ADR-054 — Hosting temporal con Vercel y Render Free

Fecha: 2026-11-06  
Estado: aceptada para implementación; despliegue real pendiente  
Origen: solicitud del usuario de publicar Navira en Vercel y usar un backend gratuito.

## Contexto

El tablero Vite hace solicitudes HTTP y abre `WS /ws/panel` en su mismo origen. Las cookies anónimas `SameSite=Strict` y la validación CSRF/origen también dependen de esa frontera. El backend conserva el coordinador, los controles y las sesiones en memoria, por lo que necesita una sola instancia y un único worker; invocaciones independientes no pueden repartir ese estado.

## Decisión

1. Preparar Vercel como hosting estático del directorio `frontend/`. Sus rewrites externos conservan las rutas del navegador (`/salud`, `/paso`, `/panel/*`, `/demo/*`, `/reto/*`, `/juego/*`, `/ws/*`) y las envían al servicio FastAPI de Render.
2. Preparar en `render.yaml` un servicio Python gratuito en Ohio, con un worker, `/salud` como health check y el perfil público efímero habilitado. Limitarlo a una sesión simultánea y 900 s de inactividad por instancia por los recursos reducidos del plan gratuito.
3. Mantener SameSite/HttpOnly/Secure en la cookie y aceptar, además del origen same-host, solo orígenes completos enumerados en `NAVIRA_ALLOWED_ORIGINS`. Configurar ahí el origen de producción exacto de Vercel; no usar comodines. No publicar `NAVIRA_API_KEY` en el bundle.
4. Incluir `frontend/.env.production` con `VITE_PUBLIC_DEMO=1` en el build Vercel para que el navegador obtenga una cookie antes de montar el panel y disparar solicitudes paralelas.

## Alternativas

- Mantener solo Lightsail: es el despliegue público verificado, pero incurre en costo y no satisface la solicitud de alternativa gratuita.
- Ejecutar el backend en funciones de Vercel: no se elige para este despliegue porque el estado autoritativo actual depende de una única instancia/proceso y del filesystem del paquete para cargar el mapa.
- Conectar el navegador directamente a un subdominio `onrender.com`: se evita porque fragmentaría el origen de las cookies `SameSite=Strict`; además, requeriría CORS para las llamadas HTTP. El proxy Vercel mantiene un único origen visible para el navegador.

## Consecuencias y límites

Render Free puede dormir el servicio tras 15 minutos sin tráfico, tardar alrededor de un minuto en despertar y reiniciarlo; su filesystem es efímero. Una caída o despliegue destruye partidas y sesiones en memoria. No se promete disponibilidad continua, persistencia, SLA o capacidad de producción. El plan Vercel Hobby está limitado por sus términos a uso personal/no comercial.

La configuración local apunta a `https://navira-api-walthergl66.onrender.com`; se debe comprobar que el servicio provisionado tenga exactamente ese hostname antes del despliegue. El dominio de producción Vercel todavía debe obtenerse y añadirse a `NAVIRA_ALLOWED_ORIGINS`. Ninguno de los dos proveedores se ha autenticado ni desplegado en CAM-159; el proxy REST/WebSocket, el bootstrap con cookie y el smoke externo siguen pendientes.

## Vínculos

[SPEC-011](../../metodo/especificaciones/SPEC-011-demo-publica-multisesion.md), [infraestructura](../../operacion/infraestructura.md), [seguridad](../../operacion/seguridad.md), [CAM-159](../../seguimiento/cambios.md#cam-159-preparar-despliegue-vercel-y-render-free).

Referencias de límites: [Render Free](https://render.com/docs/free), [WebSockets en Render](https://render.com/docs/websocket), [términos Vercel Hobby](https://vercel.com/legal/terms).
