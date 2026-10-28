# SPEC-002 — Motor y siguiente paso

ID: SPEC-002
Estado: implementada
Requisitos: PRD-03, PRD-09, PRD-10, TRD-01, TRD-02, TRD-05, TRD-06, TRD-09, TRD-12, TRD-14
Tareas: P0-01, P0-02, P2-01, P2-02, P2-03, P3-01, P3-02, P3-03
Pruebas: T-03, T-04, T-05, T-07, T-08, T-10, T-11, T-22, T-30, T-31, T-32, T-33, T-34, T-35, T-36, T-46, T-55
Cambio: CAM-104
Evidencia: parcial; ver CAM-020, CAM-028, CAM-029, CAM-033, CAM-034, CAM-035, CAM-044, CAM-058, CAM-059, CAM-060, CAM-061, CAM-062, CAM-084, CAM-086, CAM-104, CAM-132 y CAM-133 en [cambios](../../seguimiento/cambios.md) y sus reportes locales.

## Objetivo y alcance

Dar un siguiente paso válido y oportuno hacia un refugio, priorizando menor exposición futura observable y comparando el resultado real por mordidos antes que evacuados. La búsqueda temporal está integrada con fallback Dijkstra. Fuentes canónicas: [API](../../arquitectura/contratos/api.md), [algoritmos](../../arquitectura/algoritmos.md), [TRD](../../producto/TRD.md). No cambiar método/cuerpo de `/paso` ni usar información oculta.

## Criterios de aceptación

| Criterio | Comportamiento verificable | Pruebas |
|---|---|---|
| CA-002-01 | `/paso` autentica, acepta el cuerpo obligatorio y responde solo con `siguienteNodo` en éxito; inválidos tienen error explícito. | T-08 |
| CA-002-02 | Toda decisión generada es vecino habilitado o espera; considera horda/vecinos, cierres y mordidas conocidas. | T-03, T-05, T-07, T-08 |
| CA-002-03 | Repetir solicitud sobre misma instantánea conserva decisión y ninguna respuesta usa otra partida/turno silenciosamente. | T-10 |
| CA-002-04 | Bajo ráfagas conserva límite contractual y se mide p95/errores desde el cliente, con carga y origen declarados. | T-11 |
| CA-002-05 | Una política mejorada se compara con base en escenarios/semillas declarados; no usa dormidos o aleatoriedad privada ni inventa mejora. | T-04, T-22 |
| CA-002-06 | El planificador prioriza exposición estimada observable antes que distancia/tiempo, usa Dijkstra como respaldo ante salida temporal incompleta, y el evaluador ordena resultados reales por menos mordidos y luego más evacuados. | T-30 |
| CA-002-07 | Para el mismo run, versión de snapshot y sobreviviente, la ruta mostrada por el panel comparte exactamente el siguiente nodo que entrega la decisión automática; el cálculo queda acotado a un snapshot. | T-31 |
| CA-002-08 | El cálculo de riesgo distingue contacto en nodo y cruce opuesto: bloquea los cruces confirmados solo para el turno actual y estima cruces futuros por arista dirigida, sin revelar fase privada ni RNG. | T-32 |
| CA-002-09 | Si no existe una ruta completa a refugio pero hay un vecino libre y legal, el motor propone una salida inmediata priorizando riesgo próximo y luego continuidad topológica; solo espera si no existe salida segura conocida. | T-33 |
| CA-002-10 | Solo un sobreviviente activo puede recibir mordida; una llegada confirmada al refugio permanece terminal en turnos siguientes. | T-34 |
| CA-002-11 | Las rutas de sobrevivientes activos se asignan conjuntamente por snapshot; la exposición prevista precede a congestión y costo, y la ruta mostrada coincide con la acción automática. El resolutor conserva autoridad sobre colisiones y mordidas. | T-35, T-31 |
| CA-002-12 | La política solo suma exposición en turnos cubiertos por el pronóstico; no repite el último turno conocido como si describiera el futuro restante. | T-36 |
| CA-002-13 | El compromiso de ruta automática sobrevive snapshots sucesivos y se recorta con movimiento confirmado; solo se reemplaza ante zombie visible dentro del radio configurado, cierre que invalida el trayecto o desviación. No genera ciclos ni desvíos por congestión sola; consultas antiguas no mutan el compromiso vigente. | T-46 |
| CA-002-14 | Incidentes no aparecen en la ruta; la horda excluye su nodo y todos sus vecinos topológicos incluso junto a calles cerradas; zombies activos bloquean el nodo ocupado y su vecindad añade riesgo blando para elegir una alternativa. Cualquier bloqueo actual sobre un nodo restante invalida el compromiso antes del siguiente paso. Si no hay alternativa, el motor no afirma que esperar o pasar junto a un zombie sea seguro. | T-55 |

