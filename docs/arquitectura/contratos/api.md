# Contratos HTTP

Estado: `/salud`, `/paso`, `GET /panel/estado`, `GET /panel/mapa`, `POST /juego/unirse`, `GET /juego/mi-personaje` y `POST /juego/accion` tienen implementación local. Las rutas de mutación del juego validan `Origin` del mismo host; la sesión y las órdenes son de memoria. `NAVIRA_GAME_DEMO=1` ensambla un juego sintético con runner de turno de dos segundos; la aplicación predeterminada continúa sin partida. No hay endpoints desplegados. Solo el formato obligatorio de `/paso` y el estado mínimo provienen del reto; las rutas adicionales son diseño del equipo.

La configuración local optativa `NAVIRA_DEMO=1` acepta `NAVIRA_DEMO_MAP`, `NAVIRA_DEMO_SEED`, `NAVIRA_DEMO_SCENARIO` y `NAVIRA_DEMO_SURVIVORS` para iniciar el fixture sintético. Una semilla configurada hace reproducible el inicio; si se omite, el proceso genera una semilla nueva. La semilla/estado privado no forma parte del contrato HTTP. El cliente `python -m navira.carga_http` puede enviar solicitudes concurrentes a `/paso`; requiere una configuración coincidente en servidor/cliente y `NAVIRA_API_KEY` en el entorno del cliente. No cambia el contrato HTTP ni expone configuración de demo en las rutas. Las ráfagas repiten el mismo snapshot y sirven para medir la ruta de decisión; no simulan avance del reloj ni supervivencia.

`NAVIRA_GAME_DEMO=1` selecciona un juego local sintético y arranca un único runner por instancia ASGI. El servidor prepara zombies, abre `DECISIONES` por 1,7 s desde el inicio monotónico del turno, rechaza órdenes nuevas al vencer y resuelve junto con las decisiones NPC; los 300 ms restantes del período nominal de 2 s se reservan para procesar/publicar el resultado. Registro y cierre comparten una puerta `RLock` de proceso. El runner se detiene al cerrar la app y no restaura estado tras reinicio; la cadencia debe medirse antes de un despliegue.

## API obligatoria del motor

```http
POST /paso
x-api-key: <secreto-de-servicio>
Content-Type: application/json

{"sobrevivienteId":"S-0089","nodoActual":"N-0117","turno":142}
```

```json
{"siguienteNodo":"N-0118"}
```

Éxito 200; respuesta menor a 500 ms. Conservar nombre, método, campos y cuerpo de éxito. Puede devolver el mismo nodo. Resolver partida activa en servidor sin exigir un campo adicional al evaluador. Mantener la misma decisión para una solicitud repetida sobre la misma instantánea. La ruta completa y las explicaciones van en otro canal.

Nota sin cambiar códigos HTTP (ADR-028): `NAVIRA_API_KEY`, `NAVIRA_COOKIE_SECURE` y `NAVIRA_LOCAL_DEMO_CONTROL` se leen al arrancar (en `main.py`), no por petición; cambiar la clave o los flags exige reiniciar el proceso. Sin clave configurada, `POST /paso` responde 503; con clave, la credencial se comprueba antes que el esquema (401 antes que 422).

Errores previstos: 401 por credencial ausente/incorrecta; 422 por esquema inválido; 404 por sobreviviente inexistente; 409 por turno/fase/posición incompatible; 503 si el estado o la versión de mapa confirmados no están disponibles. La configuración ausente de `NAVIRA_API_KEY` también produce 503. El caso de uso con estado mapea esos errores, cubierto por pruebas ASGI; el app base sin estado sigue respondiendo espera. Estos errores cuentan en la medición si aparecen en el flujo normal. Nunca responder con un turno anterior para ocultarlos.

## Rutas y permisos

