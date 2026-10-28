# SPEC-009 — Flujo dedicado de la prueba de fuego

ID: SPEC-009
Estado: en-revision
Requisitos: PRD-06, PRD-07, TRD-02, TRD-10, TRD-11
Tareas: P4-05, P5-01, P5-03
Pruebas: T-11, T-18, T-47, T-48, T-49, T-50, T-57
Cambio: CAM-099
Evidencia: campañas locales secuenciales 3×5 minutos con tres semillas en [CAM-098](../../calidad/resultados/campana-reto-cam098.md) y [CAM-099](../../calidad/resultados/repeticiones-reto-cam099.md); AWS pendiente.

## Objetivo y alcance

Origen: solicitud del usuario de agregar una opción dedicada al reto y conservar «Simulador» como demo libre. El nuevo flujo presenta las configuraciones de las tres rondas del Track A separadas de la demo. Continúa usando el modo automático `simulador`, el motor y el resolutor compartidos; no agrega un tercer modo de dominio ni modifica el juego humano.

El reto define 20 caminantes en Anochecer; 80 sobrevivientes con caminantes, corredores y hordas y un puente colapsado en Medianoche; 200 sobrevivientes con todos los tipos, incluidos dormidos, y dos calles bloqueadas en Apocalipsis. Cada ronda tiene duración objetivo de cinco minutos. El enunciado no fija cantidad/densidad zombie, composición proporcional, turno exacto de los eventos, ni puente/calles concretas. El flujo adopta densidad media y eventos determinados por semilla como supuestos locales, visibles y sustituibles; no se anuncian como parámetros oficiales. Ver P-09/P-15.

La demo libre conserva sus perfiles, intensidad, refugios y control actuales. En Reto sobre Manta se aplica un foco urbano provisional para amenazas/eventos y se ofrece reiniciar el preset actual; el reto se ejecuta como operación separada local. AWS, persistencia durable, reportes oficiales y cumplimiento integral de T-11 siguen fuera de esta especificación hasta verificarlos.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-009-01 | El selector ofrece Simulador, Reto y Jugar; Reto muestra configuraciones fijas 20/80/200 y Simulador conserva sus controles libres. | T-47 |
| CA-009-02 | La ronda 1 genera solo caminantes; ronda 2 genera caminantes, corredores y hordas; ronda 3 incluye los cuatro tipos. La intensidad media se identifica como provisional. | T-47 |
| CA-009-03 | La ronda 2 programa un colapso de un segmento etiquetado como puente; la ronda 3 programa dos segmentos distintos; sus turnos y segmentos reproducen con la misma semilla. Ronda 1 no agrega eventos de reto. | T-18, T-47 |
| CA-009-04 | La operación de reto no cambia los defaults, eventos ni controles del endpoint de demo libre; humano y automáticos conservan el mismo resolutor. | T-47 |
| CA-009-05 | La UI distingue configuración/reporte de evaluación y advierte que densidad y calendario exacto son provisionales. No afirma que una medición local sea AWS, T-11 completa o evaluación aprobada. | T-47 |
| CA-009-06 | En el fixture Manta, las personas de cada ronda aparecen solo en las zonas de Tarqui, Los Esteros, Barbasquillo y Jocay; el reparto es equilibrado, usa nodos viales alcanzables por ruta dirigida a un refugio y se reproduce con la semilla. Simulador libre mantiene su muestreo general. Las áreas y el reparto se declaran aproximaciones configurables porque el reto no da polígonos ni cupos por sector. | T-47 |
| CA-009-07 | Desde una partida Reto existente se puede reiniciar la misma ronda. El servidor crea un `runId` y mundo nuevos, conserva el preset de población y no sustituye una ronda distinta o una partida libre. Si no hay ronda Reto para reiniciar, el endpoint responde 409. | T-47 |
| CA-009-08 | En las rondas Reto del fixture Manta, al menos la cuota redondeada del 80% de cada tipo de zombie queda dentro de 3.500 m del ancla urbana documentada; los eventos R2/R3 prefieren segmentos en esa zona si hay candidatos. Simulador libre conserva su muestreo global y el conteo/composición provisional no cambian. | T-47 |
| CA-009-09 | Un botón principal unifica los estados del run: «Iniciar» sin ronda en ejecución, «Pausar» activa y «Continuar» pausada. Pausar/continuar conserva `runId`, ronda y mundo; «Reiniciar Rn» permanece disponible para recrear el preset actual. | T-48 |
| CA-009-10 | Un preset Reto nuevo puede reemplazar explícitamente un run Reto pausado o un run activo/pausado de Simulador o Jugar. Un Reto activo no se reemplaza por otro inicio Reto; debe pausarse antes. Cada reemplazo crea mundo y `runId` nuevos. | T-49, T-57 |
| CA-009-12 | Al entrar a Reto desde otra experiencia, la UI reinicia la ronda seleccionada a R1, limpia selecciones/avisos del modo previo y oculta snapshot, actores y métricas que no correspondan al run activo. El mundo se sustituye solo al pulsar iniciar. | T-57 |
| CA-009-11 | El evaluador local ejecuta R1, R2 y R3 en ese orden, con un run/preset/semilla por ronda y una ventana de 150 slots de 2 s (cinco minutos). Registra solicitudes reales, turnos activos, slots ociosos, resultados, eventos programados/aplicados y errores; al terminar el mundo no fabrica actividad. | T-50, T-11 |

## Plan y módulos

PRD-07 y P5-03 son propietarios del requisito de tres rondas; P5-01 cubre medición. El flujo de interfaz vive en frontend; la preparación de escenarios/eventos y la selección aleatoria de inicios por sector, en aplicación/simulación backend; la API solo adapta solicitudes. La aproximación de sectores está registrada en [ADR-037](../../arquitectura/decisiones/0037-spawn-reto-cuatro-sectores.md), la concentración de amenazas en [ADR-038](../../arquitectura/decisiones/0038-foco-amenazas-reto.md), el reinicio de ronda en [ADR-039](../../arquitectura/decisiones/0039-reinicio-ronda-reto.md) y el reemplazo explícito al cambiar de modo en [ADR-044](../../arquitectura/decisiones/0044-reemplazo-explicito-al-cambiar-de-modo.md), que sustituye la política anterior de [ADR-040](../../arquitectura/decisiones/0040-reemplazo-reto-pausado.md). El dominio continúa con dos modos según [ADR-002](../../arquitectura/decisiones/0002-dos-modos.md). Contratos de evaluación y límites: [SPEC-005](SPEC-005-aws-evaluacion.md), [reglas](../../dominio/reglas-juego.md) y [pendientes](../../seguimiento/pendientes.md).

## Riesgos y verificación

P-09/P-15 quedan abiertos hasta que la organización del reto confirme densidad y calendarios. CAM-098 demuestra que la semilla evaluada completó 150 turnos activos por ronda durante cinco minutos; con otras semillas el mundo aún puede terminar antes. Persistencia, repetición de campaña, entorno oficial/AWS y criterios externos requieren evidencia independiente. No marcar verificada hasta completar CA y registrar reporte real.
