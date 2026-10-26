# SPEC-004 — Personaje humano

ID: SPEC-004
Estado: implementada
Requisitos: PRD-05, PRD-06, TRD-03, TRD-04, TRD-05, TRD-06, TRD-09, TRD-12
Tareas: P4B-01, P4B-02, P4B-03, P5-04
Pruebas: T-12, T-13, T-14, T-15, T-16, T-17, T-19
Cambio: CAM-039
Evidencia: parcial en [CAM-036](../cambios.md#cam-036-sesión-propietaria-y-aparición-humana), [CAM-037](../cambios.md#cam-037-órdenes-humanas-idempotentes), [CAM-038](../cambios.md#cam-038-controles-humanos-en-frontend) y [CAM-039](../cambios.md#cam-039-integración-local-del-ciclo-de-juego).

## Objetivo y alcance

Un jugador entra a una partida habilitada, aparece aleatoriamente y decide cómo llegar a un refugio. Un único humano y partida activa en el mínimo. Fuentes: [jugador](../flujos/jugador.md), [modos](../modos.md), [API](../contratos/api.md). No incluye multijugador simultáneo, cuentas o movimiento libre.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-004-01 | Dada partida habilitada con cupo, la sesión obtiene personaje/nodo elegible al inicio de turno; sin candidatos informa el problema. | T-12 |
| CA-004-02 | Dada sesión ajena o refresco, no roba personaje ni crea pasos extra; cliente nunca determina posición confirmada. | T-13 |
| CA-004-03 | Dada orden recibida fuera del cierre, se rechaza sin llevarla al siguiente turno; duplicados válidos conservan acuse y la última orden válida domina. | T-14 |
| CA-004-04 | Sin orden o conexión, espera mientras continúa el mundo; reconectar recupera estado real sin revivir. | T-15 |
| CA-004-05 | Humano/automático comparten resolutor; no se admiten humanos en pruebas oficiales; radio solo sugiere con información permitida. | T-16, T-17 |
| CA-004-06 | Elegir vecino/espera y entender confirmación/resultado funciona con mouse y teclado y cuenta atrás del servidor. | T-19 |

## Plan, límites y verificación

P4B-01/02/03 cuentan con implementación local parcial. CAM-039 conecta aparición pendiente, órdenes humanas y decisiones automáticas al mismo ciclo/resolutor; el lock compartido serializa registro y resolución solo si ambas dependencias reciben la misma instancia. No existe todavía reloj de producción ni runner ensamblado. P-11/P-12/P-16 siguen abiertos; P-16 está mitigado en el coordinador local pero falta aplicar deadline monotónico. Radio, recuperación tras reinicio y T-14/T-15/T-19 integral siguen pendientes. El cierre humano de 1,7 s es parámetro de diseño sujeto a medición. Esta SPEC no está verificada integralmente.