| Ruta prevista | Identidad | Resultado |
|---|---|---|
| `GET /salud` | Lectura pública mínima | Salud, sin secretos o volcado interno. |
| `GET /mapa` | API key de servicio | Grafo técnico versionado. |
| `GET /estado` | API key de servicio | Estado observable del turno requerido/activo. |
| `GET /panel/mapa` | Lectura de panel limitada | Grafo público para visualización. |
| `GET /panel/estado` | Lectura de panel limitada | Proyección observable y métricas permitidas. |
| `GET /panel/ruta/{sobreviviente_id}` | Lectura de panel limitada | Calcula la ruta observable de un solo sobreviviente activo seleccionado en modo simulador; respuesta versionada por partida/turno/snapshot. |
| `WS /ws/panel` | Origen del mismo host; lectura pública | Snapshots observables completos y heartbeat; sin credencial maestra. |
| `POST /juego/unirse` | Creación/recuperación de sesión temporal | Personaje o estado pendiente de aparición. |
| `GET /juego/mi-personaje` | Cookie de sesión existente | Snapshot del personaje propio y última orden recibida; no crea sesión. |
| `POST /juego/accion` | Sesión propietaria | Acuse de orden; no mueve posición. |
| `GET /juego/recomendacion` | Sesión propietaria | Sugerencia actual con límite de frecuencia. |
| `POST /admin/partidas` | Operador | Iniciar partida si no hay una activa. |
| `POST /admin/partidas/{runId}/finalizar` | Operador | Cierre explícito y motivo. |
| `POST /admin/eventos` | Operador | Evento validado para un turno. |
| `GET /demo/simulador` | Proceso local habilitado y loopback | Estado de una demo local. |
| `GET /demo/sesion` | Cookie anónima same-origin | Prepara un mundo público independiente y devuelve solo estado, no token. |
| `POST /demo/simulador/{iniciar,pausar,reanudar,reiniciar}` | Opt-in local/loopback o sesión pública + Origin same-host | Control del simulador sintético correspondiente únicamente a la sesión que presenta la cookie. |
| `POST /demo/simulador/detener` | Opt-in local/loopback o sesión pública + Origin same-host | Termina ordenadamente el turno ya iniciado, apaga el reloj y devuelve esa sesión a `sin_partida`; no crea un run de reemplazo. |
| `POST /demo/operador/iniciar` | Opt-in local/loopback o sesión pública + Origin same-host | Inicia un mundo de Jugar vacío y sustituye solo el run de esa sesión. |
| `POST /demo/operador/elementos` | Opt-in local/loopback o sesión pública + Origin same-host | Agrega actor/refugio o cierra segmento en el mundo de esa sesión; CAS/validaciones siguen en backend. |
| `POST /reto/iniciar` | Opt-in local/loopback o sesión pública + Origin same-host | Inicia preset Reto aislado en la sesión. |
| `POST /reto/reiniciar` | Opt-in local/loopback o sesión pública + Origin same-host | Reinicia el Reto de la sesión actual con un run nuevo. |

`POST /demo/simulador/detener` no recibe cuerpo y es idempotente: si no hay un run, devuelve estado `sin_partida` con `runId` nulo. Si hay un turno en curso, señaliza la detención antes de esperar el lock del resolutor; ese turno termina, no comienza uno adicional, y después se libera el contexto visible. `/panel/estado` y el siguiente evento WebSocket reportan `sin_partida`. El operador puede iniciar un run nuevo desde cualquiera de las tres experiencias.

### Control de demo local

