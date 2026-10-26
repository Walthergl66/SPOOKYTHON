# SPEC-001 — Mundo y simulación

ID: SPEC-001
Estado: implementada
Requisitos: PRD-01, PRD-02, TRD-03, TRD-04, TRD-05, TRD-09, TRD-11, TRD-12
Tareas: P1-01, P1-02, P1-03, P1-04, P1-05
Pruebas: T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-09, T-10, T-17, T-18
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

## Plan y módulos

P1-01 valida mapa/fixture; P1-02 define entidades e intenciones; P1-03 implementa reglas puras; P1-04 integra reloj/snapshots; P1-05 fija escenarios. Áreas previstas: dominio, simulación, aplicación y adaptadores. No consultar HTTP dentro del dominio ni publicar mundo privado.

## Casos límite, dudas y verificación

Probar nodos sin salida, segmentos paralelos, bloqueo de puentes, múltiples mordidas, snapshot incompleto y repetición de eventos. P-01 a P-05 y P-07 a P-09 siguen pendientes: pruebas deben explicitar configuración provisional. Ejecutar T indicadas antes de cerrar; no hay resultados actuales. Validar también tiempo completo con SPEC-005.

P1-01 tiene implementación parcial: `Mapa`/`Grafo`, carga JSON y validaciones tienen diez pruebas de dominio. El fixture es sintético de cuatro nodos; todavía no existe el mapa real de unas 300 intersecciones. P1-02 añade entidades, modos e intenciones con siete pruebas. P1-03 contiene un resolutor puro de turno con once pruebas (CAM-009); aplica movimientos, mordidas, evacuación y paridad del motor en ambos modos, pero las reglas siguen parcialmente provisionales y la visibilidad de dormidos no está implementada. P1-04 añade coordinación por fases, cierres programados, snapshots versionados, plazo monotónico y un puerto CAS con adaptador en memoria (CAM-010/CAM-011); CAM-015 agrega un bootstrap local de demo que carga mapa sintético y confirma la preparación del primer turno en fase de decisiones; CAM-016 orquesta rondas automáticas reproducibles sobre esas transiciones. No implementa DynamoDB, reloj continuo ni transporte/publicación; P1-05 sigue pendiente, por lo que esta SPEC no está verificada.
