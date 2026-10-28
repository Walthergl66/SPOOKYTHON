# SPEC-010 — Juego de operador con mundo en ejecución

ID: SPEC-010  
Estado: en-revision  
Requisitos: PRD-06, PRD-12, PRD-14, TRD-06, TRD-07, TRD-12, TRD-18, TRD-20
Tareas: P4-06  
Pruebas: T-52, T-53, T-54, T-55, T-56, T-57, T-65
Cambio: CAM-136
Decisión: [ADR-042](../../arquitectura/decisiones/0042-juego-operador-mundo-interactivo.md)
Evidencia: validación API y recorrido parcial del modo en [CAM-101](../../seguimiento/cambios.md#cam-101-juego-como-modo-de-operador-interactivo); inicio vacío cubierto por [CAM-102](../../seguimiento/cambios.md#cam-102-juego-inicia-con-el-mapa-vacío); cierre de calle por clic en mapa cubierto por [CAM-103](../../seguimiento/cambios.md#cam-103-identificador-estable-al-colocar-incidente); paridad del planificador con incidentes, hordas y zombies cubierta en [CAM-104](../../seguimiento/cambios.md#cam-104-reglas-de-riesgo-y-rutas-compartidas-en-juego). Faltan otros criterios de T-53.

## Objetivo y alcance

«Juego» es la experiencia de operador solicitada por el usuario. Un operador local arranca un mundo automático y, mientras este corre, selecciona una herramienta para agregar habitantes, caminantes, corredores, hordas, dormidos, refugios o incidentes. Simulador conserva su asistente de configuración; Reto conserva sus presets automáticos. El dominio sigue usando solo `simulador` y `juego`: Jugar operador opera un run de `simulador`, no constituye un modo de dominio adicional.

La superficie local requiere `NAVIRA_LOCAL_DEMO_CONTROL=1`, conexión loopback y Origin same-host. La demo pública temporal habilita Reto/Simulador/Jugar operador mediante el perfil separado y sesión aislada descritos en [SPEC-011](SPEC-011-demo-publica-multisesion.md); no es una consola administrativa productiva. No cambia `POST /paso`, no permite editar Reto y no modifica el mundo autoritativamente desde el navegador: las colocaciones se aplican con CAS en el backend.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-010-01 | La navegación inicial conserva el orden Reto, Simulador, Jugar; Jugar identifica con claridad la operación del mundo y muestra su paleta. | T-53 |
| CA-010-02 | Un operador puede iniciar o continuar una demo libre local y usar herramientas solo cuando el run automático está activo; el reloj continúa entre colocaciones. | T-52, T-53 |
| CA-010-03 | El backend rechaza ronda Reto, mundo pausado/sin partida, nodo/calle inexistente, duplicado/cerrado y entradas que exceden límites. No confía en posiciones o identidad visual enviadas por el cliente. | T-52 |
| CA-010-04 | Habitantes y tipos de zombie se agregan a la partida; dormitorios nuevos conservan su estado oculto. Los zombies no se colocan en el nodo de refugio ni sus vecinos. | T-52 |
| CA-010-05 | Refugio crea mapa versionado nuevo y aparece en el panel; incidente cierra el segmento, alerta como aplicado e invalida las rutas comprometidas para recalcular. | T-52, T-53 |
| CA-010-06 | Una intervención se serializa con la ronda y confirma una versión de snapshot siguiente por CAS. Error de conflicto se informa y se puede volver a intentar. | T-52 |
| CA-010-07 | «Nueva partida» inicia con cartografía/calles, cero habitantes, zombies, refugios e incidentes. El reloj sigue disponible en un mundo sin sobrevivientes y el operador puede colocar elementos después del inicio. | T-54 |
| CA-010-08 | Mientras Jugar tiene un mundo operador activo o pausado, ofrece «Iniciar nueva partida». La acción reemplaza el run por otro vacío, activa el reloj y limpia la selección local; Pausar/Continuar permanecen disponibles para el mundo actual. | T-56 |
| CA-010-09 | Al entrar a Jugar desde Reto o Simulador, la interfaz oculta el mundo anterior y presenta el inicio de un mundo operador vacío. Al iniciar, el servidor crea un run nuevo aun si el run anterior estaba activo o pausado; la paleta solo se habilita sobre el nuevo mundo operador. | T-57 |
| CA-010-10 | «Detener mundo» termina el turno ya iniciado, cancela el reloj, limpia el run publicado y devuelve la app a su entrada inicial; «Iniciar nueva partida» conserva la función de reemplazar el mundo operador por otro vacío. | T-56 |
| CA-010-11 | Al colocar un habitante, el servidor le asigna un perfil narrativo no usado por ningún habitante del run; la elección no altera ubicación, reloj, rutas ni resolución. | T-65 |

## Modelo y fronteras

- **Entrada de aplicación:** herramienta y un objetivo: `nodo` para actores/refugios, `segmentoId` para incidente.
- **Dominio:** `Sobreviviente`, `Zombie`, `Refugio`, `EventoCierre`, `Partida` y `SnapshotMundo` inmutables existentes.
- **Adaptador:** `POST /demo/operador/elementos`; valida esquema, loopback y mismo origen, traduce errores a HTTP.
- **Inicio vacío:** `POST /demo/operador/iniciar` crea una demo operador sin actores, refugios ni eventos iniciales; conserva el grafo vial Manta.
- **Frontend:** el mapa encaja el clic en un nodo visible o tramo dibujado. No crea estado local autoritativo.
- **Consistencia:** lock local compartido con el ejecutor automático y escritura CAS. Una acción de operador no debe exponer snapshot privado ni devolver zombies dormidos.

Límites iniciales: 200 habitantes, 200 zombies y 8 refugios por mundo local. Se puede colocar en la ventana jugable derivada del mapa activo; el backend vuelve a validar IDs del grafo. Incidentes ya cerrados se rechazan. La colocación de nuevos dormidos no publica su identidad/posición hasta que la proyección existente considere que se activaron.

## Verificación y estado

T-52 cubre API local, colocación de actores/refugio/cierre, mapa versionado, protección de Reto y objetivo inválido. T-54 prueba inicio vacío, avance del reloj y colocación posterior. T-56 prueba que la API reemplaza un mundo operador activo por un run vacío nuevo; el smoke visual local confirmó que el botón queda visible al lado de «Continuar mundo» con una partida pausada. No se pulsó para preservar ese mundo. En T-53, CAM-103 confirma visualmente selección de calle e incidente aplicado en backend; siguen pendientes el recorrido de todas las herramientas y la comprobación de objetivos inválidos desde UI. CA-010-06 tiene regresión del lock/CAS pendiente más allá de la integración local. Esta SPEC permanece `en-revision` hasta que todos los criterios y límites se prueben; una build sola no la verifica.