CAM-050 agrega controles de desarrollo que solo se ensamblan si `NAVIRA_LOCAL_DEMO_CONTROL=1`; el cuerpo de inicio/reinicio recibe escenario, población (1–200), `zombies` opcional (1–200), refugios opcionales y semilla opcional. El tablero actual envía 42 zombies por defecto y el backend aplica el conteo solicitado exactamente cuando hay nodos elegibles suficientes; posiciones y composición mixta siguen siendo sintéticas/aleatorias. Si un cliente legado omite `zombies`, se conserva el conteo por `intensidad`. `eventosCiudad` es un campo legado aceptado por compatibilidad, pero se ignora: el control local siempre sortea al inicio 1–10 incidentes reproducibles, independientemente del conteo zombie (ADR-032/033). `GET /demo/simulador` expone los conteos iniciales confirmados. `GET /panel/estado` publica eventos aplicados con `segmentoId`, `lat` y `lng` del punto medio; el calendario futuro no forma parte de la respuesta. El proceso verifica IP cliente loopback y Host localhost; las operaciones POST además exigen Origin same-host. Si el flag no está activo, las rutas responden 404. El frontend no recibe clave de servicio.

El perfil `NAVIRA_LOCAL_DEMO_CONTROL` conserva loopback exclusivamente. La variante de URL pública se habilita solo con `NAVIRA_PUBLIC_DEMO_CONTROL=1` y el aislamiento por cookie de [SPEC-011](../../metodo/especificaciones/SPEC-011-demo-publica-multisesion.md); no activar ambos perfiles como sustitutos. Es una demo temporal, no consola administrativa productiva. Pausar evita abrir un turno nuevo; un turno ya iniciado puede completar su resolución. Reiniciar genera otro run y otra semilla por defecto.

El contrato de operador recibe un tipo de herramienta y un único objetivo. Tipos aceptados: `habitante`, `caminante`, `corredor`, `horda`, `dormido`, `refugio`, `incidente`. Habitante/zombie/refugio requieren `nodo`; incidente requiere `segmentoId`. Límite por mundo local: 200 habitantes, 200 zombies y 8 refugios. La API vuelve a validar el nodo/tramo contra la versión vigente del mapa; zombies rechazan el nodo de refugio y sus vecinos. Un refugio agrega una versión de mapa. Incidente cierra el segmento inmediatamente, registra un evento aplicado y limpia rutas comprometidas para que la planificación siga los cierres. El acuse incluye solo `aceptado`, `elementoId`, `tipo`, `runId` y `snapshotVersion`, nunca entidades privadas o RNG. Dormidos se mantienen fuera de `/panel/estado` hasta activarse. Ver [SPEC-010](../../metodo/especificaciones/SPEC-010-juego-operador.md) y [ADR-042](../decisiones/0042-juego-operador-mundo-interactivo.md).

`POST /reto/iniciar` recibe `{ "ronda": 1|2|3, "semilla": entero opcional }`. Define 20 caminantes; 80 caminantes/corredores/hordas sin dormidos; o 200 con todos los tipos, respectivamente. Usa intensidad media provisional y cadencia nominal de 2 s. Ronda 2 escoge un puente etiquetado para turno 50; ronda 3 cierra dos segmentos distintos en turnos 50 y 100; R1 no agrega evento de reto. El enunciado no especifica densidad zombie, proporciones, sitio ni momento exacto: esos valores son supuestos locales. El inicio Reto sustituye el run local actual, sea de Simulador o Jugar, y genera un `runId` nuevo; un Reto activo responde 409 para impedir que se pise por un segundo inicio Reto, mientras que uno pausado se puede reemplazar. Las rondas se inician individualmente; no se automatiza aún la secuencia de quince minutos. El endpoint no cambia el contrato obligatorio `POST /paso` ni queda expuesto en modo público.



`POST /reto/reiniciar` no recibe cuerpo: exige que el control tenga una ronda Reto previa, recrea su mismo preset con semilla aleatoria nueva e inicia otro `runId`; puede sustituir la ronda Reto en curso o pausada. Si no hay ronda Reto previa responde 409. Comparte protección local de `POST /reto/iniciar` y no cambia el contrato de `/paso`.

### Perfil público temporal por navegador

