# ADR-011 — Pronóstico visible por escenarios

Fecha: 2026-10-26  
Estado: implementado localmente, exploratorio y no conectado a `/paso`  
Origen: P3-02 de SPEC-002 después de P3-01/CAM-033

## Contexto

El planificador temporal acepta bloqueos y exposición por fase. La fase de movimiento del caminante pertenece al estado aleatorio privado; la ubicación y reglas oficiales de dormidos, corredores y hordas tienen dudas abiertas (P-02/P-03/P-07/P-09). Una predicción no debe filtrar datos privados ni convertir una suposición en garantía.

## Decisión

Introducir valores mínimos `ZombieObservable` y `SobrevivienteObservable` en `routing/prediccion.py`. El pronosticador no acepta `Partida`, entidad `Zombie`, RNG ni fase privada; rechaza explícitamente el tipo dormido.

- Caminante: modelar ambas fases posibles con el mismo peso y ramificar uniformemente por calles salientes habilitadas, según el comportamiento provisional del prototipo.
- Corredor: mantener fijas las ubicaciones públicas de sobrevivientes durante el horizonte y aplicar objetivo más cercano, rango de tres saltos y hasta dos tramos por turno, parámetros actuales provisionales.
- Horda: mantener estático su nodo y vecinos bloqueados, como en el prototipo mientras P-07 siga sin respuesta.
- Agregar ocupación estimada como puntaje acotado de exposición. La salida no es probabilidad calibrada, riesgo sísmico ni supervivencia.

La función devuelve las condiciones compatibles con P3-01 y los supuestos aplicados. Se conserva fuera del endpoint y de las rondas hasta comparar políticas en P3-03. Cierres configurados se conservan para todo el horizonte, en coherencia con el modelo vigente sin reaperturas.

## Alternativas

- Leer fase privada o consumir RNG de la partida: rechazado por la frontera de información y por reproducibilidad del planificador.
- Presentar una trayectoria única como certeza: rechazado porque caminantes tienen resultados aleatorios.
- Eliminar del pronóstico corredores/hordas: rechazado para el prototipo, cuyos comportamientos provisionales actuales pueden modelarse, siempre que sus supuestos viajen con el resultado.
- Integrar de inmediato en `/paso`: rechazado hasta comprobar T-22 y presupuesto de latencia.

## Límites y revisión

Fase uniforme y selección uniforme reproducen supuestos del prototipo, no distribuciones oficiales. Sobrevivientes congelados limitan la validez de objetivos de corredor. Horda fija puede dejar de representar el mundo si P-07 define movimiento. Estas limitaciones requieren calibración y evaluación con semillas independientes antes de P3-03. Dormidos continúan fuera de cualquier pronóstico.

## Evidencia

CAM-034; cinco pruebas en `tests/test_prediccion_rutas.py`. No acredita T-22, CA-002-05, supervivencia ni latencia de `/paso`.
