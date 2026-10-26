# Módulos backend y dependencias

Estado: implementación por fases. `src/navira/api/` contiene esquemas, autenticación y rutas HTTP más `WS /ws/panel`; `src/navira/application/` incluye decisión Dijkstra, proyección observable, transición versionada y `EjecutarRondaAutomatica`; `src/navira/adapters/` incluye snapshots/mapas locales; `src/navira/domain/` contiene grafo y entidades/intenciones; `src/navira/simulation/` aplica cierres y construye snapshots. `src/navira/demo.py` ensambla contextos efímeros del mapa sintético para API y ejecutores, con perfiles y población inicial reproducible; `src/navira/simulador_demo.py` ejecuta rondas, `src/navira/carga_http.py` genera ráfagas concurrentes sobre snapshot fijo y `src/navira/evaluacion_local.py` consulta `/paso` por turno y resuelve esas respuestas en el simulador con Uvicorn loopback. El evaluador alinea los inicios de turno a una cadencia monotónica configurable (2 s por defecto), mide retraso y duración de ciclo; sigue siendo exploratorio y no reproduce reloj continuo ni entorno remoto. El punto de entrada API configura su fixture solo con `NAVIRA_DEMO=1` y admite variables de población/escenario/semilla; sin opt-in conserva el respaldo de espera. El socket de panel publica snapshots completos al cambiar la versión; el almacenamiento sigue en memoria. Dataset/distribuciones oficiales, persistencia durable/distribuida, reloj continuo, catálogo de eventos de juego, planificación temporal y evaluación siguen pendientes.

Lenguaje, contextos e invariantes: [ODDD](../ODDD.md). Requisitos técnicos: [TRD](../TRD.md); antes de implementar elegir la [SPEC](../especificaciones/README.md) correspondiente. La orientación a objetos no exige crear clases para funciones sin estado.

