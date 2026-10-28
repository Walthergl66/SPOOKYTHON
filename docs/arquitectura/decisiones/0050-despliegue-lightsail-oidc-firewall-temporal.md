# ADR-050 — CD a Lightsail con OIDC y SSH temporal por runner

Fecha: 2026-10-28  
Estado: aceptada para implementación; configuración AWS pendiente (CAM-140)  
Origen: solicitud del usuario de dejar el despliegue automatizado mediante GitHub Actions.

## Contexto

El workflow de ADR-047 ya construye imágenes por SHA y verifica health checks, pero GitHub-hosted runners no podían alcanzar el puerto 22, limitado a la IP administrativa. El repositorio es público. Un runner self-hosted persistente en la misma VM publicaría el host a código de PR no confiable y además compartiría recursos con la aplicación.

## Decisión

1. Mantener los jobs de CI/CD en runners hospedados por GitHub. El job de despliegue solo se ejecuta desde `master`, después de backend y frontend; los PR no reciben credenciales ni permisos de despliegue.
2. Autenticar AWS mediante GitHub OIDC, sin credenciales AWS de larga duración. El trust policy restringe audiencia `sts.amazonaws.com` y subject a `repo:Walthergl66/SPOOKYTHON:ref:refs/heads/master`.
3. Usar el rol de `infra/aws/github-lightsail-deploy-role.yml`, con solo `lightsail:OpenInstancePublicPorts` y `lightsail:CloseInstancePublicPorts` para la instancia Navira específica. No concede permisos de despliegue del sistema ni de otras instancias.
4. Obtener el IPv4 público del runner y abrir TCP/22 únicamente desde ese `/32`. El workflow cierra la misma regla al finalizar, incluso si falla el despliegue. Si el runner es terminado abruptamente, la limpieza de `always()` no está garantizada; comprobar que la regla se cerró y retirarla manualmente si permanece.
5. Reutilizar secretos SSH existentes, host key fijada, `NAVIRA_PUBLIC_URL`, imágenes inmutables y el script de release/rollback de ADR-047.
6. No abrir SSH a `0.0.0.0/0`, no guardar claves AWS en GitHub y no instalar runner persistente en un repositorio público.

## Configuración requerida una sola vez

Crear (o reutilizar) el proveedor OIDC de IAM `token.actions.githubusercontent.com` con audiencia `sts.amazonaws.com`. Luego crear el stack CloudFormation desde la plantilla indicada, proporcionando el ARN exacto de `navira-public-demo` en `us-east-2`. Guardar el output `GitHubActionsRoleArn` como variable de Actions `LIGHTSAIL_DEPLOY_ROLE_ARN`. El resto de secretos SSH y `NAVIRA_PUBLIC_URL` ya está configurado según evidencia aportada por el usuario; no registrar sus valores.

## Verificación y límites

La sintaxis del workflow y la plantilla se validan localmente en CAM-140. La creación del proveedor/rol, primera ejecución hospedada, apertura/cierre de firewall y health check remoto todavía no se han verificado; la sesión AWS CLI local requiere reautenticación. Hasta completar esa configuración, no afirmar que el CD quedó operativo. El despliegue interrumpe brevemente el servicio y reinicia el estado volátil de partida como ADR-047 documenta.

## Alternativas

- Runner self-hosted en Lightsail: rechazado por la exposición de un host persistente a workflows de un repositorio público.
- Abrir SSH a todo Internet: rechazado.
- IPs fijas de GitHub Actions: no asumidas, ya que los rangos de runners hospedados pueden variar.

## Documentos propietarios

[CI/CD y Lightsail](../../operacion/infraestructura.md), [seguridad](../../operacion/seguridad.md), [guía de despliegue](../../operacion/guia-paso-a-paso-despliegue.md), [SPEC-005](../../metodo/especificaciones/SPEC-005-aws-evaluacion.md), [P-21](../../seguimiento/pendientes.md).
