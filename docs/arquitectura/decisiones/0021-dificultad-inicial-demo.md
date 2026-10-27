# ADR-021 — Dificultad inicial equilibrada para la demo

Fecha: 2026-10-26  
Estado: aceptada para la demo local  
Origen: reporte del usuario de bajo total evacuado; CAM-063 aporta comparación exploratoria de intensidad.

## Contexto

La pantalla iniciaba cada demo en intensidad alta (25 % de nodos elegibles con amenazas) con incidentes viales activos. El escenario `mixto` de 20 habitantes produjo pocas evacuaciones en pruebas locales. Las intensidades baja/media/alta siguen disponibles; el cambio se limita a la selección inicial y defaults cuando la petición omite intensidad. La configuración de incidentes que se menciona en la decisión original fue sustituida por ADR-032.

## Decisión

La interfaz, el esquema HTTP local y `ControlSimuladorDemoLocal` usan intensidad `media` (14 %) por defecto. Los incidentes viales permanecen activados siempre; la persona operadora puede ajustar escenario, población e intensidad antes de iniciar. No se modifica la distribución aleatoria, el generador ni las reglas de resolución.

## Alternativas

- Mantener alta: descartada como valor inicial porque con las mismas tres semillas e incidentes produjo muchas menos evacuaciones y más mordidas que media.
- Usar baja: descartada como valor inicial porque reduce mucho la presión y puede ocultar el comportamiento de rutas frente a amenazas.
- Desactivar incidentes: se permitía en la decisión original y fue descartado posteriormente para el tablero local por ADR-032; herramientas directas de evaluación mantienen configuración explícita.

## Evidencia y límites

En tres pares sintéticos (semillas 101/202/303, escenario mixto, 20 habitantes, eventos activados, hasta 30 turnos), media obtuvo 29 evacuados/27 mordidos/4 activos y alta 13/45/2. Muestra local pequeña, sin valor estadístico ni generalización a otros escenarios o semillas. No mide seguridad real ni define densidad de amenazas oficial. Ver [CAM-063](../../calidad/resultados/default-media-cam063.md).

Documentos: [ADR-017](0017-perfiles-sinteticos-de-amenazas.md), [SPEC-007](../../metodo/especificaciones/SPEC-007-panel-operador-local.md), [pruebas](../../calidad/pruebas.md), CAM-063.
