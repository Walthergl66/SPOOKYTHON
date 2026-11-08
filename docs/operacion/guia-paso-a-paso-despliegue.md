# Historial de guía de despliegue AWS (retirada)

Esta guía se conserva solo como documentación histórica. **No ejecutar sus instrucciones AWS ni provisionar infraestructura con ellas.** CAM-161 retiró AWS como destino activo y quitó del repositorio el deploy Lightsail, scripts y plantillas de campaña/OIDC. Vercel + Render es el único hosting activo; consulte la [guía operativa vigente](infraestructura.md), [ADR-054](../arquitectura/decisiones/0054-hosting-vercel-render-free.md) y [ADR-055](../arquitectura/decisiones/0055-retirar-aws-como-infraestructura-activa.md).

## Evidencia histórica preservada

- CAM-125 completó una campaña temporal R1/R2/R3 en ECS Fargate; fue un runner efímero y no un servicio de aplicación. Consulte el [reporte de campaña](../calidad/resultados/campana-aws-cam125.md).
- CAM-126..131 y CAM-158 documentan publicaciones previas de la aplicación en Lightsail, health checks, el intento de CD de GitHub Actions y límites observados. Consulte el [reporte smoke CAM-158](../calidad/resultados/smoke-despliegue-cam158.md).
- ADR-045, ADR-047 y ADR-050 explican decisiones de evaluación, publicación Lightsail y OIDC que ya no son procedimientos vigentes.

La documentación histórica no prueba el estado actual de recursos o facturas AWS. CAM-161 no tuvo sesión AWS/CLI; el probe HTTPS a la URL anterior falló por SSL y es inconcluso. No afirmar que los recursos se eliminaron ni que dejaron de generar cargos. Si se requiere esa certeza, hace falta una verificación autorizada de cuenta independiente de este repositorio.
