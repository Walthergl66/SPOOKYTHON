# Costos y evidencias de presupuesto

CAM-161: las cifras y presupuestos AWS de este documento son únicamente evidencia histórica de planeación/despliegues previos; no son la infraestructura activa ni instrucciones para aprovisionar recursos. Vercel + Render es el destino activo. No se consultó AWS Billing ni se confirmó si quedan recursos AWS activos; el gasto remoto actual es desconocido. No afirmar que AWS quedó eliminado o que su costo es cero.

Estado: estimaciones y capturas históricas, no factura ni presupuesto actual. CAM-117 verificó entonces el Budget `Hackathon-Budget` de US$10 mensuales y tres alertas ACTUAL (50/80/100 %). La captura de ese periodo muestra destinatario `Inactive`; el usuario aceptó monitoreo manual, pero la entrega por correo no se verificó. La captura Free Plan mostraba US$120 en créditos, US$0 por pagar y 177 días a esa fecha; no es saldo actual. No hay gasto actual comprobado.

CAM-160 aprovisionó Render Free y Vercel Hobby; Vercel Production `b06e9f9` está listo y `/salud` integrado respondió 200. La validación funcional quedó parcial: bootstrap y REST autenticado recibieron 429 porque el cupo de una sesión estaba ocupado; WebSocket no se probó. No se verificó billing, elegibilidad, cuotas, transferencia ni uso facturable de las cuentas; no atribuir un costo real de US$0. Render documenta 750 horas gratuitas por workspace/mes, suspensión por inactividad, filesystem efímero y cargos suplementarios si se supera el ancho de banda saliente incluido; Vercel Hobby es para uso personal/no comercial y puede pausar deployments al superar límites incluidos. Revisar [límites Render Free](https://render.com/docs/free), [planes Vercel](https://vercel.com/pricing) y [términos Hobby](https://vercel.com/legal/terms).

**Estimación histórica CAM-127, no aplicable como guía actual:** una Lightsail `medium_3_0` en `us-east-2` se estimó a US$24/mes, o aproximadamente US$2,37 por 72 horas. No es factura; excluía impuestos, transferencia, ECR y recursos auxiliares. No se verificó el estado actual de la instancia ni la factura AWS tras los despliegues. El Budget AWS histórico solo enviaba alertas; su estado actual no fue consultado.

Las siguientes observaciones de AWS corresponden al momento de las capturas históricas. No representan derechos, créditos o billing actuales y no son una instrucción para provisionar AWS. El inventario y facturación de recursos AWS remotos es desconocido (P-25).

## Referencia mensual inicial (modelo AWS histórico)

Supuestos históricos: `us-east-1`, Linux/x86, 730 horas, una tarea de 1 vCPU/2 GB, ALB público con dos IPv4 y una IPv4 de tarea. Tarifas consultadas el 26-10-2026; el subtotal no es presupuesto de Navira y no debe usarse para crear recursos.

| Concepto | Fórmula | Aproximación USD/mes |
|---|---|---:|
| Fargate | `730 × (0,04048 + 2 × 0,004446)` | 36,04 |
| Cargo fijo ALB | `730 × 0,0225` | 16,43 |
| Tres IPv4 | `3 × 730 × 0,005` | 10,95 |
| Subtotal | Antes de variables e impuestos | 63,42 |

Este subtotal no es el costo total. Faltan consumo del ALB, DynamoDB, almacenamiento/registro de imágenes, S3, CloudFront, logs, transferencia, certificados/dominio si aplican y otros recursos que se añadan. La cantidad de IP reales puede cambiar.

## Cálculo de Fargate histórico aportado para el entorno

El usuario confirmó que usó `us-east-2` (Ohio) y compartió una estimación para **una tarea de 1 vCPU/2 GB que corre 12 horas al día**. Su mes de referencia equivale a `730 / 24 = 30,42` jornadas (aprox. 365 horas): vCPU US$14,78 + memoria US$3,25 = **US$18,03/mes**. El cálculo es correcto para las tarifas ingresadas; con 365 horas exactas y sin redondear componentes queda cerca de US$18,02.

El usuario aclaró que el cálculo corresponde a Ohio; no se recibió exportación de la calculadora para auditar los valores/régimen seleccionados. AWS factura Fargate por CPU, memoria y almacenamiento mientras la tarea está ejecutándose; los 20 GB efímeros base no generan cargo extra según la página de precios de AWS. Detener la única tarea fuera de su horario deja la API fuera de servicio. Si una tarea permanece encendida 730 horas, este tamaño da aproximadamente US$36,04 con las tarifas ingresadas.

**Estimación histórica de ventana de tres días en Ohio:** a 12 horas por día son 36 horas de tarea, `36 × (0,04048 + 2 × 0,004445) = US$1,78`; para 72 horas de ejecución, aproximadamente US$3,55. Los montos excluyen ALB, IPv4, almacenamiento, registros, transferencia y persistencia y no deben extrapolarse a recursos actuales. El Budget histórico era alerta, no límite de gasto.

El usuario compartió además un cálculo de **LCU variable del ALB**: 0,04 LCU máximas × US$0,008/LCU-hora × 730 h = **US$0,23/mes**. Para las 72 horas de los tres días, ese componente sería `0,04 × 0,008 × 72 = US$0,023`, aproximadamente **US$0,02**. El escenario usa 0,01 GB/h, 1 conexión nueva/s, duración media de 1 s y 1 regla; las evaluaciones de regla pagadas quedan en cero tras la franquicia ingresada. Esta cifra solo cubre las LCUs: el ALB también tiene un cargo base por cada hora o fracción que permanece activo. El 2026-10-28 se consultó el archivo público AWS Price List de `AWSELB` para `us-east-2`; confirma **US$0,0225 por ALB-hora** y **US$0,008 por LCU-hora**. Para 72 horas, el costo base es `72 × 0,0225 = US$1,62`, y las LCUs del escenario son aproximadamente US$0,02. IPv4 y transferencia también se contabilizan aparte. El caudal/conexiones son supuestos, no mediciones del tráfico real de Navira. La verificación es de tarifa pública; no es una exportación de la calculadora ni valida descuentos/créditos de esta cuenta.

## Modelo provisional AWS para tres días (histórico)

Estimación propia elaborada el 2026-10-28 a solicitud del usuario. Región prevista: `us-east-2`; ventana de infraestructura: 72 h. Es un cálculo de planificación histórico, no presupuesto exportado ni cotización. No usarlo para aprovisionamiento ni asumir costo real.

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

## Método de cálculo histórico (no operativo)

- El modelo separaba horas de hosting encendido y horas de simulación.
- Debía medir snapshots, tráfico, conexiones, retención y transferencia antes de estimar.
- Sus tarifas eran supuestos fechados, no cargos observados.

## Evidencias pendientes

CAM-125: la campaña Fargate de 4 vCPU/8 GiB duró 924,611 s según el reporte. El cómputo se estimó históricamente en **US$0,051**, no es factura y excluye otros recursos. En ese momento la tarea terminó y `list-tasks` devolvió cero tareas activas; el stack reportó ECR, cluster, logs, roles y security group. Su estado actual no se ha comprobado. No se consultó billing después de la migración; revisar recursos/cargos requiere inventario AWS autorizado (P-25).

| Evidencia | Ubicación prevista | Estado |
|---|---|---|
| Budget histórico | Consultas AWS Budgets CAM-115/CAM-117 y captura CAM-120 | En ese momento: `Hackathon-Budget`, US$10 mensual; email `Inactive`. Estado y cargos actuales no comprobados. |
| Plan y créditos de la captura | Captura compartida CAM-120 | Valores históricos; no sirven como saldo o elegibilidad actual. |
| Cálculo AWS completo | Modelo conservado arriba | Planeación histórica; no es presupuesto de la infraestructura activa. |
| Gasto AWS tras migración | No hubo sesión AWS/CLI en CAM-161 | Desconocido; revisar mediante inventario autorizado según P-25. |

Los presupuestos y gastos AWS mencionados arriba son registros históricos. No hay verificación de recursos activos, bajas ni facturas posteriores a CAM-161. No declarar que AWS dejó de generar costos.

Referencias oficiales del plan: [comparación Free/Paid](https://docs.aws.amazon.com/us_en/awsaccountbilling/latest/aboutv2/free-tier-plans.html), [servicios admitidos en la nueva experiencia](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html), [estado de verificación de emails Budget](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-email-recipients.html).
