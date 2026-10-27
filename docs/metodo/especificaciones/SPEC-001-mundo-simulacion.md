# SPEC-001 — Mundo y simulación

ID: SPEC-001
Estado: implementada
Requisitos: PRD-01, PRD-02, PRD-11, TRD-03, TRD-04, TRD-05, TRD-09, TRD-11, TRD-12, TRD-16
Tareas: P1-01, P1-02, P1-03, P1-04, P1-05
Pruebas: T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-09, T-10, T-17, T-18, T-24, T-28, T-29, T-40
Cambio: CAM-078
Evidencia: parcial; ver reporte de generador espacial en resultados.

## Objetivo y alcance

Ejecutar un único mundo de Manta con reglas comunes para humano/automáticos, cuatro zombies y eventos. Fuentes: [reglas](../../dominio/reglas-juego.md), [flujo](../../dominio/flujos/simulador.md), [ODDD](../../dominio/ODDD.md). Excluye camionetas y capacidad extra.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-001-01 | Grafo validado, cuatro refugios y cierres conservan identidad/dirección; un cierre invalida tránsito desde su turno. | T-07 |
| CA-001-02 | Cada tipo respeta movimiento, fase y visibilidad según reglas configuradas/documentadas. | T-01, T-02, T-03, T-04 |
| CA-001-03 | Zombies se mueven primero, todos deciden sobre una instantánea y mordidas detectan nodo final y cada cruce opuesto. | T-05, T-06 |
| CA-001-04 | Llegada y mordida se resuelven en el orden configurado, sin evacuar un mordido en ese turno. | T-09 |
| CA-001-05 | Snapshot publicado es completo y una reejecución no duplica turno; reiniciar partida no reutiliza decisiones. | T-10, T-18 |
| CA-001-06 | Mismas intenciones y estado producen mismo resultado con control humano/automático. | T-17 |
| CA-001-07 | Escenario, semilla, versiones, configuración y entradas externas idénticos reproducen el reporte dentro de la misma versión; el reporte omite zombies dormidos. | Parcial: T-24 reproduce cinco turnos locales y oculta dormidos; T-10 durable y recuperación/reporte integral pendientes |
| CA-001-08 | El generador demo crea exactamente la población solicitada (1–200), fuera de nodos refugio, con posiciones repetibles por semilla. | T-10 |
| CA-001-09 | Las partidas nuevas usan estado aleatorio independiente; cambiar semilla/estado/eventos puede divergir en ubicaciones, movimiento zombie y rutas posteriores. Se respetan reglas y la misma instantánea conserva decisión HTTP estable. | Parcial: semilla nueva, posiciones/fase inicial aleatorias, divergencia de rutas entre semillas y decisión estable al repetir snapshot; composición/eventos oficiales y persistencia integral pendientes (T-10, T-24) |
| CA-001-10 | La demo ofrece intensidades sintéticas baja/media/alta que escalan la cantidad inicial de zombies al grafo, distribuyen ubicaciones por sectores disponibles y componen caminantes/corredores/hordas/dormidos según el perfil. Misma semilla y configuración reproducen posiciones y tipos; dormidos siguen ocultos. | T-28 |
| CA-001-11 | La demo puede programar incidentes viales aleatorios que cierran segmentos desde turnos definidos; el panel solo publica el incidente aplicado, y la planificación usa cierres confirmados. No se simulan ni atribuyen amenazas sísmicas/tsunami. | T-29 |
| CA-001-12 | En partidas Manta ningún zombie aparece ni ejecuta un tramo hacia el nodo refugio o una intersección enlazada directamente; el conjunto no depende de dirección de calle ni cierres. Una entidad ya dentro solo puede permanecer o salir. Mapas sintéticos no se alteran. | T-40 |

## Plan y módulos

P1-01 valida mapa/fixture; P1-02 define entidades e intenciones; P1-03 implementa reglas puras; P1-04 integra reloj/snapshots; P1-05 fija escenarios. La demo local configura densidad sintética y distribución estratificada por sectores; usa `EventoCierre` existente para incidentes viales y los proyecta cuando ya se aplicaron. Las cantidades oficiales, movimiento de horda, incidentes sísmicos y tsunami permanecen pendientes. Áreas previstas: dominio, simulación, aplicación y adaptadores. No consultar HTTP dentro del dominio ni publicar mundo privado.

## Casos límite, dudas y verificación

Probar nodos sin salida, segmentos paralelos, bloqueo de puentes, múltiples mordidas, snapshot incompleto y repetición de eventos. P-01 a P-05 y P-07 a P-09 siguen pendientes: pruebas deben explicitar configuración provisional. Ejecutar T indicadas antes de cerrar; no hay resultados actuales. Validar también tiempo completo con SPEC-005.

P1-01 sigue parcial en cuanto a validación territorial y reglas oficiales. CAM-021 creó el fixture OSM inicial (300 nodos/599 sentidos); CAM-073 amplió el fixture fuente a 44.590 nodos y 94.146 sentidos en una envolvente rectangular con margen del cantón; CAM-077 deriva para partidas Manta un subgrafo de 35.518/75.548 dentro de la ventana urbana solicitada. CAM-025 prueba integración del motor; CAM-073 comprueba integridad/cobertura fuente, CAM-077 el recorte jugable y CAM-078 la exclusión zombie topológica de una cuadra. No se certifican todas las calles, rutas peatonales, el límite municipal ni seguridad real. Seguridad ante sismos no evaluada (P-14). P1-02 añade entidades, modos e intenciones con siete pruebas. P1-03 contiene un resolutor puro de turno con once pruebas (CAM-009); las reglas siguen parcialmente provisionales. P1-04 añade coordinación por fases, cierres programados, snapshots versionados, plazo monotónico, CAS en memoria y CLI local JSONL. CAM-018 agregó perfiles reducidos; CAM-022 documentó el requisito estocástico; CAM-023 aleatoriza estado inicial de demo y usa semilla impredecible por defecto con replay explícito; CAM-024 prueba replay multi-turno y estabilidad de decisión por snapshot. P1-05 queda parcial: composición sintética fija, corredores deterministas, hordas estáticas, P-07/P-09, durabilidad y evaluación integral pendientes. Reloj continuo y transporte/publicación siguen pendientes; la SPEC no está verificada.
