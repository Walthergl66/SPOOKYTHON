# Campaña efímera Navira en AWS — CAM-125

Fecha: 2026-10-28, región `us-east-2` (Ohio). Este reporte registra una campaña ejecutada en una tarea ECS Fargate con el evaluador y servidor ASGI en loopback dentro del contenedor. **No es una prueba de latencia de Internet, ALB, CloudFront ni una publicación pública.**

## Artefacto y ejecución

- Revisión fuente: árbol de trabajo local de `master`; los cambios de empaquetado/infraestructura no estaban comprometidos ni publicados. No se atribuye la ejecución a un SHA de Git.
- Imagen: `navira-campaign`, digest `sha256:5b0691240e9746bfbe1d724f50f2f426d4f3e9037ac40c1bb3f4336a88142e59`, plataforma Linux x86_64, Python 3.12 Alpine 3.24 fijada por digest.
- Tarea: Fargate, 4 vCPU, 8 GiB; inicio 2026-10-28 04:40:18 y parada 04:56:08 hora de Ecuador; terminó `STOPPED`, código de contenedor 0. No quedó ninguna tarea ECS ejecutándose.
- El escaneo ECR de la imagen terminó sin hallazgos. El smoke local del contenedor verificó `/salud` 200, fixture Manta, usuario no-root y apagado limpio.
- Comando de imagen: `python -m navira.evaluacion_local --campana-reto`.

## Resultados

| Ronda | Habitantes iniciales | Ventana (s) | Turnos activos | Slots ociosos | HTTP 200 | Fallos | p95 `/paso` (ms) | Evacuados | Mordidos | Activos finales | Eventos del reto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| R1 | 20 | 300.127 | 142 | 8 | 1,366 | 0 | 12.035 | 20 | 0 | 0 | Caminantes; sin eventos programados |
| R2 | 80 | 300.103 | 150 | 0 | 5,888 | 0 | 29.436 | 65 | 2 | 13 | Un puente colapsado, turno 50, aplicado |
| R3 | 200 | 300.159 | 150 | 0 | 15,513 | 0 | 65.376 | 171 | 2 | 27 | Dos calles cerradas en turnos 50 y 100, aplicadas |

Total: 900.389 s de ventanas (objetivo 900 s), 924.611 s de campaña completa incluyendo preparación/transiciones, 22,767 respuestas HTTP 200, 0 fallidas y tasa de fallo observada 0 %. Las rondas comenzaron con semilla base solicitada 20261026 y avanzaron una unidad por ronda. Mapa: `manta-osm-df97a2f3a878+zona-urbana`. Reto aplicó los presets/eventos reproducibles actuales; cantidades, densidad y semilla no están confirmadas como parámetros oficiales del jurado.

La latencia p95 es del cliente/servidor loopback en la tarea, no latencia remota del servicio. R1 finalizó todos los habitantes antes de los 150 slots y completó la ventana con ocho slots ociosos; esos slots no son turnos activos. Los valores no demuestran la cadencia que observaría un navegador o un usuario desde Internet.

## Interpretación y límites

- Se completó una ejecución AWS de las tres ventanas de cinco minutos, con cero errores HTTP y un proceso que terminó normalmente. Es evidencia de ejecución del artefacto en Fargate, no validación oficial del jurado ni publicación de Navira.
- Los p95 loopback quedan por debajo de 150 ms en estas tres rondas; no sustituyen una prueba de red/ALB. El p95 creció con el tamaño del escenario (12.035, 29.436 y 65.376 ms).
- Las cifras de evacuados/mordidos son una sola semilla por preset y no estiman rendimiento estadístico ni garantizan seguridad de rutas.
- La imagen base se cambió a Alpine 3.24.3 después de que el escaneo de una imagen Debian anterior encontrara vulnerabilidades; la imagen anterior se retiró del repositorio. El escaneo sin hallazgos solo corresponde al digest citado y a la base de datos disponible al momento del análisis. Referencia: [notas oficiales de Alpine 3.24.3](https://www.alpinelinux.org/posts/Alpine-3.21.9-3.22.7-3.23.7-3.24.3-released.html).
- Estimación orientativa Fargate solamente: a las tarifas indicativas usadas en `costos.md`, 4 vCPU/8 GiB durante 924.611 s representa cerca de US$0.051; logs, ECR, transferencia, impuestos y cobertura real de créditos no están verificados en facturación.
- AWS creó el runner efímero (ECR, cluster, grupo de logs, roles, security group y task definition). No se creó ALB, servicio web persistente, frontend, bucket web, distribución CloudFront, dominio ni certificado.
- La tarea no expuso puertos de entrada; solo tuvo salida HTTPS. No se deja ningún ECS task en ejecución. Los recursos base del stack permanecen para permitir otra campaña y pueden seguir acumulando almacenamiento/logs.
- No existe URL pública. App Runner fue denegado por una política de la organización. La ruta de publicación alternativa requiere resolver un despliegue privado con TLS/acceso restringido, operación segura, configuración de clave y estado volátil según ADR-045; no habilitar el control local en Internet.

## Evidencia relacionada

Cambios: CAM-125. Criterios de AWS y entrega: [SPEC-005](../../metodo/especificaciones/SPEC-005-aws-evaluacion.md). Topología: [infraestructura](../../operacion/infraestructura.md), [seguridad](../../operacion/seguridad.md), [costos](../../operacion/costos.md). Esta evidencia no completa por sí sola SPEC-005, T-23 ni la entrega pública.
