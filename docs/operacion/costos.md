# Costos y evidencias de presupuesto

Estado: estimación de diseño, no factura. CAM-117 verificó el Budget `Hackathon-Budget` de US$10 mensuales y tres alertas ACTUAL (50/80/100 %). La captura más reciente del usuario muestra destinatario `Inactive` y ninguna acción asociada; el usuario acepta continuar y monitorear manualmente, pero la entrega por correo no está verificada. El panel del Free Plan compartido por el usuario muestra US$120 en créditos, US$0 por pagar, 177 días y fin 2027-04-21; tratarlo como evidencia visual de esa fecha, no como saldo auditado por CLI. No hay gasto real comprobado.

CAM-127 cambia a una instancia Lightsail `medium_3_0` en `us-east-2` (2 vCPU/4 GB) porque la cuenta no permitió crear un Container Service. La tarifa publicada de US$24/mes produce la aproximación de 72 horas `24 × 72 / 730 = US$2,37`. La estimación no es factura final y excluye impuestos, transferencia sobre el allowance, almacenamiento ECR y cualquier recurso auxiliar; confirmar la tarifa vigente al revisar Billing. El Budget US$10 solo alerta; revisar Billing y detener/eliminar la instancia y revisar la Static IP al terminar. No se crea un ALB separado, CloudFront, S3 ni base de datos para esta ruta.

AWS describe el Free Plan como limitado a servicios/características seleccionados, con fin a los seis meses o al agotarse créditos, lo que ocurra primero. El acceso a una familia de servicio no confirma que cada operación/feature esté permitida ni que cada costo esté cubierto. Confirmar saldo elegible, funciones permitidas y fecha en Billing antes de provisionar; los créditos no deben descontarse automáticamente de la estimación bruta de uso. La documentación de AWS sobre el Free Plan y servicios admitidos se enlaza al final de este apartado.

## Referencia mensual inicial

Supuestos históricos: `us-east-1`, Linux/x86, 730 horas, una tarea de 1 vCPU/2 GB, ALB público con dos IPv4 y una IPv4 de tarea. Tarifas de referencia consultadas durante el análisis del 26-10-2026; revalidar al desplegar y usar configuración real. El usuario eligió `us-east-2` (Ohio), por lo que el subtotal siguiente no es el presupuesto de Navira y debe recalcularse para esa región y duración antes de crear recursos.

| Concepto | Fórmula | Aproximación USD/mes |
|---|---|---:|
| Fargate | `730 × (0,04048 + 2 × 0,004446)` | 36,04 |
| Cargo fijo ALB | `730 × 0,0225` | 16,43 |
| Tres IPv4 | `3 × 730 × 0,005` | 10,95 |
| Subtotal | Antes de variables e impuestos | 63,42 |

Este subtotal no es el costo total. Faltan consumo del ALB, DynamoDB, almacenamiento/registro de imágenes, S3, CloudFront, logs, transferencia, certificados/dominio si aplican y otros recursos que se añadan. La cantidad de IP reales puede cambiar.

## Cálculo de Fargate aportado para el entorno

El usuario confirmó que usó `us-east-2` (Ohio) y compartió una estimación para **una tarea de 1 vCPU/2 GB que corre 12 horas al día**. Su mes de referencia equivale a `730 / 24 = 30,42` jornadas (aprox. 365 horas): vCPU US$14,78 + memoria US$3,25 = **US$18,03/mes**. El cálculo es correcto para las tarifas ingresadas; con 365 horas exactas y sin redondear componentes queda cerca de US$18,02.

El usuario aclaró que el cálculo corresponde a Ohio; no se recibió exportación de la calculadora para auditar los valores/régimen seleccionados. AWS factura Fargate por CPU, memoria y almacenamiento mientras la tarea está ejecutándose; los 20 GB efímeros base no generan cargo extra según la página de precios de AWS. Detener la única tarea fuera de su horario deja la API fuera de servicio. Si una tarea permanece encendida 730 horas, este tamaño da aproximadamente US$36,04 con las tarifas ingresadas.

