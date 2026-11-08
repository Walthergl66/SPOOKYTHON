# ADR-055 — Retirar AWS como infraestructura activa

Fecha: 2026-11-07  
Estado: aceptada; migración documental y de repositorio en CAM-161  
Origen: decisión del usuario de migrar Navira fuera de AWS.

## Contexto

Navira tuvo una campaña efímera R1/R2/R3 en ECS Fargate (CAM-125) y una demo pública previamente desplegada en Lightsail (CAM-126..131, CAM-158). La topología vigente de la aplicación es Vercel para frontend/proxy y Render Free para el backend (ADR-054, CAM-160). El repositorio aún contenía un job de CD a Lightsail, scripts de publicación y plantillas AWS que ya no deben ser una ruta operativa.

## Decisión

1. Vercel + Render son la única infraestructura activa documentada para la aplicación Navira. La rama de Producción Vercel es `master`; Render permanece como servicio de backend de una instancia/un worker con estado en memoria.
2. Retirar el CD de Lightsail del workflow y borrar los artefactos de publicación Lightsail y las plantillas de campaña/OIDC AWS del repositorio.
3. Mantener CAM-125, CAM-158 y demás reportes/ADRs AWS como evidencia histórica de lo que sí se ejecutó. No reescribirlos para simular que esos despliegues no ocurrieron.
4. No afirmar que recursos AWS remotos fueron detenidos o eliminados. No hubo sesión AWS/CLI durante esta migración; una consulta HTTPS a la URL antigua falló por SSL y no demuestra que la instancia o recursos auxiliares hayan desaparecido.
5. Los documentos de operación pueden conservar costos y detalles AWS solo claramente marcados como históricos, sin pasos actuales para crear, desplegar, borrar o administrar recursos AWS.

## Consecuencias y pendientes

La CI conserva validaciones, pero ya no ejecuta un job de deploy Lightsail ni exige `LIGHTSAIL_DEPLOY_ROLE_ARN`. El estado de recursos, imágenes, IP, presupuestos y cargos remotos AWS es desconocido y requiere una verificación autorizada separada antes de afirmar que no hay recursos o costos. El smoke funcional Vercel/Render también queda parcial: en CAM-160 `/` y `/salud` respondieron 200, mientras `/demo/sesion` y `/panel/estado` respondieron 429 por el único cupo ocupado; cookie, REST autenticado y WebSocket continúan pendientes.

## Evidencia

CAM-161 retira los artefactos del repositorio y actualiza documentación. Evidencia histórica: [campaña Fargate CAM-125](../../calidad/resultados/campana-aws-cam125.md), [smoke Lightsail CAM-158](../../calidad/resultados/smoke-despliegue-cam158.md), [ADR-045](0045-evaluacion-aws-privada.md), [ADR-046](0046-demo-publica-multisesion.md), [ADR-047](0047-despliegue-lightsail-desde-github-actions.md) y [ADR-050](0050-despliegue-lightsail-oidc-firewall-temporal.md).
