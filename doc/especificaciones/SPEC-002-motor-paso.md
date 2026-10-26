# SPEC-002 — Motor y siguiente paso

ID: SPEC-002
Estado: implementada
Requisitos: PRD-03, PRD-09, TRD-01, TRD-02, TRD-05, TRD-06, TRD-09, TRD-12
Tareas: P0-01, P0-02, P2-01, P2-02, P2-03, P3-01, P3-02, P3-03
Pruebas: T-03, T-04, T-05, T-07, T-08, T-10, T-11, T-22
Cambio: CAM-006
Evidencia: parcial; ver CAM-020 y CAM-028 en [cambios](../cambios.md) y sus reportes locales.

## Objetivo y alcance

Dar un siguiente paso válido y oportuno hacia un refugio considerando costos y peligros. Primero Dijkstra integrado por HTTP; después búsqueda temporal/predicción si mejora resultados. Fuentes canónicas: [API](../contratos/api.md), [algoritmos](../algoritmos.md), [TRD](../TRD.md). No cambiar método/cuerpo de `/paso` ni usar información oculta.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-002-01 | `/paso` autentica, acepta el cuerpo obligatorio y responde solo con `siguienteNodo` en éxito; inválidos tienen error explícito. | T-08 |
| CA-002-02 | Toda decisión generada es vecino habilitado o espera; considera horda/vecinos, cierres y mordidas conocidas. | T-03, T-05, T-07, T-08 |
| CA-002-03 | Repetir solicitud sobre misma instantánea conserva decisión y ninguna respuesta usa otra partida/turno silenciosamente. | T-10 |
| CA-002-04 | Bajo ráfagas conserva límite contractual y se mide p95/errores desde el cliente, con carga y origen declarados. | T-11 |
| CA-002-05 | Una política mejorada se compara con base en escenarios/semillas declarados; no usa dormidos o aleatoriedad privada ni inventa mejora. | T-04, T-22 |

## Plan y módulos

P0 fija API/esquemas; P2 entrega una ronda con Dijkstra; P3 añade horizonte limitado y evaluación separada. Núcleo en rutas/dominio, casos de uso en aplicación, HTTP en API y adaptadores. Incluir presupuesto global del turno y alternativa válida ya calculada; espera no equivale a seguridad.

## Casos límite, dudas y verificación

Sin ruta, origen peligroso, refugio inaccesible, timeout, fase incompatible y calles paralelas. P-01/P-05 condicionan unidades y eficiencia; registrar supuestos en vez de atribuirlos al reto. La referencia base puede verificarse parcialmente por tarea; toda la SPEC solo se verifica al completar los criterios, incluida evaluación de mejora.

La implementación inicial de P0-01/P0-02 cubre el proceso FastAPI, esquemas, API key, `/salud`, `/paso` y fixtures. CAM-012 verifica arranque y contrato HTTP. CAM-013 incorpora Dijkstra genérico; CAM-014 integra el caso de uso con snapshots/mapas inyectados y mapea errores 404/409/503. CAM-020 agrega configuración local de cohortes al ensamblaje demo y un cliente de carga concurrente con resumen de latencias/errores sobre snapshot fijo. CAM-028 añade un evaluador HTTP loopback que mantiene snapshot común por turno, resuelve las intenciones recibidas y vuelve a abrir la decisión para el siguiente turno; la evidencia local cubre 20/80/200 por cinco turnos con semilla explícita. La medición no incluye espera de reloj, distribución oficial, cliente remoto ni evaluación AWS. El app principal conserva espera por defecto. CA-002-02 sigue parcial; falta medir contra el entorno de evaluación, reloj real, idempotencia durable y comparación completa. No se declara T-11 ni la SPEC verificada.
