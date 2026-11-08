# Infraestructura y operación

Estado vigente (CAM-161): **Vercel + Render son la única infraestructura activa de Navira.** Vercel aloja el frontend y hace proxy same-origin al backend Render Free de Ohio, un worker y una instancia. La rama Production de Vercel es `master`. Render conserva el estado efímero en memoria; no hay persistencia, escalado horizontal ni disponibilidad garantizada. Ver [ADR-054](../arquitectura/decisiones/0054-hosting-vercel-render-free.md) y [ADR-055](../arquitectura/decisiones/0055-retirar-aws-como-infraestructura-activa.md).

CAM-160 confirmó Render service `navira-api-walthergl66-v9ux` (`srv-dbnb4dbrjlhs7389k8sg`), deployment `dep-dbnb5849v7es73c96qi0` live y `/salud` HTTP 200. Vercel Production deployment observado `b06e9f9` respondió `/` HTML 200 y `/salud` JSON 200. Production Branch Tracking está configurado a `master`; guardar no lanza deploy. El siguiente push a `master` debe producir el siguiente deployment. En la última prueba, `/demo/sesion` y `/panel/estado` por Vercel dieron 429 por el cupo de una sesión ocupado; bootstrap/cookie, REST autenticado y WebSocket no se comprobaron. No reiniciar el backend ni aumentar el límite para desalojar una sesión. Los detalles y evidencia están en [CAM-160](../seguimiento/cambios.md#cam-160-provisionar-render-y-publicar-frontend-vercel-inicial).

## Operación de Vercel + Render

- `render.yaml` declara el servicio FastAPI en Ohio con un worker, health check `/salud`, modo demo pública, una sesión y TTL ocioso de 900 s. El filesystem y los mundos son efímeros; suspensiones/reinicios pierden partidas.
- `frontend/vercel.json` proxifica REST y WebSocket al hostname Render confirmado `https://navira-api-walthergl66-v9ux.onrender.com`. Las cookies se conservan en el origen Vercel.
- `NAVIRA_ALLOWED_ORIGINS` en Render debe contener el origen de Producción `https://navira-two.vercel.app` exactamente. No usar comodines ni exponer `NAVIRA_API_KEY` en `VITE_*`.
- Vercel Production sigue la rama `master`. Los pull requests no deben considerarse publicación Production; comprobar el deployment después de un push elegible.
- Tras cambios de hosting revisar `/salud`, bootstrap/cookie, mutaciones, REST autenticado, `WS /ws/panel`, reconexión y arranque frío. Registrar resultados observados; un status 200 de HTML de protección del preview no valida backend.
- Límites gratuitos, elegibilidad y facturación no se han auditado. No declarar costo US$0 sin revisar uso y billing del proveedor.

## Historial AWS (no operativo)

Navira sí tuvo despliegues AWS: campaña temporal en ECS Fargate documentada en [CAM-125](../calidad/resultados/campana-aws-cam125.md), y demo pública Lightsail con smoke HTTPS documentado en [CAM-158](../calidad/resultados/smoke-despliegue-cam158.md), además de evidencia CAM-126..131. Esto prueba que se ejecutaron entonces; no indica que los servicios sigan activos hoy.

CAM-161 retiró del repositorio el deploy Lightsail de GitHub Actions, sus scripts/configuración y las plantillas AWS de campaña/OIDC. No hay sesión AWS/CLI ni verificación de detención, eliminación o billing posterior. La consulta HTTPS a la URL Lightsail antigua falló por SSL; eso no prueba que los recursos hayan sido eliminados. No seguir instrucciones AWS antiguas ni intentar administrar recursos desde este repositorio. Si hace falta establecer su estado o evitar cargos, requiere una revisión autorizada de la cuenta AWS; documentar su resultado sin confundirlo con un despliegue activo de Navira.

ADRs históricos: [ADR-045](../arquitectura/decisiones/0045-evaluacion-aws-privada.md), [ADR-046](../arquitectura/decisiones/0046-demo-publica-multisesion.md), [ADR-047](../arquitectura/decisiones/0047-despliegue-lightsail-desde-github-actions.md) y [ADR-050](../arquitectura/decisiones/0050-despliegue-lightsail-oidc-firewall-temporal.md). Mantener los reportes bajo `docs/calidad/resultados/` intactos.
