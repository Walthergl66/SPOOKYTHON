# ADR-043 — Aplicar bloqueos y riesgo próximo a todas las rutas

- Estado: aceptada e implementada localmente; evaluación conductual amplia pendiente.
- Fecha: 2026-10-27.
- Origen: el usuario observó que el modo Juego no parecía respetar las reglas del Simulador y pidió evitar rutas por incidentes, hordas, vecinos de hordas y zonas próximas a zombies.
- Requisitos: PRD-03, PRD-06, PRD-10, TRD-12, TRD-14, TRD-18.
- Especificaciones: [SPEC-002](../../metodo/especificaciones/SPEC-002-motor-paso.md), [SPEC-010](../../metodo/especificaciones/SPEC-010-juego-operador.md).

## Contexto

Juego operador ejecuta un mundo `simulador` y comparte `DecidirPaso` con Simulador y Reto. Se detectó que un compromiso solo se revisaba contra su siguiente nodo, aunque una horda o zombie visible hubiese bloqueado un nodo posterior del trayecto. También se construía el perímetro de horda desde calles abiertas, de modo que un incidente podía sacar un nodo de su vecindad. R-06 define el perímetro por vecindad topológica, y R-08 mantiene los incidentes como cierres de segmentos.

La proximidad a caminantes/corredores no constituye por sí misma una mordida: el resolutor aplica mordidas por coincidencia de nodo o cruce opuesto. Sin embargo, la solicitud del usuario pide preferir rutas que pasen más lejos de los zombies.

## Decisión

1. Tratar cada segmento cerrado por incidente como no transitable durante la planificación y validar todo tramo de una ruta comprometida contra los cierres vigentes.
2. Bloquear el nodo de una horda y todos sus vecinos topológicos entrantes/salientes aunque el segmento que conecta esté cerrado temporalmente.
3. Invalidar un compromiso si cualquier nodo restante está ocupado o bloqueado por una amenaza visible, antes de servir el siguiente paso.
4. Bloquear el nodo ocupado por zombies activos; sumar exposición blanda de factor inicial `0.4` a los nodos conectados a un caminante/corredor activo. La búsqueda temporal prefiere desviar a un camino con menor exposición, pero mantiene una alternativa válida si no existe otro trayecto. No declarar la vecindad como mordida ni como bloqueo legal.
5. Mantener el filtro en el planificador compartido. No añadir una ruta o resolutor propio para Juego.

## Alternativas consideradas

- Bloquear legalmente todos los vecinos de cualquier zombie: se descarta porque la regla de mordida no establece ese radio y podría cortar calles sin salida alternativa.
- Ignorar la vecindad zombie: se descarta porque contradice la petición de preferir rutas que rodeen amenazas cercanas.
- Recalcular solamente al alcanzar el siguiente nodo peligroso: se descarta porque deja compromisos visuales/automáticos que atraviesan peligros ya conocidos en el snapshot.
- Conservar el perímetro de horda dependiente de vías abiertas: se descarta porque cambia la vecindad topológica según incidentes y contradice R-06.

## Consecuencias y límites

- Simulador, Juego operador y Reto mantienen una sola política automática.
- La exposición vecinal es una puntuación para ordenar rutas; factor 0.4 no es probabilidad calibrada ni garantía de menos mordidas.
- Si cierres, hordas y amenazas cortan todas las rutas, el motor no puede garantizar llegada o seguridad; esperar o la ruta de escape se resuelve según los riesgos observables restantes.
- La prueba unitaria sobre grafos pequeños valida el criterio, pero faltan evaluación de mordidas por varias semillas en Manta y evidencia de carga/rendimiento.

## Evidencia

CAM-104 agrega regresiones para horda junto a calles cerradas, amenaza en tramo posterior de compromiso y desvío alrededor de zombies con alternativa. Ver [T-55](../../calidad/pruebas.md) y [CAM-104](../../seguimiento/cambios.md#cam-104-rutas-seguras-ante-incidentes-hordas-y-zombies).
