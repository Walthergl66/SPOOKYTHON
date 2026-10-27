# Modelo de datos y consistencia

Estado: nodos, calles dirigidas, refugios y grafo validados están implementados en `backend/src/navira/domain/mapa.py`; `simulation/coordinador.py` crea snapshots completos por fase y `application/snapshots.py` los confirma mediante un puerto CAS. `application/simulacion_automatica.py` confirma preparación y resolución en versiones separadas. El fixture fuente `backend/data/maps/manta-hackathon-v1.json` contiene 44.590 nodos/94.146 sentidos OSM; las partidas Manta derivan una proyección jugable recortada a la ventana urbana de [mapa Manta](mapa-manta.md), sin alterar el archivo fuente. Los cuatro destinos son zonas seguras documentadas para tsunami, no validadas para emergencias ni sismos. El mapa `backend/data/maps/demo-sintetico.json` sigue sirviendo para una partida local efímera. El adaptador `adapters/snapshots_memoria.py` solo sirve en un proceso local; almacenamiento/confirmación durable sigue pendiente. Decisión de consistencia: [ADR-003](../arquitectura/decisiones/0003-estado-y-turnos.md) y [ADR-030](../arquitectura/decisiones/0030-ventana-urbana-zona-jugable.md).

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
| Sesión de jugador | Partida, ID de personaje, estado de aparición, nodo | Un propietario por partida; token opaco entregado solo en cookie; token almacenado como hash. El adaptador actual es volátil. |
| Snapshot | Partida, turno, fase, versión, datos, IDs mordidos en la última resolución | Inmutable una vez confirmado; IDs por resolución únicos. El panel calcula el acumulado desde estados terminales y el indicador reciente desde esos IDs. |
| Compromiso de ruta | Sobreviviente automático, refugio y sufijo dirigido restante | Vive dentro del snapshot privado; solo se recorta al confirmar el movimiento, se elimina en estado terminal y nunca se escribe desde una consulta del panel. |
| Evento de ciudad | ID, segmento, turno objetivo, causa | Aplicación única y trazable. |
| Resultado | Modo, versiones, decisiones, métricas y final | Separar pruebas automáticas de juego. |

`Partida`, `Sobreviviente`, `Zombie` e `IntencionMovimiento` ya existen como dataclasses inmutables en `backend/src/navira/domain/modelo.py`. La partida fija modo, versión de mapa, estado, turno y fase; `validar_mapa()` comprueba referencias. `SnapshotMundo` conserva en memoria el estado completo, cierres, eventos programados/aplicados, IDs de mordidos en su resolución más reciente y estado aleatorio privado. La aplicación de movimientos y transición versionada entre fases están implementadas en memoria. El snapshot durable y la escritura condicional siguen pendientes.

CAM-036 añade `SesionJugador` como valor de aplicación y `RepositorioSesionesMemoria`. La sesión contiene solo propiedad/estado; la identidad del browser se localiza por SHA-256 de un token aleatorio, nunca por un ID enviado desde el cliente. La sesión y el snapshot no comparten una transacción durable; el CAS protege la aparición de mundo en el adaptador local, pero la recuperación multi-proceso y expiración siguen pendientes.

CAM-037 añade `OrdenHumana`, el puerto `RepositorioOrdenes` y el adaptador `RepositorioOrdenesMemoria`. El adaptador serializa con lock la clave `(runId, personajeId, accionId)`, asigna secuencia creciente por partida y conserva solo la última orden por personaje/turno para futura resolución. También mantiene claves anteriores del turno para responder reintentos idempotentes. Se trata de un registro local volátil: todavía no se inyecta en el ciclo del coordinador, no se cierra con una transacción compartida con el snapshot ni se recupera tras reinicio.

El generador demo admite cohortes de 1 a 200 sobrevivientes; si no se entrega semilla, genera una desde entropía del sistema. Con semilla explícita muestrea reproduciblemente las ubicaciones iniciales de sobrevivientes/zombies y la fase de caminantes. En el mapa actual (cinco nodos, cuatro elegibles) pueden coincidir varios personajes. La capacidad de compartir intersección es un detalle del fixture sintético, no una regla de despliegue ni de seguridad. La composición de perfiles se conserva fija mientras P-09 no defina cantidades/distribución oficiales; la horda no cambia su regla provisional mientras P-07 siga abierta.

En el código, `Calle.id` identifica un sentido dirigido y `Calle.segmento_id` el tramo físico. Las dos direcciones de una misma calle comparten segmento; las calles paralelas usan IDs físicos distintos. El mapa valida IDs únicos, coordenadas WGS84, distancia/velocidad positivas, categorías reconocidas y referencias a nodos existentes. `Mapa.validar_mapa_evaluacion()` exige cuatro refugios en nodos distintos y, por defecto, al menos 200 nodos; ese umbral aproximado no sustituye el requisito objetivo de unas 300 intersecciones. El fixture de cuatro nodos es sintético.

## Estado real y observable

**Real privado:** todos los zombies, activaciones, generador aleatorio, estados de control y datos necesarios para recuperar. **Observable:** zombies visibles, trayectorias permitidas, sobrevivientes, bloqueos y datos públicos de refugios. Credenciales y estado aleatorio no pertenecen a ninguna respuesta de panel o recomendación.

El resolutor privado conserva todos los zombies; el caso de uso `/paso` solo considera activos para bloquear ocupación y cruces del turno. No lee dormidos al calcular su ruta, y no los incluye en errores/respuestas. `application/consultar_panel.py` publica mapa y snapshot sin dormidos, semillas, RNG ni escenario privado; añade rutas dirigidas calculadas con la política compartida y peligros visibles del estado actual. No proyecta radio ni eventos futuros; sincronización durable y permisos del panel en despliegue siguen pendientes.

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
