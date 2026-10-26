# ADR-010 — Búsqueda temporal acotada para rutas

Fecha: 2026-10-26  
Estado: implementada localmente como núcleo experimental; no integrada en `/paso`  
Origen: P3-01 de SPEC-002 para explorar espera/avance con horizonte y presupuesto finitos  

## Contexto y restricciones

Dijkstra existente usa peligros confirmados del snapshot actual y sirve como referencia estable. La planificación temporal requiere representar estados por turno, permitir espera y recibir pronósticos de peligros sin leer dormidos, estado aleatorio privado o información futura exacta. Los parámetros oficiales de zombies y la dinámica de hordas siguen sin confirmarse (P-07/P-09).

## Decisión

Implementar un buscador experimental de grafo expandido `(nodo, turnos)`. El primer paso usa bloqueos/cierres observables del snapshot actual; los pasos posteriores reciben condiciones futuras inyectadas. Esperar es una acción explícita. Las condiciones agregan cierres porque la regla vigente no reabre calles. La prioridad es lexicográfica: exposición acumulada estimada, turnos hasta refugio, costo ponderado en metros y secuencia estable de acciones. Exposición por nodo/fase se acepta entre 0 y 1; su suma es un puntaje acumulado, no probabilidad/calibración de supervivencia.

Valores iniciales locales: horizonte seis turnos (configurable de 1 a 12), máximo 20.000 expansiones y presupuesto de 25 ms por invocación. Un resultado con límite agotado no publica ruta parcial. El integrador debe conservar una ruta base por separado. P3-01 no cambia `/paso`; P3-02 debe generar pronósticos observables y P3-03 decidir, mediante comparación, si la política llega a integrarse.

## Alternativas consideradas

- Adivinar futuras posiciones usando la semilla/RNG: rechazado porque filtraría estado privado y produciría certeza falsa.
- Inmovilizar todos los nodos que cualquier zombie podría alcanzar: rechazado porque bloquearía el mapa conservadoramente sin distinguir riesgo/tiempo.
- Sustituir Dijkstra de inmediato: rechazado hasta comparar reproducibilidad, calidad y presupuesto en escenarios/semillas.
- Usar una única suma de metros, turnos y probabilidad: rechazado porque mezcla magnitudes sin una calibración oficial.

## Consecuencias, límites y costos

- El buscador es determinista para grafo, entrada, perfil y pronósticos idénticos; no consume aleatoriedad.
- El objetivo lexicográfico puede elegir una ruta más larga o esperar para reducir exposición; la métrica aún no es probabilidad real.
- Horizonte corto puede devolver `sin_ruta_en_horizonte` aunque haya una ruta más larga. El agotamiento de presupuesto descarta el parcial.
- Una medición local de fixture no demuestra el tiempo global de turno, p95 HTTP, calidad predictiva o mejora de supervivencia.
- No se invoca desde `/paso` ni desde el panel hasta completar pronósticos, baseline y criterios de selección.

## Supuestos y pendientes relacionados

Las dinámicas futuras de caminantes, corredores, horda y eventos necesitan P-02/P-03/P-07/P-09 y P3-02. Aceptar parámetros en la API no los convierte en reglas oficiales.

## Documentos y módulos propietarios afectados

`src/navira/routing/temporal.py`, `tests/test_ruta_temporal.py`, [algoritmos](../algoritmos.md), [SPEC-002](../especificaciones/SPEC-002-motor-paso.md) y el [reporte exploratorio](../resultados/busqueda-temporal-cam033.md).

## Evidencia de implementación/verificación

CAM-033: ocho pruebas de camino, espera, cierres, condiciones futuras, horizonte y límites; medición local de cohortes sintéticas 20/80/200 en el fixture Manta. No acredita T-22 ni CA-002-05.
