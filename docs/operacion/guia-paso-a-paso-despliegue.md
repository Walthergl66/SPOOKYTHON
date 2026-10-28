# Guía paso a paso para completar Navira

Actualizada: 2026-10-28. Es una guía de ejecución y verificación; no acredita que AWS esté configurado ni autoriza gasto o publicación. El estado vigente se contrasta con [estado actual](../seguimiento/estado-actual.md), [SPEC-005](../metodo/especificaciones/SPEC-005-aws-evaluacion.md), [plan](../seguimiento/plan-implementacion.md), [pendientes](../seguimiento/pendientes.md), [seguridad](seguridad.md) y [costos](costos.md).

## Situación de partida comprobada

- Las campañas R1/R2/R3 se han repetido tres veces localmente: nueve rondas de cinco minutos y 69.572 solicitudes HTTP exitosas. La evidencia está en [CAM-098](../calidad/resultados/campana-reto-cam098.md) y [CAM-099](../calidad/resultados/repeticiones-reto-cam099.md); todavía no mide RTT, disponibilidad o recursos de AWS.
- La CI tiene jobs para pruebas backend y build frontend en [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), pero su ejecución remota no está comprobada.
- En el repositorio revisado no hay Dockerfile ni plantilla de infraestructura. La documentación propone CloudFormation, S3/CloudFront, ALB, ECS Fargate, ECR, DynamoDB y CloudWatch; son diseño, no recursos existentes.
- El control de demo de Simulador/Jugar exige opt-in y conexión loopback. No se debe habilitar `NAVIRA_LOCAL_DEMO_CONTROL=1` detrás de una URL pública. La API key falla cerrada en rutas protegidas cuando no está configurada.
- Los snapshots, sesiones y coordinación son volátiles y de un proceso. Reiniciar el proceso pierde el mundo; añadir réplicas no es seguro con la coordinación actual.
- El usuario eligió `us-east-2` (Ohio). Aún no se verifican la cuenta, los permisos, el Budget, el dominio, certificados, URL pública ni gasto real. La estimación existente para `us-east-1` es una referencia incompleta y no es una cotización para Ohio.

## Fase 0 — Congelar y verificar el candidato

1. Acordar internamente qué commit exacto se evaluará. Guardar su SHA y la versión del mapa con el reporte. No mezclar cambios de la rama visual mientras se construye o prueba ese candidato.
2. En la raíz, ejecutar:

   ```bash
   cd backend
   python -m pip install -e '.[test]'
   python -m unittest discover -s tests -p 'test_*.py' -v
   cd ../frontend
   npm ci
   npm test -- --run
   npm run build
   cd ..
   python3 backend/scripts/check_docs.py
   python3 backend/scripts/check_sdd.py
   python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'
   ```

3. Resolver o documentar fallos reales antes de llamar a esto una versión candidata. No considerar los checks documentales como pruebas de funcionamiento.

**Salida de fase:** SHA identificado, jobs locales correctos y ningún fallo de producto sin triage. El 2026-10-28 la suite backend sobre el árbol de trabajo pasó 240/240; CAM-107 corrige el fallo anterior de reinicio con cero zombies. El árbol incluye cambios sin commit, por lo que ese resultado aún no identifica un SHA inmutable de candidato.

## Fase 1 — Preparar cuenta, región y presupuesto

1. La región elegida por el usuario es `us-east-2` (Ohio). Una captura aportada el 2026-10-28 muestra `Hackathon-Budget` creado por US$10. Confirmar en su detalle período, umbrales y destinatarios de alertas; la captura no identifica la región de recursos, la cuenta de despliegue ni los permisos.
2. La ventana prevista por el usuario es de tres días en `us-east-2`. En AWS Pricing Calculator especificar el tiempo real de cada recurso: por ejemplo, Fargate 1 vCPU/2 GB suma 36 horas si corre 12 h/día, o 72 horas si debe permanecer disponible toda la ventana. Estimar por separado ALB, IPv4, S3, CloudFront, ECR, CloudWatch, datos y persistencia; los servicios de red pueden seguir cobrando mientras la tarea está detenida. Configurar alertas de gasto/uso con destinatarios comprobados. La alerta de AWS Budgets puede llegar con retraso y no detiene automáticamente el gasto; mantener vigilancia y una lista explícita de recursos que se crearán.
3. Confirmar permisos mínimos para desplegar y leer métricas. No copiar claves a Git, Markdown, JavaScript, comandos guardados, tickets o logs. Usar el mecanismo de credenciales aprobado para la cuenta.
4. Usar `us-east-2` en AWS Pricing Calculator y registrar región, fecha, supuestos y cálculo real en [costos](costos.md); guardar evidencia sin datos sensibles. La tarifa pública del ALB de Ohio fue confirmada en CAM-114; falta la exportación final con las opciones reales de la cuenta.

