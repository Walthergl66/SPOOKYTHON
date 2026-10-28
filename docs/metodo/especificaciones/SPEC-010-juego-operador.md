# SPEC-010 — Juego de operador con mundo en ejecución

ID: SPEC-010  
Estado: en-revision  
Requisitos: PRD-06, PRD-12, TRD-06, TRD-07, TRD-12, TRD-18  
Tareas: P4-06  
Pruebas: T-52, T-53  
Cambio: CAM-101  
Decisión: [ADR-042](../../arquitectura/decisiones/0042-juego-operador-mundo-interactivo.md)
Evidencia: validación API y recorrido parcial del modo en [CAM-101](../../seguimiento/cambios.md#cam-101-juego-como-modo-de-operador-interactivo); T-53 requiere completar el incidente desde la interfaz.

## Objetivo y alcance

«Juego» es la experiencia de operador solicitada por el usuario. Un operador local arranca un mundo automático y, mientras este corre, selecciona una herramienta para agregar habitantes, caminantes, corredores, hordas, dormidos, refugios o incidentes. Simulador conserva su asistente de configuración; Reto conserva sus presets automáticos. El dominio sigue usando solo `simulador` y `juego`: Jugar operador opera un run de `simulador`, no constituye un modo de dominio adicional.

La API local requiere `NAVIRA_LOCAL_DEMO_CONTROL=1`, conexión loopback y Origin same-host. No es apropiada para un despliegue público. No cambia `POST /paso`, no permite editar Reto y no modifica el mundo desde el navegador: las colocaciones se aplican con CAS en el backend.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-010-01 | La navegación inicial conserva el orden Reto, Simulador, Jugar; Jugar identifica con claridad la operación del mundo y muestra su paleta. | T-53 |
| CA-010-02 | Un operador puede iniciar o continuar una demo libre local y usar herramientas solo cuando el run automático está activo; el reloj continúa entre colocaciones. | T-52, T-53 |
| CA-010-03 | El backend rechaza ronda Reto, mundo pausado/sin partida, nodo/calle inexistente, duplicado/cerrado y entradas que exceden límites. No confía en posiciones o identidad visual enviadas por el cliente. | T-52 |
| CA-010-04 | Habitantes y tipos de zombie se agregan a la partida; dormitorios nuevos conservan su estado oculto. Los zombies no se colocan en el nodo de refugio ni sus vecinos. | T-52 |
| CA-010-05 | Refugio crea mapa versionado nuevo y aparece en el panel; incidente cierra el segmento, alerta como aplicado e invalida las rutas comprometidas para recalcular. | T-52, T-53 |
| CA-010-06 | Una intervención se serializa con la ronda y confirma una versión de snapshot siguiente por CAS. Error de conflicto se informa y se puede volver a intentar. | T-52 |

## Modelo y fronteras

- **Entrada de aplicación:** herramienta y un objetivo: `nodo` para actores/refugios, `segmentoId` para incidente.
- **Dominio:** `Sobreviviente`, `Zombie`, `Refugio`, `EventoCierre`, `Partida` y `SnapshotMundo` inmutables existentes.
- **Adaptador:** `POST /demo/operador/elementos`; valida esquema, loopback y mismo origen, traduce errores a HTTP.
- **Frontend:** el mapa encaja el clic en un nodo visible o tramo dibujado. No crea estado local autoritativo.
- **Consistencia:** lock local compartido con el ejecutor automático y escritura CAS. Una acción de operador no debe exponer snapshot privado ni devolver zombies dormidos.

Límites iniciales: 200 habitantes, 200 zombies y 8 refugios por mundo local. Se puede colocar en la ventana jugable derivada del mapa activo; el backend vuelve a validar IDs del grafo. Incidentes ya cerrados se rechazan. La colocación de nuevos dormidos no publica su identidad/posición hasta que la proyección existente considere que se activaron.

## Verificación y estado

T-52 cubre API local, colocación de actores/refugio/cierre, mapa versionado, protección de Reto y objetivo inválido. T-53 cubre build, interacción cartográfica y recorrido visual de la paleta; requiere prueba en navegador sobre el backend reiniciado. CA-010-06 tiene regresión del lock/CAS pendiente más allá de la integración local. Esta SPEC permanece `en-revision` hasta que todos los criterios y límites se prueben; una build sola no la verifica.