| Módulo | Responsabilidad | No debe hacer | Verificación |
|---|---|---|---|
| `domain/` | Grafo, entidades, transitabilidad, mordidas y llegadas | Importar FastAPI/boto3, usar HTTP o decidir permisos web | `test_mapa.py` y `test_modelo.py` validan mapa, estado y contexto de intención. |
| `routing/` | Dijkstra dirigido, pronóstico observable y selección temporal experimental de rutas/refugios | Modificar mundo, leer dormidos/estado RNG o convertir puntaje de exposición en probabilidad real | `test_dijkstra.py`, `test_ruta_temporal.py` y `test_prediccion_rutas.py`; CAM-034 prueba pronóstico sin fase privada y reporta supuestos. |
| `routing/temporal.py` | Búsqueda experimental acotada `(nodo, turnos)`, espera, pronóstico observable inyectado y presupuesto | Leer RNG/dormidos, decidir por sí solo reemplazar `/paso` o convertir exposición en probabilidad de supervivencia | `test_ruta_temporal.py` cubre ruta/espera/cierre/horizonte/presupuesto; CAM-033 registra tiempo local por invocación. |
| `routing/prediccion.py` | Estimar ocupación futura de amenazas observables y devolver condiciones temporales con supuestos declarados | Recibir `Partida`, fase privada, RNG o dormidos; afirmar movimiento oficial de horda o supervivencia calibrada | `test_prediccion_rutas.py` cubre caminantes, corredores, horda, validación y rechazo de dormidos. |
| `evaluacion_rutas.py` | Comparar políticas en mundos sintéticos emparejados y reportar estados/tiempos de función | Ser benchmark HTTP, usar datos ocultos en el recomendador o declarar cumplimiento T-22/T-11 | `test_evaluacion_rutas.py`; reporte de 27 pares en CAM-035. |
| `simulation/` | Plazo de turno, fases, zombies, eventos y resolución | Mantener la única copia de estado o ejecutar coordinadores duplicados | `test_resolver.py` cubre movimientos/mordidas; `test_coordinador.py` cubre modo por fases, versionado/eventos/plazo local. Persistencia aún pendiente. |
| `application/` | Preparar/resolver turno, decidir paso, consultar proyección del panel y definir puertos de I/O | Depender de esquemas HTTP o SDK AWS; exponer el snapshot privado | `test_decidir_paso.py`, `test_snapshots_persistidos.py` y `test_panel.py` cubren decisión, CAS local y filtrado/proyección pública. |
| `simulador_demo.py` | Ejecutar rondas automáticas locales con argumentos y emitir reporte JSONL | Ser reloj continuo, persistir resultados o representar el mapa real de Manta | `test_simulador_demo.py` cubre límite, semilla, movimientos, evacuación y argumentos inválidos. |
| `carga_http.py` | Medir respuestas de `/paso` desde cliente con ráfagas y resumen de latencias/errores | Avanzar el mundo, fingir concurrencia del evaluador o usar claves embebidas en código | `test_carga_http.py` verifica conteos/percentiles; smoke Uvicorn local requerido para el transporte real. |
| `evaluacion_local.py` | Ejecutar cohortes locales con solicitudes HTTP a `/paso`, aplicar las respuestas al turno, sostener cadencia configurable y resumir latencia/retrasos | Exponer rutas nuevas, publicar el estado zombie privado, afirmar cumplimiento T-11 o simular AWS/reloj continuo | `test_evaluacion_local.py` comprueba loopback HTTP, avance multi-turno y cadencia; CAM-029 registra una corrida temporizada exploratoria. |
| `application/consultar_panel.py` | Proyectar mapa versionado y snapshot activo para observación, omitiendo dormidos/RNG | Cambiar el mundo, publicar el snapshot completo o aceptar órdenes | `test_panel.py` comprueba estado sin partida, proyección versionada y filtro de zombies dormidos. |
| `application/juego.py` | Reservar una sesión humana propietaria, elegir aparición válida o mantenerla pendiente y confirmarla por CAS | Admitir modo simulador, aceptar posición del cliente, leer dormidos para planificar o persistir sesión en memoria como durable | `test_juego_sesion.py` cubre aparición, propietario concurrente, turno tardío, cookie segura y errores de elegibilidad. Hook de siguiente turno requiere integración con el coordinador de juego. |
| `api/routes.py` — `POST /juego/unirse` | Validar Origin, devolver estado propio y emitir cookie opaca HttpOnly | Aceptar credencial de servicio, devolver token en JSON o autorizar por ID de jugador | `test_juego_sesion.py` cubre cookie/atributos y rechazo cross-origin. Ruta deshabilitada si no se inyecta el servicio. |
| `api/routes.py` — `WS /ws/panel` | Emitir el snapshot observable inicial, detectar nuevas versiones confirmadas y heartbeat; rechazar otro origen | Aplicar deltas, controlar una partida, persistir historial o coordinar workers | `test_panel.py` cubre handshake, ocultamiento, cambio de versión, heartbeat, origen y reconexión. |
| `player/` | Aparición, propiedad lógica y orden humana por turno | Autorizar con cookies directamente o mover posiciones | Idempotencia y cierre de acciones. |
| `api/` | Esquemas, autenticación, HTTP y WebSocket | Implementar reglas o búsqueda dentro de controladores | Pruebas de contrato. |
| `adapters/` | DynamoDB futuro, snapshot en memoria, reloj, cliente HTTP del motor, métricas y proyecciones de transporte | Cambiar políticas del dominio o anunciar durabilidad del adaptador en memoria | Tres pruebas del CAS local; DynamoDB e integración siguen pendientes. |
| `main.py` | Ensamblar dependencias y arrancar componentes | Contener lógica de simulación | Arranque comprobable. |

## Dirección de importaciones

`domain` no importa módulos externos del proyecto. `routing` y las políticas de `player` dependen de tipos del dominio. `application` orquesta esas políticas y define puertos. El coordinador se ensambla con reloj, repositorio y cliente de decisiones inyectados; el código de transporte del simulador queda en adaptadores. `api` y `adapters` dependen de contratos internos; el núcleo nunca importa esos adaptadores. `main` ensambla implementaciones concretas.

Las credenciales de sesión se validan en el borde y producen una identidad simple para el caso de uso. La regla de propiedad se verifica dentro del caso de uso con esa identidad, para no depender únicamente de una pantalla.

## Casos de uso mínimos

1. Iniciar/cerrar partida y programar evento.
2. Preparar/publicar una instantánea observable de turno.
3. Decidir paso automático sobre esa instantánea.
4. Incorporar personaje humano y registrar/reemplazar orden.
5. Resolver todas las intenciones mediante un único validador.
6. Consultar proyección y exportar resultado.

No crear un servicio por entidad ni extraer microservicios inicialmente. Los comentarios y docstrings explican invariantes, unidades, fase del turno y motivos difíciles de deducir; no repiten cada línea. Un cambio de responsabilidad requiere actualizar este documento y el historial.
