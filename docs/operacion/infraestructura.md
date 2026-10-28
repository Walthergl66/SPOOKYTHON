# Infraestructura y operación AWS

Estado: diseño previsto; no hay recursos de aplicación ni URL comprobados. Región elegida: `us-east-2` (Ohio). CAM-117 verificó `Hackathon-Budget` por US$10 mensuales con alertas ACTUAL de 50/80/100 %; CAM-120 muestra email `Inactive` sin acciones. El usuario acepta continuar sin confirmación del email y monitorear manualmente. La captura Free Plan indica US$120 de crédito, pero servicios/funciones y uso elegibles deben comprobarse. CAM-124 autentica el perfil CLI `navira`, valida la plantilla en AWS y deja el Change Set `navira-foundation-review-20261028c` disponible para revisión. Contiene seis recursos propuestos; no se ejecutó y `list-stack-resources` está vacío. No hay stack de aplicación ni recursos creados. Las subredes públicas candidatas se obtuvieron mediante lectura pero sus IDs se omiten. Costos: [costos](costos.md). Accesos: [seguridad](seguridad.md).

## Recursos iniciales

| Recurso | Propósito | Estado |
|---|---|---|
| AWS Budget con alerta | Visibilidad del gasto desde el inicio | `Hackathon-Budget`, US$10 mensual; tres umbrales y un suscriptor email por alerta comprobados en CAM-117. Verificación/entrega del correo pendiente según el usuario; revisar gasto manualmente. |
| Plan de cuenta AWS | Créditos y disponibilidad de servicios | Captura aportada en CAM-120: Free Plan, US$120 de saldo mostrado y 177 días restantes. Saldo no auditado por CLI; confirmar disponibilidad de cada recurso/feature y elegibilidad de cargos antes de crear. |
| Imagen backend | Empaquetado local y smoke de salud | Dockerfile, digest base fijado y lock runtime en CAM-116; build/salud/mapa/usuario no root/SIGTERM pasan con Podman local. No publicada en ECR. |
| Runner R1/R2/R3 | Ejecutar la campaña efímera en AWS sin listener | Plantilla validada por AWS y Change Set disponible para revisión (CAM-124); no ejecutado. Requiere una VPC existente con subredes públicas. |
| ECR, ECS, IAM y CloudWatch | Imagen y tarea puntual de campaña | Seis recursos base propuestos en CAM-124 (ECR, cluster ECS, grupo de logs, dos roles y SG); no aplicados. La task definition se condiciona a una imagen con digest y no está en el Change Set. |
| S3 privado + CloudFront | Frontend y entrada HTTPS pública | Pendiente. |
| ALB | Enrutar API/WebSocket a tarea | Pendiente. |
| ECS Fargate | API, simulador y proceso de planificación | Pendiente. |
| Registro de imágenes | Publicar imagen reproducible del backend | Pendiente. |
| DynamoDB bajo demanda | Estados, órdenes y metadatos | Pendiente. |
| CloudWatch | Logs, alarmas y métricas | Pendiente. |
| IAM/configuración segura | Roles y secretos fuera del repositorio | Pendiente. |
| CloudFormation | Declaración parametrizada y repetible | Pendiente. |

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

`cfn-lint` pasó localmente y CAM-124 verificó `cloudformation:ValidateTemplate` y la creación del Change Set usando la sesión temporal del perfil `navira`. El Change Set está disponible y muestra seis altas, pero todavía no se ha ejecutado; la lista de recursos del stack está vacía. Revisar sus permisos/costos y compatibilidad con el plan antes de ejecutar. Esta validación no demuestra cuotas, rutas a Internet de las subredes, disponibilidad futura, cobros cubiertos por créditos ni éxito de despliegue. El runner no resuelve TLS/red de staging público.

## Operación y recuperación

Registrar salud, errores, p95, duración de turnos y retraso acumulado. Alertar por estado desactualizado y fallo del coordinador. Retención de logs limitada y exportación de resultados de evaluación. No configurar reinicios que creen dos coordinadores sobre la misma partida.

No existe recuperación automática verificada. Probar fallo de proceso y escritura antes de prometer continuidad. Conservar la versión anterior desplegable y el mapa correspondiente para revertir una publicación; una reversión no puede interpretar snapshots incompatibles sin migración o nueva partida.

Mantener URL funcional hasta el pitch. La retirada de recursos debe ser una tarea explícita, preservando reportes y evidencias; no apagar automáticamente el entorno durante la presentación. Todavía no existen comandos de despliegue confirmados.
