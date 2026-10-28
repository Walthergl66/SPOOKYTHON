# Flujo del operador

Estado: diseño previsto. Primera interfaz administrativa: CLI; una interfaz web posterior debe usar autorización equivalente.

CAM-050 añade un tablero local de demo sintética con inicio, pausa, continuación y reinicio. Se habilita solo con `NAVIRA_LOCAL_DEMO_CONTROL=1`, loopback y Origin same-host; no sustituye el panel administrativo productivo ni modifica eventos oficiales. El formulario configura perfil sintético y población, con semilla opcional solo en API. En el tablero no se muestra estado RNG ni se inventan métricas.

CAM-079 fija 4× como velocidad inicial de esta demo local. Desde CAM-100 el tablero no ofrece selector y mantiene la cadencia en 4×; no altera las acciones por turno ni salta rondas. Ver [flujo del simulador](simulador.md).

CAM-081 elimina del menú el control de incidentes viales aleatorios y los deja siempre activos al iniciar o reiniciar la demo. El endpoint ignora el campo legado `eventosCiudad`; los eventos continúan siendo genéricos, aleatorios y visibles en el panel solo después de aplicarse. Ver [ADR-032](../../arquitectura/decisiones/0032-incidentes-viales-siempre-activos-en-demo.md).

## Preparar e iniciar

1. Autenticarse con credencial administrativa independiente.
2. Comprobar salud, versión del mapa, recursos y que no haya otra partida activa.
3. En Simulador, pulsar «Iniciar simulación», elegir los cuatro puntos seguros y después configurar entre 1 y 200 habitantes y entre 1 y 200 zombies. La demo conserva escenario mixto y velocidad fija 4×; refugios, población y cantidad se envían al servidor.
4. Crear `runId` y estado inicial. Las cantidades libres pertenecen al perfil sintético y no alteran los presets de Reto.
5. Iniciar reloj y habilitar observación. En juego, habilitar la incorporación de un humano.

## Durante la ejecución

- Generar cierres con identificador, turno objetivo y segmento afectado; rechazar solicitudes ambiguas o pasadas.
- Vigilar latencia, errores, retraso de reloj y consumo; registrar cada intervención.
- No mover personajes manualmente, revelar dormidos al motor o modificar dificultad sin registro.
- Un visitante no cambia modo, reinicia ni termina una ronda. Una interrupción administrativa se registra como tal.

## Cerrar y entregar

1. Finalizar por duración/regla de escenario o instrucción administrativa autorizada.
2. Exportar resultados, semilla, eventos, versión de código/mapa y órdenes humanas si existen.
3. Clasificar el reporte por modo y guardar evidencia de latencia desde el cliente utilizado.
4. Reiniciar con otro `runId` solo al terminar la partida anterior; invalidar cachés y sesiones de control correspondientes.
5. Antes de entregar, comprobar enlaces públicos, Budget, costos y pitch mediante [plan](../../seguimiento/plan-implementacion.md).
