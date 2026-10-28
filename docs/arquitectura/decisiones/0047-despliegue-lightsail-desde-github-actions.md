# ADR-047 — Actualizaciones de Lightsail desde GitHub Actions

Fecha: 2026-10-28  
Estado: aceptada; CI y empaquetado comprobados; despliegue automático bloqueado por conectividad SSH (CAM-131)
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
7. No abrir SSH a todo Internet ni modificar el firewall desde el workflow. La regla actual de Lightsail permite el origen administrativo; GitHub-hosted runners no tendrán acceso hasta establecer una ruta de red permitida y acotada. El primer despliegue de Actions debe esperar a resolver esa condición sin ampliar exposición indiscriminadamente.

## Estado de verificación

El run de GitHub Actions #50 pasó backend, build frontend, validación de configuración, construcción de imágenes e instalación/verificación de `known_hosts`; el job falló en la transferencia al agotar el tiempo de conexión al puerto 22. El runner hospedado no pertenece al origen permitido por la regla SSH de Lightsail. El commit `ddfa843f81c9cb87732d56b4a1f5b59cf0ee4665` se aplicó manualmente desde el origen administrativo con el script de release y rollback local disponible; `GET /` y `/salud` devolvieron HTTP 200. La publicación manual no resuelve el CD automático. P-21 permanece abierta; no ampliar la regla a `0.0.0.0/0`.

## Alternativas

- Publicar en ECR y extraer desde Lightsail: descartado para esta instancia porque el acceso de publicación ECR fue denegado y Lightsail no tenía rol de extracción operativo.
- Almacenar la API key en GitHub y pasarla al host en cada despliegue: descartado; la configuración productiva ya reside en la VM y no hace falta rotarla para cambiar imágenes.
- Ejecutar el workflow en pull requests: descartado porque se exponen credenciales de despliegue a cambios no confiables.
- Añadir otra réplica para evitar interrupción: descartado por estado volátil y coordinador único.

## Consecuencias y límites

Cada push a `master` que pase CI intenta desplegar la nueva revisión. Se requiere configurar los secrets `LIGHTSAIL_HOST`, `LIGHTSAIL_USER`, `LIGHTSAIL_SSH_PRIVATE_KEY`, `LIGHTSAIL_KNOWN_HOSTS` y la variable `NAVIRA_PUBLIC_URL` en los ajustes del repositorio. El runner GitHub-hosted no puede alcanzar el puerto 22 mientras el firewall mantenga únicamente el IPv4 administrativo actual; una opción de conectividad segura debe definirse antes de dar por activo el CD. Se mantiene una interrupción breve y se pierden las partidas/sesiones al reiniciar el proceso backend.

El rollback automático cubre fallos comprobados en loopback dentro de la instancia. Si el test externo HTTPS falla después, el job queda fallido y requiere diagnóstico; el workflow no abre el firewall ni revierte por un error externo de DNS/red.

## Documentos propietarios

[CI/CD y Lightsail](../../operacion/infraestructura.md), [seguridad](../../operacion/seguridad.md), [guía de despliegue](../../operacion/guia-paso-a-paso-despliegue.md), [SPEC-005](../../metodo/especificaciones/SPEC-005-aws-evaluacion.md).
