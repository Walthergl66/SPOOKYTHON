# ADR-051 — Replanificar a un refugio alternativo alcanzable

- Estado: aceptada e implementada localmente; regresiones focalizadas pasan.
- Fecha: 2026-10-28.
- Contexto: el habitante conserva un refugio asignado aunque una horda, zombie, incidente o cruce confirmado elimine toda ruta legal a ese objetivo. El planificador puede entonces devolver el nodo actual como ruta, aunque exista otro refugio alcanzable. La resolución del movimiento ya rechaza el perímetro de la horda, pero esa garantía no elige un destino alternativo.
- Decisión: conservar el refugio asignado mientras haya una ruta legal. Cuando deje de ser alcanzable, planificar contra todos los refugios y comprometer el refugio alcanzable de menor costo. Mantener ese destino alternativo mientras el original continúe inaccesible. Al no haber ningún refugio alcanzable, conservar CA-002-09: salida inmediata legal de bajo riesgo o espera si no existe salida segura conocida.
- Alternativas consideradas: continuar esperando por el destino asignado; permitir el paso por vecinos de la horda; redirigir siempre al refugio más cercano ignorando las rutas de riesgo. Se descartan porque causan detención, violan R-06 o ignoran cierres y peligros del snapshot.
- Consecuencias: rutas individuales y de cohorte pueden cambiar de objetivo; el nodo de horda y sus vecinos permanecen prohibidos y la preferencia blanda por alejarse de zombies no se convierte en bloqueo legal. El siguiente paso mostrado y el automático deben derivarse de la misma ruta/versión de snapshot.
- Verificación: CA-002-15/T-63 y regresiones en `backend/tests/test_decidir_paso.py`; las 66 pruebas focalizadas de planificador, resolutor, panel y simulador pasan con el entorno Python del proyecto; `compileall` y validadores docs/SDD pasan. No se afirma menor tasa de mordidas ni validación visual sobre Manta.
- Relaciones: R-06, CA-002-09/14/15, ADR-034/043, CAM-141, T-55/T-62/T-63.