**Ventana de despliegue confirmada por el usuario: tres días en Ohio.** A 12 horas por día son 36 horas de tarea y el cálculo de Fargate es `36 × (0,04048 + 2 × 0,004445) = US$1,78`. Si la aplicación debe estar disponible durante las 72 horas completas, Fargate sube a aproximadamente US$3,55. Estos montos usan las tarifas aportadas por el usuario y no incluyen ALB, IPv4, S3, CloudFront, ECR, CloudWatch, transferencia ni persistencia. Para el estimado total, configura cada recurso con sus horas reales en esos tres días; algunos servicios, como balanceador e IP, pueden seguir facturando aunque la tarea Fargate esté detenida. El Budget de US$10 es una alerta, no un límite de gasto.

El usuario compartió además un cálculo de **LCU variable del ALB**: 0,04 LCU máximas × US$0,008/LCU-hora × 730 h = **US$0,23/mes**. Para las 72 horas de los tres días, ese componente sería `0,04 × 0,008 × 72 = US$0,023`, aproximadamente **US$0,02**. El escenario usa 0,01 GB/h, 1 conexión nueva/s, duración media de 1 s y 1 regla; las evaluaciones de regla pagadas quedan en cero tras la franquicia ingresada. Esta cifra solo cubre las LCUs: el ALB también tiene un cargo base por cada hora o fracción que permanece activo. El 2026-10-28 se consultó el archivo público AWS Price List de `AWSELB` para `us-east-2`; confirma **US$0,0225 por ALB-hora** y **US$0,008 por LCU-hora**. Para 72 horas, el costo base es `72 × 0,0225 = US$1,62`, y las LCUs del escenario son aproximadamente US$0,02. IPv4 y transferencia también se contabilizan aparte. El caudal/conexiones son supuestos, no mediciones del tráfico real de Navira. La verificación es de tarifa pública; no es una exportación de la calculadora ni valida descuentos/créditos de esta cuenta.

## Modelo provisional de costo total para tres días

Estimación propia elaborada el 2026-10-28 a solicitud del usuario. Región prevista: `us-east-2`; ventana de infraestructura: 72 h. Es un cálculo de planificación, no un presupuesto exportado desde AWS Pricing Calculator ni una cotización. Usa tarifas compartidas por el usuario y referencias públicas; confirmar especialmente el precio fijo del ALB para Ohio antes de crear recursos.

| Componente | Supuesto para 12 h/día | Cálculo estimado | Para 24 h/día |
|---|---|---:|---:|
| ECS Fargate | 1 tarea Linux/x86, 1 vCPU/2 GB; 36 h de ejecución | US$1,78 | US$3,55 |
| ALB, cargo fijo | 1 ALB activo 72 h; referencia US$0,0225/h | US$1,62 | US$1,62 |
| ALB, LCU | 0,04 LCU promedio por hora durante 72 h | US$0,02 | US$0,02 |
| IPv4 públicas | 2 IP del ALB × 72 h + IP de tarea × 36 h, US$0,005/IP-h | US$0,90 | US$1,08 |
| ECR | 1 GB de imagen privada retenida 3 días, referencia US$0,10/GB-mes | US$0,01 | US$0,01 |
| CloudWatch Logs | Provisión conservadora de 1 GB ingerido × US$0,50/GB, antes de posible cuota gratuita | US$0,50 | US$0,50 |
| CloudFront + almacenamiento estático S3 | Plan Free, dentro de 1 M solicitudes, 100 GB de salida y 5 GB de crédito de S3; sin dominio propio | US$0,00 | US$0,00 |
| **Subtotal planificado** |  | **US$4,83** | **US$6,78** |

La columna 12 h/día mantiene el ALB y CloudFront disponibles las 72 h aunque la tarea se detenga 12 h cada día; durante ese tiempo la API no responde. La columna 24 h/día mantiene la tarea y su IP durante toda la ventana. Las cifras de ALB/IP usan las cantidades/rates indicados en el modelo y no incluyen impuestos.

CloudFront Free se cuenta en US$0 solo si se selecciona ese plan y la distribución/uso encajan en sus límites actuales; AWS publica 1 M de solicitudes, 100 GB de transferencia y 5 GB de crédito mensual de S3 para ese plan. Si se usa el esquema Pay-as-you-go, se añaden solicitudes, transferencia y operaciones S3 según uso real. CloudWatch se calcula en bruto con 1 GB; AWS publica 5 GB de logs incluidos en el nivel gratuito aplicable, pero no se asume que la cuenta concreta tenga saldo/eligibilidad. ECR usa 1 GB porque todavía no existe imagen Docker y su tamaño real no se ha medido.

