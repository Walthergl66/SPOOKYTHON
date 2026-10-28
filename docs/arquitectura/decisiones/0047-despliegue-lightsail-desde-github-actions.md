# ADR-047 — Actualizaciones de Lightsail desde GitHub Actions

Fecha: 2026-10-28  
Estado: aceptada; protocolo de despliegue y rollback vigente; autenticación/conectividad actualizadas por ADR-050 (CAM-140)
Origen: solicitud del usuario de automatizar la actualización de Navira tras cambios en el repositorio.

## Contexto

La demo temporal corre en una única instancia Lightsail. Backend, sesiones y coordinador dependen de memoria local; la entrada pública termina TLS en Nginx y el contenedor de frontend proxifica al backend. La publicación anterior construyó imágenes fuera de GitHub y las transfirió por SSH. No se debe copiar la API key al frontend, workflow, artefactos o logs.

## Decisión

1. Reutilizar el workflow CI existente. Solo `master` puede desplegar; el job espera a que pasen backend y frontend. Los pull requests ejecutan validación y nunca despliegan. `workflow_dispatch` permite repetir CI/despliegue desde `master`.
2. Construir backend y frontend con tags del SHA completo, transferir el archivo comprimido y el script de despliegue por SSH, y ejecutar un único coordinador en Lightsail.
3. Autenticar el host SSH con una clave privada de GitHub Actions y una entrada `known_hosts` fijada y verificada. No usar `ssh-keyscan` como confianza automática durante cada ejecución.
4. Conservar la configuración del backend únicamente en `/etc/navira/public.env` en la instancia. La primera actualización automatizada migra las variables del contenedor previo a un archivo de permisos `0600`, sin imprimirlas ni transferirlas al workflow. Exigir demo pública, cookie segura y API key; rechazar el flag de control local.
5. El script conserva los tags anteriores, reemplaza los contenedores y comprueba backend y frontend en loopback. Ante fallo local intenta restaurar las imágenes previas. El workflow verifica también salud y UI mediante HTTPS público.
6. Aceptar una interrupción breve durante el reemplazo. No hay despliegue blue/green porque ambos contenedores comparten puertos y el mundo en memoria no soporta dos coordinadores.
7. El runner hospedado no alcanza SSH con el firewall restringido al origen administrativo. ADR-050 complementa esta decisión con OIDC y apertura temporal de TCP/22 desde el IPv4 `/32` del job; la regla se cierra al finalizar. Nunca abrir SSH a todo Internet.

## Estado de verificación

El run #50 pasó CI/build y falló al conectar al SSH restringido. CAM-139 instaló manualmente una revisión posterior y comprobó `/` y `/salud` (HTTP 200). CAM-140 actualiza el workflow y añade rol OIDC/plantilla IAM; aún faltan crear proveedor/rol y configurar la variable GitHub, por lo que el CD automático todavía no está verificado. Véase ADR-050.

## Alternativas

- Publicar en ECR y extraer desde Lightsail: descartado para esta instancia porque el acceso de publicación ECR fue denegado y Lightsail no tenía rol de extracción operativo.
- Almacenar la API key en GitHub y pasarla al host en cada despliegue: descartado; la configuración productiva ya reside en la VM y no hace falta rotarla para cambiar imágenes.
- Ejecutar el workflow en pull requests: descartado porque se exponen credenciales de despliegue a cambios no confiables.
- Añadir otra réplica para evitar interrupción: descartado por estado volátil y coordinador único.

## Consecuencias y límites

Cuando se configure el rol OIDC y `LIGHTSAIL_DEPLOY_ROLE_ARN`, un push a `master` que pase CI intenta desplegar la revisión. Se requieren los secrets `LIGHTSAIL_HOST`, `LIGHTSAIL_USER`, `LIGHTSAIL_SSH_PRIVATE_KEY`, `LIGHTSAIL_KNOWN_HOSTS` y variables `NAVIRA_PUBLIC_URL`, `LIGHTSAIL_DEPLOY_ROLE_ARN`. `known_hosts` debe corresponder a la clave SSH del host, comprobada por un canal confiable. El job abre SSH solo para su `/32` y cierra esa regla al terminar. La implementación debe completar un primer run exitoso antes de considerar activo el CD. Se mantiene una interrupción breve y se pierden las partidas/sesiones al reiniciar el backend.

El rollback automático cubre fallos comprobados en loopback dentro de la instancia. Si el test externo HTTPS falla después, el job queda fallido y requiere diagnóstico; el workflow no abre el firewall ni revierte por un error externo de DNS/red.

## Documentos propietarios

[CI/CD y Lightsail](../../operacion/infraestructura.md), [seguridad](../../operacion/seguridad.md), [guía de despliegue](../../operacion/guia-paso-a-paso-despliegue.md), [SPEC-005](../../metodo/especificaciones/SPEC-005-aws-evaluacion.md).
