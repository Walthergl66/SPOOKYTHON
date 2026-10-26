# Pendientes, supuestos y riesgos

Estado al 2026-10-26. Ninguna aclaración externa confirmada todavía. Las respuestas se añaden con fecha y fuente; cerrar también reglas, contratos, ADR y pruebas afectados.

| ID | Asunto | Supuesto o siguiente paso | ¿Impide empezar local? |
|---|---|---|---|
| P-01 | Velocidad/distancia frente a un salto por turno | Resolución de rutas usa metros y factor de tipo configurable neutral 1.0; no incluye velocidad en el costo hasta confirmar la interpretación oficial. | No. |
| P-02 | Fase de despertar y primer movimiento del dormido | Prototipo: alcance no dirigido de 2 saltos al inicio de fase, no se mueve al despertar; opción configurable. Confirmar regla oficial y fase del primer movimiento. | No. |
| P-03 | Objetivo y desempates del corredor | Prototipo: menor ruta dirigida dentro de 3 saltos, empate por ID; objetivo fijo durante dos pasos. Confirmar criterio oficial. | No. |
| P-04 | Refugio seguro y mordida/llegada | Prototipo resuelve mordida antes de evacuar; no otorga inmunidad al refugio. Confirmar regla oficial. | No. |
| P-05 | Fórmula de supervivencia y eficiencia | Registrar vivos/evacuados/pendientes, saltos, metros y costo temporal. | No. |
| P-06 | Región, cuenta y permisos AWS | `us-east-1` propuesta; acceso y Budget no verificados. | No; sí afecta despliegue. |
| P-07 | Movimiento exacto de horda «casi inmóvil» | Prototipo mantiene la horda estática; confirmar si debe moverse y en qué condiciones. | No. |
| P-08 | Calles dirigidas, puentes y cierres | El núcleo acepta cierre por arista dirigida o segmento físico completo. Falta confirmar qué ID entrega cada evento oficial. | No. |
| P-09 | Cantidad zombie y dificultad inicial | La demo local tiene perfiles reducidos y cohortes 20/80/200 con semilla para pruebas sintéticas; no corresponden a las rondas oficiales. Falta fijar densidad y distribución de zombies para las rondas completas y confirmar las condiciones oficiales de evaluación. | No. |
| P-10 | Tamaño del equipo y repositorio remoto | Supuesto dos/tres integrantes; no hay remoto verificado. | No. |
| P-11 | TLS origen, certificados y dominio | Resolver camino autenticado de extremo a extremo antes de publicar juego/API. | No; sí afecta publicación. |
| P-12 | Sesión y expiración de propiedad humana | CAM-043 recupera por cookie la sesión/posición/última orden mientras vive el proceso y no crea personaje sin cookie; falta definir expiración/revocación y recuperación durable sin permitir robo o renacimiento. | No; cerrar antes de juego público. |
| P-13 | Cobertura geográfica del mapa | Existe exportador OSM y fixture de 300 nodos, con cuatro refugios oficiales de tsunami y rutas dirigidas hasta ellos. Revisar que el recorte represente los barrios del reto y validar cobertura peatonal; no equivale a cartografía oficial exhaustiva. | No para el modelo genérico; sí para cerrar el mapa de evaluación. |
| P-14 | Seguridad sísmica de refugios en Manta | Las capas consultadas del GAD identifican zonas seguras de evacuación por tsunami, no certifican los sitios ante terremotos. Conseguir microzonificación local y validación de suelo/estructura por sitio antes de etiquetar destinos como seguros ante sismos. | No para el fixture; sí para cualquier afirmación o uso de seguridad sísmica. |
| P-15 | Distribuciones estocásticas de evaluación | El usuario confirma que el mundo debe variar y que pequeñas diferencias pueden cambiar su evolución. Definir/configurar rangos y distribuciones de posiciones, tipos, decisiones aleatorias y eventos sin inventar cantidades oficiales; P-09 y P-07 condicionan esos parámetros. | No para desarrollar el generador sintético; sí para congelar escenarios oficiales. |
| P-16 | Cierre de turno y concurrencia de órdenes | CAM-040 implementa puerta con deadline monotónico de 1,7 s, serialización entre `RegistrarOrdenHumana` y cierre/resolución, y rechazo de orden tardía en el runner local. `RLock` coordina solo un proceso; snapshots y órdenes no son durables ni multi-host. | Resuelto para demo de un proceso; sí antes de despliegue multi-worker/productivo. |

## Riesgos de ejecución

- Tiempo disponible hasta la entrega: priorizar una ronda funcional, no camionetas ni efectos complejos.
- CPU/latencia: la preparación también debe caber en dos segundos. Medir antes de prometer capacidad.
- Persistencia: snapshots completos, idempotencia y órdenes confirmadas; definir recuperación real.
- Panel congelado: heartbeat, fase y hora de actualización visibles.
- Documentación desactualizada: cada cierre actualiza estado/cambios y documentos propietarios.

Nuevos pendientes reciben un ID estable. No borrar preguntas resueltas: marcar resolución y enlazar decisión/evidencia, conservando la historia.