Referencias oficiales: [usar AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/bcm-lite-use-budget.html) y [seguridad de red de Amazon ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-network.html). AWS actualiza los datos de Budgets varias veces al día y las alertas pueden retrasarse; por eso una alerta no equivale a un tope inmediato de gasto.

**Salida de fase:** región y permisos aprobados, Budget con período/alertas comprobados y costo estimado para la ventana de tres días que se pueda comparar con los US$10 listados. Si falta cualquiera, detener creación de infraestructura. Un Budget con alertas no es un tope automático de gasto.

## Fase 2 — Cerrar los bloqueos de publicación

1. Seguir [ADR-045](../arquitectura/decisiones/0045-evaluacion-aws-privada.md): staging privado con restricción de red y clave para `/paso`; no exponer controles locales/operador ni la clave en el navegador.
2. Ejecutar la campaña completa como tarea efímera ECS Fargate desde el mismo SHA/digest, sin listener público, con `python -m navira.evaluacion_local --campana-reto`. Su HTTP loopback mide el artefacto en AWS, pero no ALB/CloudFront; la ráfaga HTTP remota del staging se registra por separado.
3. Declarar staging volátil para smoke: cualquier reinicio invalida el run y exige un `runId` nuevo. No afirmar continuidad. Implementar persistencia condicional, idempotencia, recuperación y exclusión de coordinadores antes de declarar resuelta la recuperación requerida.
4. Mantener un coordinador por proceso hasta tener coordinación distribuida probada. No aumentar `desiredCount` ni habilitar autoscaling del motor con estado en memoria.
5. Completar las pruebas pendientes según [SPEC-005](../metodo/especificaciones/SPEC-005-aws-evaluacion.md): T-16 separación de Reto/Juego, T-18 recuperación y T-23 operación/entrega. Las campañas locales T-50 no sustituyen la ejecución de la tarea efímera en AWS.

**Salida de fase (diseño CAM-113):** alcance privado, método de campaña y política volátil definidos; los controles locales existentes se vuelven a verificar con pruebas. Esto cierra el diseño de Fase 2, no crea staging ni implementa recuperación. Fase 3 debe aplicar y probar red, permisos y empaquetado antes de ejecutar la campaña.

## Fase 3 — Crear empaquetado e infraestructura reproducibles

1. Añadir un Dockerfile del backend y una comprobación local de arranque, salud, mapa incluido y apagado limpio. Añadir el comando de imagen para la tarea de campaña efímera. Añadir Dockerfile separado solo si el frontend necesita servidor dinámico; si es estático, producir el build de Vite y publicarlo en S3 privado detrás de CloudFront.
2. Añadir plantilla versionada de CloudFormation para los recursos elegidos. Parametrizar entorno, región, tamaños y retención; revisar el plan/cambios de la plantilla antes de crear recursos.
3. Aplicar la topología documentada: frontend S3/CloudFront; API y WebSocket hacia ALB/ECS Fargate; imágenes en ECR; estado durable en DynamoDB si su contrato queda implementado; logs/métricas en CloudWatch. No crear un recurso solo porque aparece en el diseño: justificarlo y actualizar costos.
4. Configurar roles IAM separados, Secrets Manager/configuración segura, TLS en navegador y origen, cabeceras de origen y security groups mínimos. Para Fargate, asignar security group a la tarea y restringir su entrada al security group del ALB, conforme a las [recomendaciones de red de ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-network.html). Validar el tramo CDN–origen antes de enviar credenciales.
5. Configurar health check y `GET /salud`; verificar que rutas API no caigan en fallback HTML de la SPA y que la política de caché no almacene respuestas del estado ni del juego.

**Salida de fase:** imagen arrancable y plantilla revisada en un entorno de pruebas; el diff de infraestructura, permisos y costos queda documentado. No existe hoy un comando de despliegue confirmado.

## Fase 4 — Publicar a staging una sola versión

