# SPEC-004 — Personaje humano

ID: SPEC-004
Estado: implementada
Requisitos: PRD-05, PRD-06, PRD-14, TRD-03, TRD-04, TRD-05, TRD-06, TRD-09, TRD-12, TRD-20
Tareas: P4B-01, P4B-02, P4B-03, P5-04
Pruebas: T-12, T-13, T-14, T-15, T-16, T-17, T-19, T-25, T-65
Cambio: CAM-047
Evidencia: parcial en [CAM-036](../../seguimiento/cambios.md#cam-036-sesión-propietaria-y-aparición-humana), [CAM-037](../../seguimiento/cambios.md#cam-037-órdenes-humanas-idempotentes), [CAM-038](../../seguimiento/cambios.md#cam-038-controles-humanos-en-frontend), [CAM-039](../../seguimiento/cambios.md#cam-039-integración-local-del-ciclo-de-juego), [CAM-040](../../seguimiento/cambios.md#cam-040-reloj-y-juego-demo-local), [CAM-041](../../seguimiento/cambios.md#cam-041-contador-visual-del-deadline), [CAM-042](../../seguimiento/cambios.md#cam-042-sugerencia-de-radio-en-controles-humanos), [CAM-043](../../seguimiento/cambios.md#cam-043-recuperar-la-sesión-humana-al-reconectar), [CAM-045](../../seguimiento/cambios.md#cam-045-accesibilidad-de-navegación-y-tiempo-de-juego), [CAM-046](../../seguimiento/cambios.md#cam-046-expiración-local-de-sesión-humana) y [CAM-047](../../seguimiento/cambios.md#cam-047-recorrido-manual-de-teclado-parcial).

## Objetivo y alcance

Un jugador entra a una partida habilitada, aparece aleatoriamente y decide cómo llegar a un refugio. Un único humano y partida activa en el mínimo. Fuentes: [jugador](../../dominio/flujos/jugador.md), [modos](../../dominio/modos.md), [API](../../arquitectura/contratos/api.md). No incluye multijugador simultáneo, cuentas o movimiento libre.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-004-01 | Dada partida habilitada con cupo, la sesión obtiene personaje/nodo elegible al inicio de turno; sin candidatos informa el problema. | T-12 |
| CA-004-02 | Dada sesión ajena o refresco, no roba personaje ni crea pasos extra; cliente nunca determina posición confirmada. | T-13 |
| CA-004-03 | Dada orden recibida fuera del cierre, se rechaza sin llevarla al siguiente turno; duplicados válidos conservan acuse y la última orden válida domina. | T-14 |
| CA-004-04 | Sin orden o conexión, espera mientras continúa el mundo; reconectar recupera estado real sin revivir. | T-15 |
| CA-004-05 | Humano/automático comparten resolutor; no se admiten humanos en pruebas oficiales; radio solo sugiere con información permitida. | T-16, T-17 |
| CA-004-06 | Elegir vecino/espera y entender confirmación/resultado funciona con mouse y teclado y cuenta atrás del servidor. | T-19 |
| CA-004-07 | En demo, la sesión expira tras el TTL deslizante configurado; las rutas notifican 410 y el personaje/cupo no pasa a otra cookie. | T-25 |
| CA-004-08 | El personaje humano recibe un perfil narrativo libre del catálogo del run al confirmarse su aparición; no repite el perfil de otro sobreviviente ni cambia las reglas o la decisión humana. | T-65 |

## Plan, límites y verificación

CAM-040 conecta un runner local de dos segundos, deadline monotónico de 1,7 s, rechazo de órdenes tardías y juego sintético opt-in; una prueba HTTP espera la siguiente ronda y confirma que re-unirse conserva el personaje. CAM-041 expone el restante para un contador visual informativo. CAM-042 muestra la siguiente calle recomendada desde `rutasPrevistas` y requiere una acción humana explícita para enviarla. CAM-043 agrega recuperación HTTP de la sesión existente y prueba la posición del snapshot actual y última orden, sin crear personaje al faltar cookie. CAM-045 agrega skip link, foco en selector y anuncio de reloj limitado por umbrales; falta recorrido manual con lector de pantalla para completar T-19. CAM-046 aplica solo a la demo un TTL deslizante configurable de 30 minutos y HTTP 410; el tombstone retiene el cupo tras expirar y no habilita transferencia. P-12 queda parcialmente resuelto localmente, pero expiración/revocación durable y recuperación tras reinicio siguen pendientes. P-16 queda resuelto para el proceso local; multi-proceso requiere otro adaptador. P-11 sigue abierto. T-14/T-15 integral y la cadencia sostenida también siguen pendientes. Esta SPEC no está verificada integralmente.
