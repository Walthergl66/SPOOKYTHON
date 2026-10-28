# Infraestructura y operación AWS

Estado al 2026-10-28 (CAM-125): recursos AWS de evaluación creados en `us-east-2` y una campaña Fargate R1/R2/R3 completada; la tarea terminó con código 0 y no quedan tareas ejecutándose. No existe servicio web, URL pública ni staging conectado a la interfaz. El intento con App Runner fue rechazado por una política de la organización. El correo del Budget aparece `Inactive`; el usuario aceptó supervisión manual. El crédito Free Plan de la captura no demuestra elegibilidad de cargos. Evidencia: [CAM-125](../calidad/resultados/campana-aws-cam125.md). Costos: [costos](costos.md). Accesos: [seguridad](seguridad.md).

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

Esta topología sustituye solo la prohibición de exponer los controles locales para la demo solicitada; el runner Fargate de evaluación y su alcance loopback permanecen separados. Se usa un Container Service de una réplica `medium-1` (2 GB/1 vCPU), Nginx público en 8080 y backend privado en 8000 dentro del mismo servicio. El proxy sirve frontend y API same-origin, conserva el WebSocket y limita rutas públicas. Lightsail proporciona endpoint HTTPS administrado. `NAVIRA_PUBLIC_DEMO_CONTROL=1`, `NAVIRA_PUBLIC_MAX_SESSIONS=3`, `NAVIRA_PUBLIC_SESSION_IDLE_SECONDS=10800`, `NAVIRA_PUBLIC_SESSION_COOKIE_SECONDS=86400`, `NAVIRA_COOKIE_SECURE=1`, `NAVIRA_DEMO_MAP=/opt/navira/backend/data/maps/manta-hackathon-v1.json`; `NAVIRA_LOCAL_DEMO_CONTROL` permanece apagado. El backend corre con un worker.

Imágenes buildadas localmente con Podman (Docker daemon no disponible), `amd64/linux`; ECR privado `navira-campaign` tiene tags inmutables y escaneo on-push. Lightsail debe activar su rol ECR image-puller para ese repo antes del deployment. Configurar solo frontend como puerto público 8080/HTTP detrás del endpoint administrado; backend sin puerto público. Los valores sensibles, si se añaden, deben pasarse al servicio fuera del repo.

Límites probados localmente: máximo tres sesiones por navegador/instancia, mundos de Reto/Simulador/Juego operador distintos, expiración de tres horas sin actividad. Sin base de datos: reiniciar servicio elimina todo. Un solo servicio/proceso; no escalar réplicas. La instancia medium-1 está estimada para el evento de 72 h; se debe borrar Container Service al terminar para detener el cargo. Estado AWS y URL solo se anotan después de comprobación real.

Primera tarea a medir: 1 vCPU/2 GB, una réplica. El tamaño no constituye una garantía de capacidad. Mantener servicio encendido y listo antes de evaluar; el arranque del contenedor no debe formar parte del camino normal por petición.

## Red propuesta para el evento

CloudFront sirve el frontend desde S3 mediante acceso de origen y enruta API/WebSocket al ALB. Configurar rutas antes del comportamiento genérico del frontend; no convertir errores API en HTML por una regla SPA. Desactivar caché para API/estado y reenviar `x-api-key`, cookies y cabeceras WebSocket necesarias según cada ruta.

Para evitar NAT en la versión inicial: tarea con IP pública para salida, en subred pública; entrada permitida solo desde el security group del ALB. Restringir ALB al origen previsto de CloudFront y validar un encabezado de origen independiente de la API key. El control de origen no sustituye autenticación de jugador/operador. Documentar y comprobar la protección del tramo CloudFront–origen antes de enviar credenciales; HTTPS de navegador a CDN no prueba por sí solo cifrado hasta el backend.

La configuración exacta de TLS del origen, certificados y dominio es P-11; resolver antes del despliegue público autenticado. Si se cambia la topología para resolverlo, actualizar arquitectura y costos mediante ADR. No improvisar un bypass de seguridad ni anunciar una URL que no se haya verificado.

## Orden de despliegue

1. Inspeccionar acceso autorizado y región, y configurar Budget/alerta.
2. Crear recursos parametrizados y roles mínimos.
3. Publicar imagen y frontend de una revisión identificada.
4. Configurar secretos por el mecanismo seguro elegido; nunca en plantilla o logs públicos.
5. Arrancar una única tarea, esperar salud y cargar mapa validado.
6. Comprobar endpoint público, autenticación y WebSocket; ejecutar una ronda corta.
7. Ejecutar tres rondas y guardar evidencia de versión, latencia y reloj.

La campaña completa se ejecutará en una tarea efímera y privada desde el mismo artefacto, conforme a [ADR-045](../arquitectura/decisiones/0045-evaluacion-aws-privada.md). No tendrá listener ni permiso para modificar el servicio de staging. La prueba HTTP del endpoint a través del ALB será independiente; no confundirla con la campaña loopback. Mantener un coordinador por tarea y no desplegar el control local.

### Borrador del runner de campaña

`infra/aws/campaign.yml` declara ECR con tags inmutables, logs con retención configurable, un cluster ECS, rol de ejecución limitado a extraer esa imagen/escribir esos logs y un security group sin entrada y con salida HTTPS. La definición Fargate solo se crea después de proporcionar la URI ECR inmutable `@sha256`; se lanza explícitamente con `aws ecs run-task`, una sola tarea, subred pública y `assignPublicIp=ENABLED`. El stack no crea listener, servicio persistente, NAT ni frontend. `VpcId` y subredes son parámetros de infraestructura existente; comprobar que las subredes tengan ruta al Internet Gateway. La tarea no tiene permiso de aplicación para mutar staging.

`cfn-lint` y `cloudformation:ValidateTemplate` pasaron. CAM-125 ejecutó y verificó el stack, publicó la imagen, creó una task definition inmutable y corrió la campaña. El digest y resultados están en el reporte CAM-125. Esta verificación no demuestra cobertura de créditos, factura final, URL pública, TLS, servicio web, API remota ni persistencia. La cuenta denegó App Runner por política organizativa. El runner no resuelve TLS/red de staging.

## Operación y recuperación

Registrar salud, errores, p95, duración de turnos y retraso acumulado. Alertar por estado desactualizado y fallo del coordinador. Retención de logs limitada y exportación de resultados de evaluación. No configurar reinicios que creen dos coordinadores sobre la misma partida.

No existe recuperación automática verificada. Probar fallo de proceso y escritura antes de prometer continuidad. Conservar la versión anterior desplegable y el mapa correspondiente para revertir una publicación; una reversión no puede interpretar snapshots incompatibles sin migración o nueva partida.

Mantener URL funcional hasta el pitch. La retirada de recursos debe ser una tarea explícita, preservando reportes y evidencias; no apagar automáticamente el entorno durante la presentación. Todavía no existen comandos de despliegue confirmados.
