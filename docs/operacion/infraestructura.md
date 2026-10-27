# Infraestructura y operación AWS

Estado: diseño previsto; no hay recursos, URL o credenciales comprobados. Región propuesta `us-east-1`, pendiente P-06. Costos: [costos](costos.md). Accesos: [seguridad](seguridad.md).

## Recursos iniciales

| Recurso | Propósito | Estado |
|---|---|---|
| AWS Budget con alerta | Visibilidad del gasto desde el inicio | No verificado. |
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

## Operación y recuperación

Registrar salud, errores, p95, duración de turnos y retraso acumulado. Alertar por estado desactualizado y fallo del coordinador. Retención de logs limitada y exportación de resultados de evaluación. No configurar reinicios que creen dos coordinadores sobre la misma partida.

No existe recuperación automática verificada. Probar fallo de proceso y escritura antes de prometer continuidad. Conservar la versión anterior desplegable y el mapa correspondiente para revertir una publicación; una reversión no puede interpretar snapshots incompatibles sin migración o nueva partida.

Mantener URL funcional hasta el pitch. La retirada de recursos debe ser una tarea explícita, preservando reportes y evidencias; no apagar automáticamente el entorno durante la presentación. Todavía no existen comandos de despliegue confirmados.
