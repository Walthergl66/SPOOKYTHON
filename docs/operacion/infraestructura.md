# Infraestructura y operación AWS

Estado al 2026-10-28 (CAM-139): además de la campaña de evaluación CAM-125, la demo pública temporal está en `us-east-2`, Lightsail instance `navira-public-demo`, IPv4 estática `3.17.253.59`, URL HTTPS [3.17.253.59.nip.io](https://3.17.253.59.nip.io). Se desplegó el código `81212bce74cea102b27a308f0f3bff894af43003` desde el origen administrativo, con host key fijado. La imagen activa identifica ese SHA; ambos contenedores están arriba y las comprobaciones HTTPS de `/` y `/salud` devuelven HTTP 200. El primer paquete de imágenes falló health check y el script restauró el release anterior; un segundo paquete corregido se desplegó con éxito. No se modificó firewall. GitHub Actions #50 sigue bloqueado por origen de red al puerto 22 desde runner hospedado; no abrir SSH globalmente. Sesiones, mundos y coordinador continúan volátiles. La cuenta deniega lectura de recursos Lightsail por CLI; el correo del Budget aparece `Inactive` y el usuario acepta supervisión manual. Evidencia de evaluación: [CAM-125](../calidad/resultados/campana-aws-cam125.md); continuidad: [CAM-139](../seguimiento/cambios.md#cam-139-despliegue-verificado-en-lightsail). Costos: [costos](costos.md). Accesos: [seguridad](seguridad.md).

## Recursos iniciales

| Recurso | Propósito | Estado |
|---|---|---|
| AWS Budget con alerta | Visibilidad del gasto desde el inicio | `Hackathon-Budget`, US$10 mensual; tres umbrales y un suscriptor email por alerta comprobados en CAM-117. Verificación/entrega del correo pendiente según el usuario; revisar gasto manualmente. |
| Plan de cuenta AWS | Créditos y disponibilidad de servicios | Captura aportada en CAM-120: Free Plan, US$120 de saldo mostrado y 177 días restantes. Saldo no auditado por CLI; confirmar disponibilidad de cada recurso/feature y elegibilidad de cargos antes de crear. |
| Imagen backend | Empaquetado y smoke de salud | Publicada en ECR como digest inmutable; smoke local de `/salud`, fixture, no-root y SIGTERM pasa. Escaneo del digest ejecutado sin hallazgos (CAM-125). |
| Runner R1/R2/R3 | Ejecutar campaña efímera en AWS sin listener | Ejecutado en una tarea Fargate de 4 vCPU/8 GiB; las tres ventanas de 300 s terminaron y la tarea salió 0. Evidencia CAM-125; loopback no es métrica de red pública. |
| ECR, ECS, IAM y CloudWatch | Imagen y tarea puntual de campaña | Stack aplicado: repositorio ECR, cluster ECS, grupo de logs, dos roles IAM, security group sin entrada y task definition anclada a digest. Un runner terminó; no hay servicio ECS persistente ni tareas activas. |
| S3 privado + CloudFront | Frontend y entrada HTTPS pública | Pendiente. |
| ALB | Enrutar API/WebSocket a tarea | Pendiente. |
| ECS Fargate | API, simulador y proceso de planificación | Pendiente. |
| Registro de imágenes | Publicar imagen reproducible del backend | Pendiente. |
| DynamoDB bajo demanda | Estados, órdenes y metadatos | Pendiente. |
| CloudWatch | Logs, alarmas y métricas | Pendiente. |
| IAM/configuración segura | Roles y secretos fuera del repositorio | Pendiente. |
| CloudFormation | Declaración parametrizada y repetible | Pendiente. |

## Demo pública temporal en Lightsail (ADR-046)

Esta ruta sirve la URL abierta solicitada y queda separada del runner Fargate de evaluación. La organización no permitió crear Lightsail Container Service; la instancia VM alternativa es `medium_3_0` (2 vCPU/4 GB, tarifa de lista estimada US$24/mes), con Static IP `3.17.253.59` y hostname temporal `3.17.253.59.nip.io`. Host Amazon Linux 2023 ejecuta Docker para backend/frontend y Nginx del host para HTTPS/ACME. Solo 80/443 están abiertos a Internet; SSH 22 está restringido al IPv4 administrativo observado durante la configuración. `nip.io` es un servicio de terceros, no un dominio propio; el certificado Let's Encrypt se obtuvo y Certbot instaló la renovación automática. No hay balanceador, base de datos ni persistencia.

El frontend público corre con `VITE_PUBLIC_DEMO=1`; backend con `NAVIRA_PUBLIC_DEMO_CONTROL=1`, `NAVIRA_PUBLIC_MAX_SESSIONS=3`, `NAVIRA_PUBLIC_SESSION_IDLE_SECONDS=10800`, `NAVIRA_PUBLIC_SESSION_COOKIE_SECONDS=86400`, `NAVIRA_COOKIE_SECURE=1`; `NAVIRA_LOCAL_DEMO_CONTROL` permanece apagado. Ambos contenedores usan red host en un solo servidor/proceso; el Nginx de la interfaz en 8080 reenvía al backend en 8000 y el Nginx host termina TLS. Solo la interfaz es enrutable desde el proxy; el firewall Lightsail bloquea el puerto 8080 externo. El backend corre con un worker.

### Actualizaciones automáticas desde GitHub

`.github/workflows/ci.yml` contiene los jobs de CI y `Deploy to Lightsail`. En `master`, el despliegue espera ambos jobs de pruebas/build, construye las dos imágenes con el SHA Git completo, las transfiere por SSH y ejecuta [`deploy-release.sh`](../../deploy/lightsail/deploy-release.sh). Los pull requests no despliegan; `workflow_dispatch` permite repetir la validación desde `master`. El script conserva la configuración privada en `/etc/navira/public.env`, comprueba `NAVIRA_PUBLIC_DEMO_CONTROL=1`, `NAVIRA_COOKIE_SECURE=1`, una `NAVIRA_API_KEY` y que el control local siga apagado. Si falta el archivo, migra el entorno del contenedor backend anterior sin mostrar sus valores. Hace health checks de loopback y restaura los tags de imágenes anteriores si falla uno. GitHub comprueba después `/salud` y la UI por HTTPS.

Configurar como GitHub Actions secrets `LIGHTSAIL_HOST`, `LIGHTSAIL_USER`, `LIGHTSAIL_SSH_PRIVATE_KEY` y `LIGHTSAIL_KNOWN_HOSTS`; configurar `NAVIRA_PUBLIC_URL` como variable del repositorio. `known_hosts` debe corresponder a la clave SSH del host, comprobada por un canal confiable (no confiar en `ssh-keyscan` ejecutado por el mismo workflow). No se guarda la API key en GitHub.

**Estado del CD/despliegue:** CAM-139 desplegó y verificó manualmente `81212bce74cea102b27a308f0f3bff894af43003` desde el origen administrativo. GitHub Actions run #50 pasó pruebas, build de ambas imágenes, validación de configuración y fijación de `known_hosts`, pero falló con timeout al puerto 22 desde el runner (bloqueo de red). El acceso SSH manual ya está configurado; para Actions hace falta un canal de red restringido que admita al runner. No ampliar SSH a `0.0.0.0/0`. Cada reemplazo causa una interrupción breve y pierde mundos/sesiones en memoria.

Las imágenes se construyen localmente con Podman y se transfieren a la VM mediante SSH; ECR tiene tags previos inmutables, pero Lightsail no pudo activar un rol image-puller y el artefacto desplegado debe quedar identificado por su digest/commit en CAM-127. El límite de tres sesiones acota memoria casual, no es una prueba de carga. Un solo proceso; reinicio destruye partidas. La tarifa estimada de la VM por 72 horas encendida es `24 × 72 / 730 = US$2,37`, antes de impuestos/uso adicional; al cerrar, detener/eliminar la instancia y revisar si se conserva la Static IP. Ver [costos](costos.md).

## Red propuesta para el evento

CloudFront sirve el frontend desde S3 mediante acceso de origen y enruta API/WebSocket al ALB. Configurar rutas antes del comportamiento genérico del frontend; no convertir errores API en HTML por una regla SPA. Desactivar caché para API/estado y reenviar `x-api-key`, cookies y cabeceras WebSocket necesarias según cada ruta.

Para evitar NAT en la versión inicial: tarea con IP pública para salida, en subred pública; entrada permitida solo desde el security group del ALB. Restringir ALB al origen previsto de CloudFront y validar un encabezado de origen independiente de la API key. El control de origen no sustituye autenticación de jugador/operador. Documentar y comprobar la protección del tramo CloudFront–origen antes de enviar credenciales; HTTPS de navegador a CDN no prueba por sí solo cifrado hasta el backend.

La URL pública temporal HTTPS está activa, con Nginx/Certbot del host y `nip.io`; no es dominio propio. La configuración de dominio propio/certificado dedicado sigue en P-11. Si se cambia la topología, actualizar arquitectura y costos mediante ADR. No improvisar un bypass de seguridad ni anunciar una URL que no se haya verificado.

## Orden de despliegue

1. Inspeccionar acceso autorizado y región, y configurar Budget/alerta.
2. Crear recursos parametrizados y roles mínimos.
3. Publicar imagen y frontend de una revisión identificada.
4. Configurar secretos por el mecanismo seguro elegido; nunca en plantilla o logs públicos.
5. Arrancar una única tarea, esperar salud y cargar mapa validado.
6. Comprobar endpoint público, autenticación y WebSocket; ejecutar una ronda corta.
7. Ejecutar tres rondas y guardar evidencia de versión, latencia y reloj.
8. Para la demo temporal, hasta disponer de conectividad restringida para el runner, desplegar desde el entorno administrativo con el script y comprobar SHA, salud y UI públicos. Para reactivar CD, resolver P-21 sin abrir SSH a todo Internet; luego confirmar Actions y health check remoto.

La campaña completa se ejecutará en una tarea efímera y privada desde el mismo artefacto, conforme a [ADR-045](../arquitectura/decisiones/0045-evaluacion-aws-privada.md). No tendrá listener ni permiso para modificar el servicio de staging. La prueba HTTP del endpoint a través del ALB será independiente; no confundirla con la campaña loopback. Mantener un coordinador por tarea y no desplegar el control local.

### Borrador del runner de campaña

`infra/aws/campaign.yml` declara ECR con tags inmutables, logs con retención configurable, un cluster ECS, rol de ejecución limitado a extraer esa imagen/escribir esos logs y un security group sin entrada y con salida HTTPS. La definición Fargate solo se crea después de proporcionar la URI ECR inmutable `@sha256`; se lanza explícitamente con `aws ecs run-task`, una sola tarea, subred pública y `assignPublicIp=ENABLED`. El stack no crea listener, servicio persistente, NAT ni frontend. `VpcId` y subredes son parámetros de infraestructura existente; comprobar que las subredes tengan ruta al Internet Gateway. La tarea no tiene permiso de aplicación para mutar staging.

`cfn-lint` y `cloudformation:ValidateTemplate` pasaron. CAM-125 ejecutó y verificó el stack, publicó la imagen, creó una task definition inmutable y corrió la campaña. El digest y resultados están en el reporte CAM-125. Esta verificación no demuestra cobertura de créditos, factura final, URL pública, TLS, servicio web, API remota ni persistencia. La cuenta denegó App Runner por política organizativa. El runner no resuelve TLS/red de staging.

## Operación y recuperación

Registrar salud, errores, p95, duración de turnos y retraso acumulado. Alertar por estado desactualizado y fallo del coordinador. Retención de logs limitada y exportación de resultados de evaluación. No configurar reinicios que creen dos coordinadores sobre la misma partida.

No existe recuperación automática verificada. Probar fallo de proceso y escritura antes de prometer continuidad. Conservar la versión anterior desplegable y el mapa correspondiente para revertir una publicación; una reversión no puede interpretar snapshots incompatibles sin migración o nueva partida.

Mantener URL funcional hasta el pitch. La retirada de recursos debe ser una tarea explícita, preservando reportes y evidencias; no apagar automáticamente el entorno durante la presentación. El despliegue Lightsail temporal usa `deploy/lightsail/deploy-release.sh`. GitHub Actions se ejecutó en el run #50, pero el runner hospedado no alcanzó SSH; el candidato se instaló manualmente desde la ruta administrativa y se comprobaron los health checks públicos. CD automático sigue pendiente de P-21.