Con `NAVIRA_PUBLIC_DEMO_CONTROL=1`, `GET /demo/sesion` crea o confirma una sesión anónima. La respuesta contiene solo estado/alcance/persistencia; el identificador aleatorio viaja en cookie `navira_demo_session` (HttpOnly, SameSite=Strict, Secure según configuración), no en JSON. Middleware resuelve un control aislado para `/panel/*`, `/demo/*`, `/reto/*` y `/paso`; los WebSockets del panel buscan la misma cookie y no reciben token en el protocolo. Mutaciones conservan validación `Origin` same-host. El límite por defecto es tres sesiones; excederlo responde 429 y `Retry-After: 30`. `NAVIRA_PUBLIC_SESSION_IDLE_SECONDS` define el TTL deslizante de 10.800 s y `NAVIRA_PUBLIC_MAX_SESSIONS` la capacidad. Reiniciar proceso elimina sesiones y mundos. Este modo solo se sirve detrás del proxy HTTPS descrito en [SPEC-011](../../metodo/especificaciones/SPEC-011-demo-publica-multisesion.md); no cambia la API key requerida por `/paso` ni publica credenciales al navegador.

En el fixture Manta, Reto concentra una cuota provisional del 80% de cada tipo zombie dentro de 3.500 m de un ancla central aproximada (Parque La Dolorosa/R-03); el remanente se sortea fuera del foco. Los cierres de R2/R3 se eligen de segmentos dentro del foco cuando existen. Conteos, densidad media, radio y proporción son supuestos sintéticos, no parámetros oficiales. Este sesgo no se aplica a demo libre ni a mapas sintéticos.

Las rutas de panel evitan enviar `x-api-key` maestra al navegador. Tienen proyección y límites propios; no son una puerta de entrada al estado real. La CLI administrativa tampoco conserva secretos en argumentos o ejemplos versionados.

`POST /juego/unirse` está implementado localmente bajo inyección explícita de `UnirseAJuego`. Devuelve `runId`, `jugadorId`, estado y nodo únicamente del propio personaje; el token opaco solo viaja en una cookie `HttpOnly; Secure; SameSite=Strict; Path=/juego`. El endpoint rechaza solicitudes sin `Origin` o con origen distinto. `NAVIRA_COOKIE_SECURE=0` existe solo para pruebas/desarrollo explícito; nunca debe usarse en un despliegue público. En `NAVIRA_GAME_DEMO=1`, `NAVIRA_GAME_SESSION_IDLE_SECONDS` configura el plazo deslizante de inactividad (predeterminado 1800 segundos). Las rutas de unión, recuperación y acción responden HTTP 410 para una cookie vencida y la invalidan en el navegador; la política queda lista para volver a entrar en una partida futura. El adaptador guarda hash de token y conserva un tombstone de propiedad para impedir que otro visitante tome el mismo personaje en la partida actual; sesiones/tombstones se pierden al reiniciar, por lo que esta política no habilita publicación productiva. El hook `incorporar_aparicion_pendiente()` se llama desde el coordinador local antes del movimiento zombie.

`GET /juego/mi-personaje` permite recuperar el estado de una sesión ya existente asociada a esa cookie. No acepta una identidad de jugador en la URL/cuerpo y no crea reservas. Devuelve el nodo y el estado del personaje desde el snapshot actual, no desde su aparición original, junto con la última orden recibida del repositorio local; la respuesta incluye `Cache-Control: no-store`. Sin cookie válida responde 403; cookie vencida 410; estado de partida no disponible 503. La lectura válida renueva el TTL local. No requiere `Origin` porque no altera estado y la cookie usa `SameSite=Strict`. Este endpoint recupera sesiones dentro de la vida del proceso solamente: no habilita restauración tras reinicio.

`POST /juego/accion` está implementado localmente bajo inyección explícita de `RegistrarOrdenHumana`. Recibe el cuerpo del ejemplo de Orden humana, pero contrasta run/personaje con la cookie propietaria; solo acepta una sesión activa, personaje humano activo, modo juego, turno actual y fase `DECISIONES`. La posición de origen siempre se toma del snapshot vigente, no del nodo guardado en la sesión de aparición. El destino debe ser espera o vecino dirigido abierto, y los nodos de horda/vecinos bloqueados no son elegibles. La presencia de otro zombie activo permite una orden de riesgo, dejando la mordida al resolutor. Responde `accionId`, secuencia creciente del servidor, `estado=recibida` y turno; no cambia posición. Una sesión vencida en el juego demo responde 410 y conserva el personaje/cupo mediante tombstone.

