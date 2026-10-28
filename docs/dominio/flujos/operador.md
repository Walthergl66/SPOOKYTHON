# Flujo del operador

Estado: la demo local tiene control de simulación y colocación interactiva parcial; no existe una interfaz administrativa productiva.

CAM-050 añade un tablero local de demo sintética con inicio, pausa, continuación y reinicio. Se habilita solo con `NAVIRA_LOCAL_DEMO_CONTROL=1`, loopback y Origin same-host; no sustituye el panel administrativo productivo ni modifica eventos oficiales. El formulario configura perfil sintético y población, con semilla opcional solo en API. En el tablero no se muestra estado RNG ni se inventan métricas.

CAM-079 fija 4× como velocidad inicial de esta demo local. Desde CAM-100 el tablero no ofrece selector y mantiene la cadencia en 4×; no altera las acciones por turno ni salta rondas. Ver [flujo del simulador](simulador.md).

CAM-101 redefine «Jugar» como modo operador: escoger habitante, caminante, corredor, horda, dormido, refugio o incidente y hacer clic en el mapa. El cliente encaja nodos o segmentos, pero el backend valida IDs/topología y confirma cada acción en el snapshot del servidor. CAM-102 define que cada mundo nuevo conserva la red de calles de Manta, pero inicia sin habitantes, zombies, refugios ni eventos. El reloj admite ese estado vacío y continúa en cuanto el operador lo inicia. Un run Reto se rechaza; un run pausado no permite colocar.

CAM-081 elimina del menú el control de incidentes viales aleatorios y los deja siempre activos al iniciar o reiniciar la demo. El endpoint ignora el campo legado `eventosCiudad`; los eventos continúan siendo genéricos, aleatorios y visibles en el panel solo después de aplicarse. Ver [ADR-032](../../arquitectura/decisiones/0032-incidentes-viales-siempre-activos-en-demo.md).

## Preparar e iniciar

1. Autenticarse con credencial administrativa independiente.
2. Comprobar salud, versión del mapa, recursos y que no haya otra partida activa.
3. En Simulador, pulsar «Iniciar simulación», elegir los cuatro puntos seguros y después configurar entre 1 y 200 habitantes y entre 1 y 200 zombies. En Juego, «Iniciar mundo operador» crea un mapa de Manta vacío de actores, refugios y eventos para que el operador lo pueble.
4. Crear `runId` y estado inicial. Las cantidades libres pertenecen al perfil sintético y no alteran los presets de Reto.
5. Iniciar reloj y habilitar observación. En juego, habilitar la incorporación de un humano.

En Jugar, el botón «Iniciar nueva partida» se mantiene disponible mientras el mundo operador está activo o pausado. Crea un `runId` distinto en el mismo mapa vacío y reemplaza el run anterior; Pausar/Continuar siguen controlando el run que se está observando. No se permite usarlo para sustituir una ronda Reto.

## Durante la ejecución

- Generar cierres con identificador, turno objetivo y segmento afectado; rechazar solicitudes ambiguas o pasadas.
- Vigilar latencia, errores, retraso de reloj y consumo; registrar cada intervención.
- Las herramientas de Juego agregan entidades; no reubican manualmente personajes existentes ni revelan dormidos antes de activarse. Cada incidente cierra una vía y replantea las rutas.
- Un visitante no cambia modo, reinicia ni termina una ronda. Una interrupción administrativa se registra como tal.

## Cerrar y entregar

1. Finalizar por duración/regla de escenario o instrucción administrativa autorizada.
2. Exportar resultados, semilla, eventos, versión de código/mapa y órdenes humanas si existen.
3. Clasificar el reporte por modo y guardar evidencia de latencia desde el cliente utilizado.
4. Reiniciar con otro `runId` solo al terminar la partida anterior; invalidar cachés y sesiones de control correspondientes.
5. Antes de entregar, comprobar enlaces públicos, Budget, costos y pitch mediante [plan](../../seguimiento/plan-implementacion.md).
