# SPEC-001 — Mundo y simulación

ID: SPEC-001
Estado: implementada
Requisitos: PRD-01, PRD-02, TRD-03, TRD-04, TRD-05, TRD-09, TRD-11, TRD-12
Tareas: P1-01, P1-02, P1-03, P1-04, P1-05
Pruebas: T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-09, T-10, T-17, T-18, T-24
Cambio: CAM-007
Evidencia: pendiente

## Objetivo y alcance

Ejecutar un único mundo de Manta con reglas comunes para humano/automáticos, cuatro zombies y eventos. Fuentes: [reglas](../reglas-juego.md), [flujo](../flujos/simulador.md), [ODDD](../ODDD.md). Excluye camionetas y capacidad extra.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-001-01 | Grafo validado, cuatro refugios y cierres conservan identidad/dirección; un cierre invalida tránsito desde su turno. | T-07 |
| CA-001-02 | Cada tipo respeta movimiento, fase y visibilidad según reglas configuradas/documentadas. | T-01, T-02, T-03, T-04 |
| CA-001-03 | Zombies se mueven primero, todos deciden sobre una instantánea y mordidas detectan nodo final y cada cruce opuesto. | T-05, T-06 |
| CA-001-04 | Llegada y mordida se resuelven en el orden configurado, sin evacuar un mordido en ese turno. | T-09 |
| CA-001-05 | Snapshot publicado es completo y una reejecución no duplica turno; reiniciar partida no reutiliza decisiones. | T-10, T-18 |
| CA-001-06 | Mismas intenciones y estado producen mismo resultado con control humano/automático. | T-17 |
| CA-001-07 | Escenario, semilla, versiones, configuración y entradas externas idénticos reproducen el reporte dentro de la misma versión; el reporte omite zombies dormidos. | T-10, T-24 |
| CA-001-08 | El generador demo crea exactamente la población solicitada (1–200), fuera de nodos refugio, con posiciones repetibles por semilla. | T-10 |
| CA-001-09 | Las partidas nuevas usan estado aleatorio independiente; cambiar semilla/estado/eventos puede divergir en ubicaciones, movimiento zombie y rutas posteriores. Se respetan reglas y la misma instantánea conserva decisión HTTP estable. | T-10, T-24 |

## Plan y módulos

P1-01 valida mapa/fixture; P1-02 define entidades e intenciones; P1-03 implementa reglas puras; P1-04 integra reloj/snapshots; P1-05 fija escenarios. Áreas previstas: dominio, simulación, aplicación y adaptadores. No consultar HTTP dentro del dominio ni publicar mundo privado.

## Casos límite, dudas y verificación

Probar nodos sin salida, segmentos paralelos, bloqueo de puentes, múltiples mordidas, snapshot incompleto y repetición de eventos. P-01 a P-05 y P-07 a P-09 siguen pendientes: pruebas deben explicitar configuración provisional. Ejecutar T indicadas antes de cerrar; no hay resultados actuales. Validar también tiempo completo con SPEC-005.

P1-01 es parcial: el modelo `Mapa`/`Grafo` tiene validación genérica; CAM-021 añade un fixture OSM de Manta con 300 nodos, 599 sentidos, cuatro anclas en puntos marcados “Zona Segura” de los mapas de tsunami del GAD y caminos dirigidos desde cada nodo a algún refugio. Las pruebas cubren integridad y procedencia, no exactitud cartográfica, cobertura completa de los barrios, rutas peatonales ni seguridad real. Seguridad ante sismos no evaluada (P-14). P1-02 añade entidades, modos e intenciones con siete pruebas. P1-03 contiene un resolutor puro de turno con once pruebas (CAM-009); las reglas siguen parcialmente provisionales. P1-04 añade coordinación por fases, cierres programados, snapshots versionados, plazo monotónico, CAS en memoria y CLI local JSONL. CAM-018 agrega perfiles reducidos con semilla; CAM-022 documenta el nuevo requisito estocástico. La demo actual solo aleatoriza caminantes y ubicaciones iniciales de cohortes; no aleatoriza composición/ubicaciones zombie por ejecución, mantiene fija la horda y por defecto usa semilla 31. P1-05 debe completar generador estocástico y reproducción auditable sin fijar la distribución oficial pendiente P-09 ni movimiento de horda P-07. Reloj continuo, durabilidad y transporte/publicación siguen pendientes; la SPEC no está verificada.
