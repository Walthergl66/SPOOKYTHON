# ADR-020 — Planificación coordinada por snapshot

Fecha: 2026-10-26
Estado: implementada localmente; impacto en mordidas pendiente
Origen: solicitud del usuario de buscar rutas de evacuación priorizando la menor cantidad de personas mordidas.

## Contexto

ADR-018/019 planifican una ruta individual por sobreviviente. En grupos, decisiones equivalentes pueden concentrar los primeros pasos en el mismo nodo. El resolutor conserva la autoridad sobre movimientos, cruces y mordidas; el modelo actual no define capacidad de calles/refugios ni impide que varios sobrevivientes compartan nodo.

## Decisión

`DecidirPaso` prepara una asignación de rutas de todos los sobrevivientes activos para la versión vigente `(runId, snapshot, mapa)`. Panel, simulador automático y solicitudes `/paso` consultan esa misma asignación. Al cambiar el snapshot se descarta el plan y se calcula otro.

La selección ordena primero a quienes tienen mayor exposición observable en su nodo actual. Para cada uno compara alternativas legales de primer paso por exposición acumulada del pronóstico disponible, luego por ocupación ya asignada a ese destino, costo de ruta y desempate estable. Congestión es una penalización suave que solo desempata entre rutas de exposición equivalente; no representa capacidad ni modifica reglas de colisión.

## Alternativas

- Mantener rutas independientes: no reduce concentración en bifurcaciones compartidas.
- Bloquear como ocupado un nodo reservado: descartado porque el dominio no define capacidad o exclusión de sobrevivientes.
- Cambiar el resolutor o reservar capacidad de refugio: fuera de las reglas confirmadas y no adoptado.

## Consecuencias y límites

La recomendación panel/acción sigue determinista para el snapshot y usa únicamente amenazas visibles; no consulta dormidos ni RNG privado. El planificador compara salidas alternativas, evita búsquedas temporales individuales redundantes al asignar una cohorte y cachea solo una versión. La excepción sin ruta completa elige una salida legal por amenaza inmediata/costo, o espera cuando no hay salida. El ensayo de grafo mínimo valida distribución/prioridad, no menos mordidas en mundos completos. La medición interna fría 20/80/200 fue 28,73/34,36/92,52 ms en una semilla; no demuestra latencia HTTP, carga ni ciclo de dos segundos. Se requiere comparación emparejada y medición de extremo a extremo antes de afirmar beneficio o escalabilidad.

Documentos: [SPEC-002](../../metodo/especificaciones/SPEC-002-motor-paso.md), [algoritmos](../algoritmos.md), [pruebas](../../calidad/pruebas.md), CAM-061 y [CAM-062](../../calidad/resultados/horizonte-riesgo-cam062.md), que limita la exposición al pronóstico explícito sin extenderla a pasos no modelados.
