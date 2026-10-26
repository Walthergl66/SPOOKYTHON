# ADR-008 — Simulación estocástica con reproducción auditable

Fecha: 2026-10-26  
Estado: aceptada como requisito y diseño  
Origen: aclaración explícita del usuario: el simulador debe ser aleatorio y pequeños cambios pueden alterar rutas, hordas y evolución posterior.

## Contexto

El reto exige elecciones aleatorias para caminantes y resultados dinámicos; también exige poder comparar rondas. El estado de partida ya guarda una copia privada del estado de `random.Random`, pero el demo usa semilla predeterminada fija, fija las posiciones de zombies por perfil, deja las hordas estáticas y dirige corredores a objetivos/desempates deterministas. La aleatoriedad existente es parcial.

## Decisión

El mundo de cada partida debe ser estocástico: una partida nueva sin semilla indicada obtiene una semilla nueva; el generador privado controla posiciones/estados iniciales y las elecciones que las reglas dejan al azar, además de los eventos aleatorios configurados. Un cambio de semilla, composición, posición, evento u orden puede propagarse y alterar encuentros, rutas y resultados posteriores.

Una ejecución se reproduce dentro de la misma versión de reglas si se conserva semilla, estado del generador, versiones de código/mapa, configuración, eventos y órdenes/intenciones externas. No se garantiza reproducción entre versiones que cambien consumo u orden de aleatoriedad. Cada turno conserva el estado RNG en el snapshot confirmado para recuperar desde fase intermedia.

La aleatoriedad nunca se expone al planificador, panel, radio o jugador como conocimiento del futuro. El motor debe responder igual a solicitudes repetidas para una misma instantánea; el mundo nuevo puede producir otra instantánea y, con ella, otra recomendación. La ruta de evaluación debe ser eficiente y basada en el estado observable, no elegida al azar sin criterio.

La aleatoriedad está limitada por las reglas: el corredor persigue; la horda bloquea nodo y vecinos; su movimiento se configura solo después de cerrar P-07. No inventar cantidad/distribución oficial de zombies (P-09). Los perfiles probabilísticos de desarrollo se identifican como sintéticos y mantienen parámetros explícitos.

## Alternativas y consecuencias

- Usar una semilla fija siempre: rechazado para ejecución ordinaria porque repite exactamente el mismo caso y oculta variación.
- Aleatoriedad no reproducible ni registrada: rechazada porque impediría depurar y comparar.
- Reproducibilidad total entre cambios de código: no prometida; preservar entrada/semilla/estado dentro de una versión estable y versionar cambios de algoritmo.
- Sortear la decisión de ruta sin considerar eficiencia: rechazado; aleatoriedad del mundo y calidad de planificación tienen objetivos distintos.

Las diferencias iniciales pueden provocar cascadas no lineales; no hay garantía matemática de que cada perturbación cambie el resultado final. Un cambio de comportamiento puede desplazar el flujo aleatorio y cambiar decisiones posteriores.

## Consecuencias y pendientes

P1-05 debe generar partidas y movimiento con variación controlada, semillas no fijas por defecto, estado privado y replay. P-15 define distribuciones antes de fijar escenarios oficiales; P-07 gobierna movimiento de hordas. T-24 comprobará reproducción y divergencia estocástica. T-10 mantiene idempotencia de una decisión HTTP sobre la misma instantánea.

Documentos propietarios: [PRD](../PRD.md), [TRD-11](../TRD.md), [ODDD](../ODDD.md), [reglas](../reglas-juego.md), [algoritmos](../algoritmos.md), [datos](../datos.md), [pruebas](../pruebas.md), [SPEC-001](../especificaciones/SPEC-001-mundo-simulacion.md) y [plan](../plan-implementacion.md).

Evidencia del estado antes de implementación: `src/navira/demo.py`, `src/navira/simulation/resolver.py`, `src/navira/simulation/coordinador.py` y pruebas actuales revisadas en CAM-022. No declara completado el comportamiento objetivo.
