# PRD — Requisitos del producto Navira

Versión: 1. Fecha: 2026-10-26. Estado: base de producto documentada, sin aplicación implementada. Origen: [reto](referencias/reto-original.md), solicitudes del usuario en [contexto](contexto.md) y modos ya acordados. Este documento identifica necesidades y prioridades; las [especificaciones](especificaciones/README.md) concretan su aceptación sin duplicar los contratos.

## Problema, público y valor

Ayudar a sobrevivientes a llegar a refugios sobre un mapa que cambia durante el recorrido. El jurado necesita observar y medir un motor dinámico; el jugador quiere experimentar la evacuación; el operador necesita iniciar escenarios reproducibles. Es una demostración de hackathon, no un servicio certificado de emergencias.

## Requisitos identificados

### PRD-01 — Mundo reconocible y refugios

Disponer de un grafo de Manta de unas 300 intersecciones, calles con distancia/tipo y cuatro refugios. Conservar conectividad entre los barrios del reto y representar cierres. Prioridad: obligatoria por reto. Detalle: [reglas](reglas-juego.md), [datos](datos.md).

### PRD-02 — Simulación dinámica y reglas comunes

Ejecutar zombies, turnos, bloqueos, mordidas y llegadas según las reglas del reto. Humano y automáticos usan un mismo mundo y resolutor. Prioridad: obligatoria. No convertir ambigüedades pendientes en reglas oficiales; ver [pendientes](pendientes.md).

### PRD-03 — Evacuación automática

Recomendar un siguiente paso válido hacia un refugio con costos de calle y peligros visibles, recalculando cuando cambia el mundo. Prioridad: obligatoria. Esperar es una acción válida, pero no garantiza seguridad. Detalle: [motor](algoritmos.md).

### PRD-04 — Observación comprensible en vivo

Mostrar zombies visibles por tipo, sobrevivientes, rutas, refugios, cierres y turno. Comunicar desconexión y última actualización. Prioridad: obligatoria; un mapa detenido no se presenta como vivo. Detalle: [espectador](flujos/espectador.md).

### PRD-05 — Juego humano complementario

Permitir entrar como personaje en un nodo aleatorio elegible y llevarlo a un refugio mediante calles vecinas o espera. Primera versión: un humano por partida y resto automático, sin registro permanente. Radio opcional aconseja sin mover ni garantizar supervivencia. Prioridad: solicitada por el usuario. Detalle: [jugador](flujos/jugador.md).

### PRD-06 — Roles y separación de modos

Separar espectador, jugador, operador y servicio. El modo queda fijo por partida; la evaluación oficial no admite control humano y sus métricas se separan del juego. Prioridad: necesaria para integrar el complemento sin alterar el reto. Detalle: [roles](flujos/roles.md), [modos](modos.md).

### PRD-07 — Evaluación reproducible

Ejecutar las tres rondas de cinco minutos con 20, 80 y 200 sobrevivientes y eventos requeridos. Conservar semillas, configuraciones, decisiones, versiones y resultados suficientes para auditar. Prioridad: obligatoria. Vivos, evacuados y pendientes se reportan separados.

### PRD-08 — Entrega utilizable y defendible

Aplicación en AWS, repositorio público con historial real, Budget con alerta, README reproducible, arquitectura, costos, pitch y enlaces comprobados según el reto. Prioridad: obligatoria. Fechas y entregables: [contexto](contexto.md), [plan](plan-implementacion.md).

### PRD-09 — Mejora de rutas demostrable

Comparar política base con predicción de corredores y búsqueda temporal. Conservar la política mejor medida si una mejora no compensa sus costos o riesgo. Prioridad: mejora posterior a una ronda base funcional; no es garantía de supervivencia ni requisito de obtener puntos extra.

## Alcance y exclusiones

Comprometido: los requisitos anteriores, implementados de forma incremental. Fuera del mínimo: múltiples partidas concurrentes, multijugador simultáneo, cuentas permanentes, movimiento libre continuo, LLM para decidir pasos y app móvil. Capacidad de refugios y camionetas son extras condicionados, no requisitos activos nuevos.

## Éxito y aceptación

Una ronda completa vía HTTP real es el primer hito. Después se mide supervivencia/evacuación, eficiencia, latencia y errores en AWS. Metas técnicas y método: [TRD](TRD.md), [pruebas](pruebas.md). No establecer un porcentaje de supervivencia inventado; usar escenarios comparables y rúbrica oficial. Aceptación por funcionalidad y vínculos a tareas/pruebas: [trazabilidad](trazabilidad.md).

Cambiar alcance requiere actualizar este PRD, la especificación afectada y el historial; una instrucción actual del usuario puede autorizar ese ajuste sin repetir aprobaciones rutinarias.
