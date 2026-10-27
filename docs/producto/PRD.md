# PRD — Requisitos del producto Navira

Versión: 1. Fecha: 2026-10-26. Estado: requisitos documentados; aplicación implementada parcialmente. Origen: [reto](../referencias/reto-original.md), solicitudes del usuario en [contexto](contexto.md) y modos ya acordados. Este documento identifica necesidades y prioridades; las [especificaciones](../metodo/especificaciones/README.md) concretan su aceptación sin duplicar los contratos.

## Problema, público y valor

Ayudar a sobrevivientes a llegar a refugios sobre un mapa que cambia durante el recorrido. El jurado necesita observar y medir un motor dinámico; el jugador quiere experimentar la evacuación; el operador necesita iniciar escenarios reproducibles. Es una demostración de hackathon, no un servicio certificado de emergencias.

## Requisitos identificados

### PRD-01 — Mundo reconocible y refugios

Disponer de un grafo de Manta con calles dirigidas, distancia/tipo y cuatro refugios. La base del reto considera unas 300 intersecciones; el usuario solicitó además ampliar el mapa fuente a toda la envolvente OSM de Manta, incluidas parroquias rurales, y luego fijó una ventana urbana más pequeña como zona de juego. La partida, las apariciones, las rutas y los refugios personalizados se limitan a `[-80.807, -1.082]`–`[-80.621, -0.897]`; el resto del fixture se conserva como fuente cartográfica, pero queda fuera del grafo jugable. Esta caja aproximada no es límite municipal certificado. Cuando el escenario modele evacuación por tsunami, preferir destinos señalados como “Zona Segura” por la fuente oficial; no inferir seguridad ante sismos sin evaluación específica. Prioridad: obligatoria por reto. Detalle: [reglas](../dominio/reglas-juego.md), [datos](../dominio/datos.md) y [dataset Manta](../dominio/mapa-manta.md).

### PRD-02 — Simulación dinámica y reglas comunes

Ejecutar zombies, turnos, bloqueos, mordidas y llegadas según las reglas del reto. El escenario debe variar de forma estocástica entre ejecuciones; pequeñas diferencias de semilla, estado o eventos pueden cambiar rutas y resultados posteriores. La demo debe permitir intensidades sintéticas de amenazas distribuidas por el grafo para observar rutas bajo presión; no representar esos presets como densidades oficiales de Manta. En el control local, cada partida activa desde 1 hasta 10 cierres viales aleatorios definidos al inicio, sin relación con la intensidad zombie. Humano y automáticos usan un mismo mundo y resolutor. Prioridad: obligatoria. No convertir ambigüedades pendientes en reglas oficiales; ver [pendientes](../seguimiento/pendientes.md).

### PRD-03 — Evacuación automática

Recomendar un siguiente paso válido hacia un refugio, priorizando menos mordidas estimadas a lo largo del recorrido y recalculando cuando cambia el mundo. Prioridad: obligatoria. Esperar es una acción válida, pero no garantiza seguridad; el criterio para comparar resultados reales está en PRD-10. Detalle: [motor](../arquitectura/algoritmos.md).

### PRD-04 — Observación comprensible en vivo

Mostrar zombies visibles por tipo, sobrevivientes, rutas, refugios, cierres y turno. Al confirmarse un incidente vial, alertar en el mapa y señalar el punto afectado; las nuevas recomendaciones deben rodear el cierre. Comunicar desconexión y última actualización. Prioridad: obligatoria; un mapa detenido no se presenta como vivo. Detalle: [espectador](../dominio/flujos/espectador.md).

### PRD-05 — Juego humano complementario

Permitir entrar como personaje en un nodo aleatorio elegible y llevarlo a un refugio mediante calles vecinas o espera. Primera versión: un humano por partida y resto automático, sin registro permanente. Radio opcional aconseja sin mover ni garantizar supervivencia. Prioridad: solicitada por el usuario. Detalle: [jugador](../dominio/flujos/jugador.md).

### PRD-06 — Roles y separación de modos

Separar espectador, jugador, operador y servicio. El modo queda fijo por partida; la evaluación oficial no admite control humano y sus métricas se separan del juego. Prioridad: necesaria para integrar el complemento sin alterar el reto. Detalle: [roles](../dominio/flujos/roles.md), [modos](../dominio/modos.md).

### PRD-07 — Evaluación reproducible

Ejecutar las tres rondas de cinco minutos con 20, 80 y 200 sobrevivientes y eventos requeridos. La ejecución ordinaria obtiene un estado aleatorio nuevo; al fijar semilla, versión, configuración, eventos y órdenes se puede reproducir esa ejecución. Conservar esos datos y resultados suficientes para auditar. Prioridad: obligatoria. Vivos, evacuados y pendientes se reportan separados.

### PRD-08 — Entrega utilizable y defendible

Aplicación en AWS, repositorio público con historial real, Budget con alerta, README reproducible, arquitectura, costos, pitch y enlaces comprobados según el reto. Prioridad: obligatoria. Fechas y entregables: [contexto](contexto.md), [plan](../seguimiento/plan-implementacion.md).

### PRD-09 — Mejora de rutas demostrable

Comparar política base con predicción de corredores y búsqueda temporal. Conservar la política mejor medida si una mejora no compensa sus costos o riesgo. Prioridad: mejora posterior a una ronda base funcional; no es garantía de supervivencia ni requisito de obtener puntos extra.

### PRD-10 — Minimizar mordidas durante la evacuación

La política de ruta debe priorizar la reducción del número de sobrevivientes mordidos como objetivo primario; entre políticas con igual cantidad de mordidos, favorecer más evacuados. El planificador usa exposición futura estimada a partir de amenazas visibles y debe recalcular cuando cambie el snapshot. Las mordidas reales se miden al resolver el mundo y prevalecen para comparar resultados; una estimación no es garantía de supervivencia. Prioridad: obligatoria para la política del simulador. Detalle: [algoritmos](../arquitectura/algoritmos.md), [SPEC-002](../metodo/especificaciones/SPEC-002-motor-paso.md).

### PRD-11 — Perímetro de protección de refugios

En partidas del mapa Manta, impedir que los zombies aparezcan o avancen a menos de una cuadra topológica de un refugio. La protección incluye el nodo del refugio y las intersecciones conectadas directamente por cualquier sentido de calle; solo el grafo Manta usa esta regla, porque los mapas pequeños sintéticos no representan distancias urbanas. Prioridad: mejora solicitada por el usuario. Detalle: [reglas](../dominio/reglas-juego.md) y [SPEC-001](../metodo/especificaciones/SPEC-001-mundo-simulacion.md).

## Alcance y exclusiones

Comprometido: los requisitos anteriores, implementados de forma incremental. Fuera del mínimo: múltiples partidas concurrentes, multijugador simultáneo, cuentas permanentes, movimiento libre continuo, LLM para decidir pasos y app móvil. Capacidad de refugios y camionetas son extras condicionados, no requisitos activos nuevos.

## Éxito y aceptación

Una ronda completa vía HTTP real es el primer hito. Después se mide supervivencia/evacuación, eficiencia, latencia y errores en AWS. Metas técnicas y método: [TRD](TRD.md), [pruebas](../calidad/pruebas.md). No establecer un porcentaje de supervivencia inventado; usar escenarios comparables y rúbrica oficial. Aceptación por funcionalidad y vínculos a tareas/pruebas: [trazabilidad](../metodo/trazabilidad.md).

Cambiar alcance requiere actualizar este PRD, la especificación afectada y el historial; una instrucción actual del usuario puede autorizar ese ajuste sin repetir aprobaciones rutinarias.
