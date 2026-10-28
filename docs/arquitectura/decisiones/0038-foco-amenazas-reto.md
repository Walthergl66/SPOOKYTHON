# ADR-038 — Concentrar amenazas del Reto en el núcleo urbano

- Estado: aceptada para implementación local.
- Fecha: 2026-10-27.
- Contexto: las rondas Reto mostraban amenazas e incidentes repartidos por la ventana jugable y dejaban vacía el área urbana central. El usuario pidió acercar zombies, hordas e incidentes al centro para que el mapa presente una amenaza más legible.
- Decisión: únicamente en los presets Reto sobre el fixture Manta, ubicar al menos `round(cantidad_por_tipo × 0,8)` de cada tipo zombie dentro de un radio de 3.500 m alrededor del punto aproximado de Parque La Dolorosa/R-03 (`-0.9522745219919659, -80.72726572846808`). Seleccionar el resto aleatoriamente fuera del foco cuando haya nodos. Para R2/R3, preferir puentes/calles cuyo centro geométrico quede dentro del mismo radio; usar candidatos de toda la ventana solo como fallback si faltan segmentos locales. Mantener conteo, composición, eventos y turnos provisionales actuales. La misma semilla reproduce el mundo.
- Alternativas: concentrar todos los zombies en un único sector (reduce variedad y cobertura); cambiar globalmente los generadores de demo (alteraría el simulador libre); aumentar el conteo de amenazas (el usuario pidió distribución central y los conteos del reto siguen sin confirmación).
- Consecuencias: cada tipo, incluidas las hordas, tiene una cuota explícita en el centro y una fracción permanece fuera para conservar cobertura. La distribución espacial no constituye un modelo epidemiológico ni de amenaza real. La ronda libre mantiene exactamente su selección global anterior.
- Supuestos y actualización: el punto R-03 es una referencia urbana aproximada, no un centro geométrico/administrativo certificado. Radio y cuota son parámetros provisionales; revisar si el reto publica densidades o polígonos oficiales. P-09/P-15 siguen abiertos.
- Verificación: T-47/CAM-095 comprueba la cuota por tipo, eventos centrados, replay y Simulador libre sin foco.
- Referencias: [SPEC-009](../../metodo/especificaciones/SPEC-009-modo-reto.md), [mapa Manta](../../dominio/mapa-manta.md), [pendientes](../../seguimiento/pendientes.md).