El repositorio en memoria atomiza idempotencia y reemplazo dentro del proceso. Para un `accionId` ya conocido, el mismo contenido devuelve el acuse previo incluso si la fase ya cerró; otro contenido produce 409. La última orden válida por personaje/turno sustituye la anterior y conserva su secuencia para auditoría local. En `NAVIRA_GAME_DEMO=1`, una puerta monotónica compartida cierra nuevas órdenes a los 1,7 s y serializa registro frente a resolución. CAM-040 cubre el comportamiento local; el lock no coordina procesos, y ni snapshot ni orden son durables, por lo que no equivale a persistencia productiva.

### Panel HTTP de solo lectura — implementación parcial

`GET /panel/estado` devuelve `sin_partida` cuando no se inyecta una partida activa; para una ronda activa devuelve run, modo, turno, fase, versión de snapshot/mapa, sobrevivientes, zombies activos, movimientos de zombies visibles, cierres, áreas de horda, metadatos `eventosCiudad` de cierres ya aplicados, rutas previstas dirigidas para personajes activos y métricas por modo. El snapshot general proyecta rutas compartidas durante `decisiones`. Fuera de esa fase, en modo automático, `GET /panel/ruta/{sobreviviente_id}` calcula solo la ruta del habitante seleccionado (CAM-093), con `runId`, `turno`, `snapshotVersion`, `sobrevivienteId` y `trayecto`; el juego humano conserva la ruta solo durante `decisiones`. Esto evita recalcular rutas para toda la cohorte en cada fase. El cliente acepta la respuesta solo si coincide con partida, turno y selección actuales. En `metricas`, `mordidos` es el total de sobrevivientes en estado terminal mordido y `mordidosUltimoTurno` es el número de personas únicas mordidas por la resolución confirmada más reciente; no son dos acumulados sumables. Nunca publica segmentos de incidentes futuros. En juego puede incluir `decisionRestanteMs`, calculado por el servidor desde el deadline monotónico; es informativo para la UI y nunca autoriza una orden. Zombies que siguen dormidos, escenario privado y estado/semilla del generador se omiten completamente. CAM-059 hace que panel/decisión compartan el trayecto calculado para el mismo run/snapshot/personaje; su primer nodo siguiente coincide con la intención del servidor. Una ruta es una vista previa de decisión, no un movimiento confirmado ni garantía de seguridad. CAM-042 reutiliza esa ruta observable como sugerencia opcional de Radio Navira; el cliente no calcula una ruta con datos privados y solo registra una orden si la persona elige explícitamente «Usar sugerencia». No se implementa aún el endpoint separado `GET /juego/recomendacion` de la tabla de rutas previstas. `GET /panel/mapa` devuelve únicamente el grafo versionado asociado a la partida activa (nodos, sentidos de calle y refugios); sin partida o versión disponible responde 503. Las lecturas del panel son GET y no exigen la clave maestra del motor.

`GET /panel/ruta/{sobreviviente_id}` responde 404 cuando no existe un sobreviviente activo con ese ID o cuando ya no es elegible; 503 si no hay partida activa, mapa o planificador disponible. No modifica la partida ni revela el estado privado de zombies dormidos.

CAM-157: `GET /panel/mapa` envía `ETag` ligado a `mapVersion`, `Cache-Control: private, no-cache` y `Vary: Accept-Encoding, Cookie`. El cliente puede revalidar con `If-None-Match`; un mapa ya cacheado de esa versión devuelve `304` sin cuerpo. Solicitudes gzip aceptadas reciben nivel 1, con caché de dos versiones en memoria; `gzip;q=0` queda sin comprimir. El cache contiene únicamente la geometría pública e inmutable del mapa, nunca snapshots ni estado privado. La primera proyección fría local midió 407–449 ms, así que la caché evita cargas repetidas pero no garantiza que la primera respuesta cumpla p95 ≤150 ms.

