# SPEC-004 — Personaje humano

ID: SPEC-004
Estado: implementada
Requisitos: PRD-05, PRD-06, TRD-03, TRD-04, TRD-05, TRD-06, TRD-09, TRD-12
Tareas: P4B-01, P4B-02, P4B-03, P5-04
Pruebas: T-12, T-13, T-14, T-15, T-16, T-17, T-19
Cambio: CAM-041
Evidencia: parcial en [CAM-036](../cambios.md#cam-036-sesión-propietaria-y-aparición-humana), [CAM-037](../cambios.md#cam-037-órdenes-humanas-idempotentes), [CAM-038](../cambios.md#cam-038-controles-humanos-en-frontend), [CAM-039](../cambios.md#cam-039-integración-local-del-ciclo-de-juego), [CAM-040](../cambios.md#cam-040-reloj-y-juego-demo-local) y [CAM-041](../cambios.md#cam-041-contador-visual-del-deadline).

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

CAM-040 conecta un runner local de dos segundos, deadline monotónico de 1,7 s, rechazo de órdenes tardías y juego sintético opt-in; una prueba HTTP espera la siguiente ronda y confirma que re-unirse conserva el personaje. CAM-041 expone el restante para un contador visual informativo. P-16 queda resuelto para el proceso local; multi-proceso requiere otro adaptador. P-11/P-12 siguen abiertos. Sesión volátil, reinicio durable, radio y T-14/T-15/T-19 integral siguen pendientes. La cadencia solo se verificó con un smoke de ronda, no como métrica p95/sostenida. Esta SPEC no está verificada integralmente.