## Plan y módulos

P0 fija API/esquemas; P2 entrega una ronda con Dijkstra; P3 añade horizonte limitado y evaluación separada. Núcleo en rutas/dominio, casos de uso en aplicación, HTTP en API y adaptadores. Incluir presupuesto global del turno y alternativa válida ya calculada; espera no equivale a seguridad.

## Casos límite, dudas y verificación

Sin ruta, origen peligroso, refugio inaccesible, timeout, fase incompatible y calles paralelas. P-01/P-05 condicionan unidades y eficiencia; registrar supuestos en vez de atribuirlos al reto. La referencia base puede verificarse parcialmente por tarea; toda la SPEC solo se verifica al completar los criterios, incluida evaluación de mejora.

La implementación inicial de P0-01/P0-02 cubre el proceso FastAPI, esquemas, API key, `/salud`, `/paso` y fixtures. CAM-012 verifica arranque y contrato HTTP. CAM-013 incorpora Dijkstra genérico; CAM-014 integra el caso de uso con snapshots/mapas inyectados y mapea errores 404/409/503. CAM-020 agrega configuración local de cohortes al ensamblaje demo y un cliente de carga concurrente con resumen de latencias/errores sobre snapshot fijo. CAM-028 añade un evaluador HTTP loopback que mantiene snapshot común por turno, resuelve las intenciones recibidas y vuelve a abrir la decisión para el siguiente turno; CAM-029 alinea los inicios a una cadencia monotónica configurable, mide duración/retraso y registra tres turnos por cohorte 20/80/200 con período objetivo de dos segundos. CAM-044 solicita hasta 150 turnos por cohorte; el mundo sintético finaliza a los 12/15/13 turnos, con p95 por solicitud de 18,860/58,097/92,060 ms y cero errores en una pasada local. El reporte confirma el límite de duración, no satisface cinco minutos ni T-11. CAM-033 implementa y mide el núcleo temporal acotado; CAM-034 añade un pronóstico por escenarios observables y supuestos explícitos; CAM-035 compara ambas políticas en mundos sintéticos emparejados de tres turnos. CAM-058 conecta la política temporal a `/paso` y al simulador automático, con Dijkstra como respaldo; introduce el orden real de evaluación mordidos primero y evacuados después. CAM-059 agrega exposición por cruces opuestos futuros, salida inmediata si todas las rutas completas están bloqueadas y reutilización del mismo trayecto para vista previa y decisión del snapshot. CAM-060 hace respetar R-11: solo sobrevivientes activos pueden ser mordidos y la evacuación confirmada es terminal. En una comparación preliminar emparejada (tres semillas, mixto, 20, intensidad alta, incidentes, 12 turnos), la política temporal de CAM-059 tuvo 6 mordidos menos agregados y fue igual o mejor en los tres pares. La muestra es pequeña, local y no cambia la garantía: riesgo estimado no es mordida real ni supervivencia. T-22 ampliada, latencia HTTP/carga y reglas oficiales siguen pendientes; CA-002-04/05 y la SPEC permanecen parciales.

CAM-084 agrega CA-002-13: el snapshot conserva rutas completas automáticas entre turnos y el coordinador guarda el sufijo solo tras resolver el movimiento. Se mantienen hasta amenaza visible dentro del radio topológico configurado, cierre invalidante o desviación; un zombie lejano no fuerza por sí solo el cambio. El radio inicial de tres saltos es provisional. T-46 queda pendiente de automatización/evidencia; esta tarea no verifica cohortes, reducción de mordidas ni cumplimiento integral de la SPEC.

CAM-086 reduce trabajo redundante del pronóstico al agregar zombies con transiciones lineales antes de propagar su masa y cachear el índice inverso de aristas por grafo. Una regresión compara la salida agregada de nodos y cruces con la suma de pronósticos individuales. CAM-104 endurece la vigencia de rutas frente a cualquier nodo peligroso restante, conserva el perímetro topológico completo de hordas junto a cierres y añade preferencia blanda por alejarse de zombies activos próximos. CAM-132 comparte campos estáticos por refugio, crea índices de adyacencia inversa por grafo y reemplaza BFS repetidas de objetivos de corredores por un índice inverso acotado; una regresión compara sus resultados con la búsqueda directa. CAM-133 limita la validación de cada solicitud `/paso` a la versión de mapa y el personaje pedido; las transiciones de snapshot conservan la validación integral. Con 200 habitantes, muestras locales de 3/10/20 turnos dieron p95 216.299/129.513/151.720 ms, sin fallas; la muestra de 20 turnos superó 150 ms y cinco ciclos excedieron 2 s. No se acredita la meta sostenida ni latencia pública. La SPEC permanece parcial y T-11/T-22/T-46 siguen pendientes.
