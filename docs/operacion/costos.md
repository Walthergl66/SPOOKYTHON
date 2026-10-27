# Costos y evidencias de presupuesto

Estado: estimación de diseño, no factura. Ningún gasto real ni Budget ha sido comprobado.

## Referencia mensual inicial

Supuestos: `us-east-1`, Linux/x86, 730 horas, una tarea de 1 vCPU/2 GB, ALB público con dos IPv4 y una IPv4 de tarea. Tarifas de referencia consultadas durante el análisis del 26-10-2026; revalidar al desplegar y usar configuración real.

| Concepto | Fórmula | Aproximación USD/mes |
|---|---|---:|
| Fargate | `730 × (0,04048 + 2 × 0,004446)` | 36,04 |
| Cargo fijo ALB | `730 × 0,0225` | 16,43 |
| Tres IPv4 | `3 × 730 × 0,005` | 10,95 |
| Subtotal | Antes de variables e impuestos | 63,42 |

Este subtotal no es el costo total. Faltan consumo del ALB, DynamoDB, almacenamiento/registro de imágenes, S3, CloudFront, logs, transferencia, certificados/dominio si aplican y otros recursos que se añadan. La cantidad de IP reales puede cambiar.

El renderer local usa la instancia pública de OpenFreeMap sin API key conforme a su configuración consultada el 2026-10-26. No se incorpora un precio de tiles al subtotal porque el servicio público se anuncia sin cargo y sin SLA, pero sus términos/continuidad pueden cambiar; validar proveedor, licencia y volumen de uso antes de producción. Esto no es un costo contratado ni una garantía de disponibilidad.

Fuentes: [Fargate](https://aws.amazon.com/fargate/pricing/), [ALB](https://aws.amazon.com/elasticloadbalancing/pricing/) y [VPC/IPv4](https://aws.amazon.com/vpc/pricing/). No asumir gratuidad por créditos, Free Tier o cuenta sandbox sin comprobarla.

## Cómo completar el cálculo

- Separar horas de hosting encendido de horas con simulación activa.
- Medir tamaño de snapshot, escrituras/lecturas por turno y operaciones facturables. No estimar DynamoDB solo por número de llamadas HTTP.
- Medir tráfico del panel, conexiones WebSocket, imágenes, retención y transferencia.
- Aplicar tarifas verificadas a esas cantidades y registrar fecha/región.
- Comparar con gasto real por servicio y explicar diferencias.

## Evidencias pendientes

| Evidencia | Ubicación prevista | Estado |
|---|---|---|
| Budget y alerta configurados desde el inicio | `docs/evidencias/budget.png` | No existe. |
| Cálculo completo mensual | Este archivo o exportación enlazada | Pendiente de dimensionamiento. |
| Gasto real del evento | Resumen comprobado sin datos sensibles | No verificado. |

Un Budget con alerta no garantiza un tope automático de gasto. Mantener revisión durante pruebas y no retirar recursos antes del pitch sin instrucción correspondiente.