El endpoint local `GET /demo/simulador/candidatos` devuelve nodos/calles del fixture fuente y `limitesJugables` para el mapa de selección. El cliente filtra el exterior y coloca solo dentro. Al iniciar una partida Manta, el backend deriva el subgrafo; un refugio seleccionado fuera recibe 422. El contrato obligatorio `POST /paso` no cambia.

Los campos concretos se fijan en los esquemas OpenAPI de la aplicación y sus pruebas ASGI. El panel obtiene estado/mapa al abrir, puede refrescar manualmente y CAM-032 agrega `WS /ws/panel` para snapshots completos al cambiar la versión y heartbeat de conexión. El socket requiere `Origin` del mismo host. La proyección de ruta se limita a los personajes activos y solo se calcula en fase de decisiones; no es evaluación temporal futura. El socket lee el repositorio de snapshots en memoria, por lo que no ofrece replay durable o coordinación multi-proceso.

## Orden humana

```json
{
  "runId": "juego-001",
  "turno": 12,
  "personajeId": "P-01",
  "siguienteNodo": "N-0118",
  "accionId": "orden-00031"
}
```

El servidor valida sesión, propiedad, modo, fase, turno y movimiento topológico. Genera una secuencia creciente. Repetir `accionId` con el mismo cuerpo devuelve el acuse existente; usarlo con otro cuerpo produce conflicto. La última orden válida aceptada antes del cierre sustituye la previa; la persistencia confirma el orden, no un timestamp del cliente. Si se permite concurrencia en reemplazos, usar una condición de versión para que una escritura tardía no revierta una más nueva.

Acuse previsto:

```json
{"accionId":"orden-00031","secuencia":31,"estado":"recibida","turno":12}
```

Rechazar órdenes tardías o de otra partida sin trasladarlas al turno siguiente. Falta de orden implica espera. Un acuse confirma recepción persistida; el movimiento se confirma al resolver el turno. No rechazar una orden solo por riesgo estimado, pero sí por transitabilidad/reglas de horda.

## Estado observable mínimo

```json
{
  "runId":"ejemplo",
  "turno":142,
  "fase":"zombies_movidos",
  "mapVersion":"manta-v1",
  "zombies":[{"id":"Z-01","tipo":"corredor","nodo":"N-0120"}],
  "aristasBloqueadas":["E-034"],
  "movimientosZombies":[{"id":"Z-01","trayecto":["N-0118","N-0119","N-0120"]}],
  "sobrevivientes":[{"id":"S-0089","nodo":"N-0117","estado":"activo","perfilNarrativo":{"id":"NAV-P0001","nombre":"Ana Acosta","edad":29,"ocupacion":"comerciante","descripcion":"Perfil ficticio de ambientación."}}]
}
```

Todos los IDs del ejemplo son ilustrativos. `movimientosZombies` amplía el estado mínimo para resolver cruces; nunca publica trayectos de dormidos que sigan ocultos. En implementación, fijar esquemas de solicitudes, respuestas y errores mediante OpenAPI y pruebas, sin romper el contrato obligatorio.

`sobrevivientes[].perfilNarrativo` es opcional para compatibilidad con snapshots antiguos y puede ser `null`. Si existe, contiene solo `id`, `nombre`, `edad`, `ocupacion` y `descripcion` ficticios. El catálogo actual se genera de forma determinista a partir de vocabulario local y contiene 500 perfiles; una partida selecciona hasta 200 distintos con una semilla derivada por separado para no alterar la aleatoriedad del mundo. El panel valida el objeto antes de renderizarlo. No usarlo como input de rutas, decisiones o puntuación.