No se incluye DynamoDB: todavía no está implementado en la app; el estado actual es volátil y se perdería al reiniciar la tarea. Tampoco se incluyen NAT Gateway (la topología prevista lo omite), registro de dominio, consumo fuera de la ventana, tráfico real por encima del escenario, retención extensa de logs, copias de seguridad o impuestos. Si se necesita persistencia o si se crea cualquiera de esos recursos, recalcular. La suma queda debajo de US$10 en ambos casos, pero el Budget es una alerta, no una barrera automática de gasto; conservar margen y revisar los cargos efectivos.

El renderer local usa la instancia pública de OpenFreeMap sin API key conforme a su configuración consultada el 2026-10-26. No se incorpora un precio de tiles al subtotal porque el servicio público se anuncia sin cargo y sin SLA, pero sus términos/continuidad pueden cambiar; validar proveedor, licencia y volumen de uso antes de producción. Esto no es un costo contratado ni una garantía de disponibilidad.

Fuentes: [Lightsail](https://aws.amazon.com/lightsail/pricing/), [Fargate](https://aws.amazon.com/fargate/pricing/), [ALB](https://aws.amazon.com/elasticloadbalancing/pricing/), [AWS Price List AWSELB para Ohio](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSELB/current/us-east-2/index.json), [VPC/IPv4](https://aws.amazon.com/vpc/pricing/), [CloudFront Free](https://aws.amazon.com/cloudfront/pricing/), [ECR](https://aws.amazon.com/ecr/pricing/), [S3](https://aws.amazon.com/s3/pricing/) y [CloudWatch](https://aws.amazon.com/cloudwatch/pricing/). No asumir gratuidad por créditos, Free Tier o cuenta sandbox sin comprobarla.

## Cómo completar el cálculo

- Separar horas de hosting encendido de horas con simulación activa.
- Medir tamaño de snapshot, escrituras/lecturas por turno y operaciones facturables. No estimar DynamoDB solo por número de llamadas HTTP.
- Medir tráfico del panel, conexiones WebSocket, imágenes, retención y transferencia.
- Aplicar tarifas verificadas a esas cantidades y registrar fecha/región.
- Comparar con gasto real por servicio y explicar diferencias.

## Evidencias pendientes

CAM-125: la campaña Fargate de 4 vCPU/8 GiB duró 924,611 s entre inicio y fin según el reporte del runner. Con las tarifas indicativas de Fargate usadas en este documento, el cómputo solo se estima en **US$0,051**; no es lectura de factura y no incluye ECR, CloudWatch Logs, transferencia, impuestos ni recursos base retenidos. La tarea se detuvo y `list-tasks` confirmó cero tareas activas. El cluster, ECR, grupo de logs, roles y security group quedan para reuso y no generan una tarifa horaria equivalente a la tarea, aunque ECR/logs pueden almacenar datos. El escaneo y la tarea terminada no prueban el saldo real de créditos. Revisar Cost Explorer/Billing cuando se actualice y antes de ampliar la infraestructura.

| Evidencia | Ubicación prevista | Estado |
|---|---|---|
| Budget configurado desde el inicio | Consultas AWS Budgets CAM-115/CAM-117 y captura aportada CAM-120 | `Hackathon-Budget`, US$10 mensual; alertas ACTUAL 50/80/100 %. El usuario acepta monitoreo manual; la captura indica email `Inactive`, sin acciones, y no prueba entrega. AWS Budget alerta, no bloquea gastos. |
| Plan y créditos disponibles | Captura compartida por el usuario CAM-120; consultar AWS Billing al provisionar | Free Plan, saldo visual US$120, US$0 por pagar, 177 días restantes y fin 2027-04-21. Saldo/servicios elegibles no verificados por API; revisar en el momento de la ejecución. |
| Cálculo completo mensual | Este archivo o exportación enlazada | Pendiente de dimensionamiento. |
| Gasto real del evento | Cost Explorer/Billing | No verificado; solo existe una estimación del cómputo de campaña en CAM-125. |

Un Budget con alerta no garantiza un tope automático de gasto. Mantener revisión durante pruebas y no retirar recursos antes del pitch sin instrucción correspondiente.

Referencias oficiales del plan: [comparación Free/Paid](https://docs.aws.amazon.com/us_en/awsaccountbilling/latest/aboutv2/free-tier-plans.html), [servicios admitidos en la nueva experiencia](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html), [estado de verificación de emails Budget](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-email-recipients.html).
