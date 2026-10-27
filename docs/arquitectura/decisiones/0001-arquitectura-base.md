# ADR-001 — Arquitectura base modular

Fecha: 2026-10-26. Estado: aceptada para diseño; implementación pendiente. Origen: análisis del reto y plan preparado en esta conversación.

## Contexto

Un grafo pequeño debe atender ráfagas de hasta 200 decisiones con límite de 500 ms y un mundo que cambia cada dos segundos. El reto exige AWS, seguridad básica, costos defendibles y explicación del código por el equipo.

## Decisión

Python/FastAPI para API, núcleo independiente de frameworks, React/TypeScript/Vite/Leaflet para panel y juego. Contenedor permanente en ECS Fargate, DynamoDB para persistencia, ALB y CloudFront/S3 para entrada/frontend. Un proceso de planificación separado del HTTP. Tamaño inicial 1 vCPU/2 GB sujeto a medición; una tarea y un coordinador.

## Alternativas y motivo

- Lambda: posible, pero exige resolver estado compartido y controlar arranques; no elegida para la primera versión.
- EC2: puede reducir costos, añade gestión de host; reconsiderar si presupuesto o permisos lo justifican.
- Microservicios/Redis/colas: no se ha demostrado una necesidad que compense el trabajo adicional.

## Consecuencias

Código de reglas testeable sin AWS. Costos fijos incluso sin partidas. Una tarea no proporciona alta disponibilidad. TLS del origen y recursos/permisos deben cerrarse antes de publicar. No se garantiza capacidad hasta medir carga y ciclo completo.

Documentos propietarios: [arquitectura](../arquitectura.md), [infraestructura](../../operacion/infraestructura.md), [costos](../../operacion/costos.md) y [módulos backend](../modulos/backend.md). Pendientes P-06 y P-11.
