# Modelo de datos y consistencia

Estado: nodos, calles dirigidas, refugios y grafo validados están implementados en `src/navira/domain/mapa.py`; `simulation/coordinador.py` crea snapshots completos por fase y `application/snapshots.py` los confirma mediante un puerto CAS. `application/simulacion_automatica.py` confirma preparación y resolución en versiones separadas. Existe además `data/maps/manta-hackathon-v1.json`, fixture OSM de 300 nodos con cuatro anclas de zona segura de tsunami del GAD Manta; su alcance es parcial y sus fuentes/límites están en [mapa Manta](mapa-manta.md) y [ADR-007](decisiones/0007-mapa-manta-y-evidencia-de-amenazas.md). No constituye un mapa validado para emergencias y no evalúa seguridad sísmica. El mapa `data/maps/demo-sintetico.json` sigue sirviendo para una partida local efímera. El adaptador `adapters/snapshots_memoria.py` solo sirve en un proceso local; almacenamiento/confirmación durable sigue pendiente. Decisión de consistencia: [ADR-003](decisiones/0003-estado-y-turnos.md).

Lenguaje común y límites de consistencia: [ODDD](ODDD.md). Este archivo conserva la fuente de campos/versiones; ODDD enlaza el modelo sin imponer otra base de datos o un item único para toda la partida.

| Entidad | Campos esenciales | Invariantes |
|---|---|---|
| Nodo | ID, latitud, longitud | ID único, coordenadas válidas. |
| Calle/segmento | ID físico, origen/destino, distancia, tipo, velocidad, dirección | Costo positivo; cruces reconocen el mismo segmento. |
| Refugio | ID, nodo; capacidad solo si se activa extra | Nodo existente. |
| Partida | `runId`, modo, escenario, versiones, semilla y estado privado del generador, estado | Un modo fijo y una partida activa; aleatoriedad aislada por partida. |
| Zombie | ID, tipo, nodo, fase, activación | Dormido oculto en proyección. |
| Sobreviviente | ID, nodo, control, estado, refugio objetivo | Control humano/automático; activo/mordido/evacuado. |
| Orden humana | Partida, turno, personaje, acción, secuencia, destino | Propiedad, idempotencia y cierre. |
| Snapshot | Partida, turno, fase, versión, datos | Inmutable una vez confirmado. |
| Evento de ciudad | ID, segmento, turno objetivo, causa | Aplicación única y trazable. |
| Resultado | Modo, versiones, decisiones, métricas y final | Separar pruebas automáticas de juego. |

`Partida`, `Sobreviviente`, `Zombie` e `IntencionMovimiento` ya existen como dataclasses inmutables en `src/navira/domain/modelo.py`. La partida fija modo, versión de mapa, estado, turno y fase; `validar_mapa()` comprueba referencias. `SnapshotMundo` conserva en memoria el estado completo, cierres, eventos programados/aplicados y estado aleatorio privado. La aplicación de movimientos y transición versionada entre fases están implementadas en memoria. El snapshot durable y la escritura condicional siguen pendientes.

El generador demo admite cohortes de 1 a 200 sobrevivientes; con más de uno elige por semilla entre nodos no refugio. En el mapa actual (cinco nodos, cuatro elegibles) pueden coincidir varios personajes. La capacidad de compartir intersección es un detalle del fixture sintético, no una regla de despliegue ni de seguridad.

En el código, `Calle.id` identifica un sentido dirigido y `Calle.segmento_id` el tramo físico. Las dos direcciones de una misma calle comparten segmento; las calles paralelas usan IDs físicos distintos. El mapa valida IDs únicos, coordenadas WGS84, distancia/velocidad positivas, categorías reconocidas y referencias a nodos existentes. `Mapa.validar_mapa_evaluacion()` exige cuatro refugios en nodos distintos y, por defecto, al menos 200 nodos; ese umbral aproximado no sustituye el requisito objetivo de unas 300 intersecciones. El fixture de cuatro nodos es sintético.

## Estado real y observable

**Real privado:** todos los zombies, activaciones, generador aleatorio, estados de control y datos necesarios para recuperar. **Observable:** zombies visibles, trayectorias permitidas, sobrevivientes, bloqueos y datos públicos de refugios. Credenciales y estado aleatorio no pertenecen a ninguna respuesta de panel o recomendación.

El resolutor privado conserva todos los zombies; el caso de uso `/paso` solo considera activos para bloquear ocupación y cruces del turno. No lee dormidos al calcular su ruta, y no los incluye en errores/respuestas. La proyección de panel y radio todavía no está implementada.

## Versiones

Identidad mínima de una instantánea: `(runId, turno, fase, mapVersion)`; el prototipo agrega una versión monotónica para distinguir cada transición. El coordinador genera snapshots de decisión y resolución completos y permite abrir el siguiente turno solo desde una resolución confirmada por el llamador. Decisiones incorporan esa identidad y sobreviviente/nodo actual. Un reinicio de partida genera nuevo `runId` aunque el turno vuelva a cero.

DynamoDB será la fuente de verdad prevista. La aplicación define un puerto `RepositorioSnapshots` con escritura condicional por versión; el adaptador actual solo coordina hilos del proceso y no es durable. El adaptador DynamoDB debe preparar una versión completa y confirmar un manifiesto/puntero de publicación; los consumidores no leen fragmentos a medio escribir. La lectura inmediata que depende de una escritura confirmada debe ser consistente en la tabla, no depender de un índice eventualmente actualizado.

Antes de fijar formato físico: medir tamaño de snapshots, límites vigentes del servicio y unidades facturables. Si un snapshot requiere fragmentos, publicar solo al confirmar el conjunto; no asumir que un item puede crecer sin límite. Definir retención y exportación; no borrar evidencia de evaluación mediante expiración prematura.

## Recuperación y reproducción

- Un solo escritor del mundo; proteger fase/turno esperado con condiciones de versión.
- Persistir orden aceptada antes del acuse y marcar aplicación para evitar dobles movimientos.
- Guardar configuración, versión de código/mapa, semilla, estado aleatorio privado, eventos, decisiones y órdenes suficiente para reconstrucción exacta dentro de la misma versión de reglas.
- La semilla sola no reproduce decisiones humanas; también conservar su secuencia.
- Con la misma versión de código/mapa, configuración, semilla/estado, eventos y entradas externas, repetir debe reconstruir la secuencia. Cambiar cualquiera de ellos puede desviar llamadas posteriores al generador y modificar la partida completa.
- Una semilla igual no garantiza idénticos zombies si cambian la versión del algoritmo, el orden de consumo aleatorio o los objetivos de persecución. Comparar escenarios con esa limitación explícita.
- El generador y su estado son privados: no se incluyen en `/paso`, radio, panel ni observación pública. Se guardan únicamente en el estado interno necesario para recuperar/auditar.
- Si recuperación segura no está implementada/verificada, reportarlo como limitación e interrumpir explícitamente tras un fallo.