1. Ejecutar la CI de GitHub sobre el SHA candidato y exigir backend tests + frontend build verdes.
2. Construir y publicar la imagen con etiqueta inmutable asociada al SHA; desplegar el frontend del mismo SHA. Mantener `desiredCount=1` para el coordinador.
3. Inyectar secretos desde el mecanismo seguro de AWS y comprobar en revisión que no aparecen en el bundle ni logs.
4. Esperar el health check y verificar desde fuera de la VPC, sin revelar credenciales: frontend carga, tiles/atribución del mapa responden, `/salud` funciona, API no autenticada devuelve lo esperado, API autenticada valida contrato, WebSocket conecta/recupera y el navegador no presenta errores críticos.
5. Ejecutar un smoke Reto corto y un ciclo de pausa/reinicio controlado. Verificar que se usan IDs de run nuevos y que un reinicio no se presenta como continuidad de una partida perdida.
6. Registrar SHA, digest de imagen, versión del mapa, parámetros, región, URL, fecha, resultados, p95, errores y límites. No copiar claves ni datos privados al reporte.

**Salida de fase:** staging reproducible y T-23 parcial con reporte de humo; no anunciar producción todavía.

## Fase 5 — Ejecutar la evaluación remota completa

1. Usar el mismo cliente y protocolo de campaña que generó CAM-098/CAM-099; medir en la máquina cliente el tiempo total de cada HTTP, incluyendo timeouts y errores. No ocultar preparación, slots inactivos ni rondas finalizadas temprano.
2. Ejecutar R1, R2 y R3 en secuencia con parámetros autorizados por la organización. La campaña local actual usa supuestos documentados de densidad/eventos y debe presentarse como tal hasta confirmar los oficiales.
3. Registrar para cada ronda: SHA/digest, región, cohorte, semilla, escenario, mapa, eventos programados y aplicados, turnos activos, ventana completa de cinco minutos, p50/p95/max de `/paso`, p95/ciclo de turnos, cantidad de solicitudes, errores/timeouts, mordidos, evacuados y activos finales.
4. Repetir la campaña completa según el número acordado con el equipo/jurado. CAM-099 aporta tres repeticiones locales; el mínimo remoto de aceptación todavía debe seguir SPEC-005/T-11 y cualquier instrucción oficial.
5. Si un criterio falla, conservar reporte, ajustar una sola causa por vez y repetir desde un nuevo run. No retocar métricas ni presentar una corrida local como AWS.

**Salida de fase:** reportes reproducibles en AWS/entorno oficial, T-11/T-23 y CA-005 con evidencia trazable; SPEC-005 solo cambia a verificada cuando todos sus criterios se cumplen.

## Fase 6 — Integrar la rama visual y liberar

1. Cuando la rama visual esté lista, integrarla a `master` después de revisar el diff y ejecutar de nuevo CI, pruebas frontend y build. No mezclarla silenciosamente en el SHA ya evaluado.
2. Construir un nuevo artefacto con nuevo SHA/digest y desplegarlo primero a staging. Repetir smoke de mapa, consola, WebSocket, flujos Reto/Simulador/Jugar autorizados y tests de contrato.
3. Repetir la campaña de evaluación si el cambio afecta renderizado, payload/cadencia, cliente HTTP, configuración o cualquier componente medido. Si se demuestra que solo cambia estilos, documentar el análisis de impacto y conservar el reporte previo ligado al SHA anterior.
4. Promover el mismo artefacto validado, conservar versión anterior para rollback y comprobar URL/enlaces en la entrega. Mantener recursos necesarios hasta terminar la presentación; eliminar recursos después solo como acción explícita y revisada.

**Salida de fase:** versión de entrega identificada, pruebas y evidencia asociadas al artefacto exacto, rollback probado/documentado y paquete del pitch completo.

## Orden recomendado y criterio de «listo»

El primer trabajo práctico es Fase 0; en paralelo, el responsable de cuenta puede completar Fase 1. No iniciar Fase 3 hasta cerrar Fase 1. No abrir acceso público para el control local. Para decir «listo para desplegar públicamente» deben estar cerrados: presupuesto/región, autenticación de operador, TLS/red, empaquetado/IaC, recuperación o limitación explícita aceptada, CI sobre el SHA, smoke remoto y campaña de evaluación con reporte. Hoy varios de esos puntos siguen pendientes.

| Evidencia final | Documento propietario |
|---|---|
| Requisitos, criterios y estado de evaluación | [SPEC-005](../metodo/especificaciones/SPEC-005-aws-evaluacion.md) |
| Tareas P0/P5/P6 | [plan](../seguimiento/plan-implementacion.md) |
| Región, topología y despliegue | [infraestructura](infraestructura.md) |
| Riesgos y controles | [seguridad](seguridad.md) |
| Estimación y gasto real | [costos](costos.md) |
| Tests y reportes | [pruebas](../calidad/pruebas.md) |
| Historial y siguiente acción | [CAM](../seguimiento/cambios.md) y [estado actual](../seguimiento/estado-actual.md) |
