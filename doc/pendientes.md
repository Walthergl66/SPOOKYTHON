# Pendientes, supuestos y riesgos

Estado al 2026-10-26. Ninguna aclaración externa confirmada todavía. Las respuestas se añaden con fecha y fuente; cerrar también reglas, contratos, ADR y pruebas afectados.

| ID | Asunto | Supuesto o siguiente paso | ¿Impide empezar local? |
|---|---|---|---|
| P-01 | Velocidad/distancia frente a un salto por turno | Un salto; costo adicional de calle. Consultar interpretación. | No. |
| P-02 | Fase de despertar y primer movimiento del dormido | Prototipo: alcance no dirigido de 2 saltos al inicio de fase, no se mueve al despertar; opción configurable. Confirmar regla oficial y fase del primer movimiento. | No. |
| P-03 | Objetivo y desempates del corredor | Prototipo: menor ruta dirigida dentro de 3 saltos, empate por ID; objetivo fijo durante dos pasos. Confirmar criterio oficial. | No. |
| P-04 | Refugio seguro y mordida/llegada | Prototipo resuelve mordida antes de evacuar; no otorga inmunidad al refugio. Confirmar regla oficial. | No. |
| P-05 | Fórmula de supervivencia y eficiencia | Registrar vivos/evacuados/pendientes, saltos, metros y costo temporal. | No. |
| P-06 | Región, cuenta y permisos AWS | `us-east-1` propuesta; acceso y Budget no verificados. | No; sí afecta despliegue. |
| P-07 | Movimiento exacto de horda «casi inmóvil» | Prototipo mantiene la horda estática; confirmar si debe moverse y en qué condiciones. | No. |
| P-08 | Calles dirigidas, puentes y cierres | El núcleo acepta cierre por arista dirigida o segmento físico completo. Falta confirmar qué ID entrega cada evento oficial. | No. |
| P-09 | Cantidad zombie y dificultad inicial | Parametrizar escenarios y confirmar condiciones de evaluación. | No. |
| P-10 | Tamaño del equipo y repositorio remoto | Supuesto dos/tres integrantes; no hay remoto verificado. | No. |
| P-11 | TLS origen, certificados y dominio | Resolver camino autenticado de extremo a extremo antes de publicar juego/API. | No; sí afecta publicación. |
| P-12 | Sesión y expiración de propiedad humana | Una sesión/partida; definir duración/recuperación sin permitir robo o renacimiento. | No; cerrar antes de juego público. |
| P-13 | Fuente y extensión geográfica del mapa | Preparar extracción reproducible desde OpenStreetMap para el área y barrios requeridos; faltan polígono, exportación y archivo real. | No para el modelo genérico; sí para simular la ciudad. |

## Riesgos de ejecución

- Tiempo disponible hasta la entrega: priorizar una ronda funcional, no camionetas ni efectos complejos.
- CPU/latencia: la preparación también debe caber en dos segundos. Medir antes de prometer capacidad.
- Persistencia: snapshots completos, idempotencia y órdenes confirmadas; definir recuperación real.
- Panel congelado: heartbeat, fase y hora de actualización visibles.
- Documentación desactualizada: cada cierre actualiza estado/cambios y documentos propietarios.

Nuevos pendientes reciben un ID estable. No borrar preguntas resueltas: marcar resolución y enlazar decisión/evidencia, conservando la historia.
