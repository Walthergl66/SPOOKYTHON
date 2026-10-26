# Continuidad entre agentes y colaboradores

Objetivo: retomar trabajo sin depender del historial del chat. Protocolo obligatorio definido también en [AGENTS.md](../AGENTS.md).

## Al comenzar una tarea

1. Leer índice, contexto, estado actual, cambios, pendientes y este protocolo.
2. Inventariar todos los `.md` bajo `doc/` y revisarlos antes de modificar. Leer históricos como antecedentes; usar documentos propietarios vigentes como fuente de implementación.
3. Inspeccionar archivos y cambios reales; comprobar qué existe antes de usar comandos o afirmar avances.
4. Identificar tarea, requisitos, módulos, contratos afectados y evidencia necesaria. Si hay diferencias, registrarlas y resolver con instrucciones actuales del usuario, fuente del reto y código comprobado.
5. Empezar por la siguiente acción concreta; no repetir trabajo verificado ni ampliar alcance porque parezca interesante.
6. Identificar requisitos del [PRD](PRD.md)/[TRD](TRD.md), modelo [ODDD](ODDD.md) y [SPEC](especificaciones/README.md) de la tarea; seguir el ciclo de [SDD](SDD.md). Para tareas triviales usar su variante reducida.

## Durante el trabajo

- Mantener cada decisión en su documento propietario; enlazar desde otros lugares para evitar copias divergentes.
- Ante un cambio duradero de arquitectura, contrato, regla o alcance, crear ADR con alternativas y consecuencias.
- Registrar dudas con ID en `pendientes.md`, sin presentar supuestos como hechos.
- Comentar invariantes y motivos en código cercano a la lógica; documentar el contexto duradero aquí. No transcribir deliberación interna ni secretos.
- No afirmar pruebas, despliegues o costos sin ejecución/evidencia. Diferenciar previsto, implementado y verificado.

## Al cerrar o interrumpir

1. Actualizar documentos propietarios del comportamiento cambiado.
2. Añadir entrada a [cambios](cambios.md) con ID, motivo, archivos, decisiones, verificación y pendientes.
3. Actualizar [estado actual](estado-actual.md): qué existe, trabajo incompleto, comandos reales y siguiente paso exacto.
4. Actualizar estados del [plan](plan-implementacion.md) solo si sus criterios se cumplieron.
5. Ejecutar `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py` y las pruebas pertinentes al cambio. Si no se pudieron ejecutar, registrar la causa concreta.
6. Responder con resultado, validación y límites materiales. No cerrar con un supuesto «todo listo» si faltan tareas autorizadas necesarias.

Un ajuste de redacción puede agruparse en una entrada de cambio; no crear un ADR por una errata. Un cambio de reglas/contrato sí necesita razonamiento trazable. No es necesario actualizar el contexto si el propósito sigue igual; sí hacerlo cuando cambia el alcance.

Actualizar criterios de la SPEC y vínculos en trazabilidad al cambiar comportamiento. Completar una tarea no convierte automáticamente toda la SPEC en verificada. Conservar autorización vigente y no usar SDD para añadir aprobaciones repetidas o funcionalidades no solicitadas.

## Transferencia mínima

Usar [plantilla de transferencia](plantillas/transferencia.md) para resumir estado en `estado-actual.md`. Debe decir dónde continuar y qué falta, incluso si el agente fue interrumpido antes de ejecutar pruebas. Una transferencia no borra el historial: `estado-actual.md` es resumen vigente, `cambios.md` conserva entradas anteriores y ADR conserva decisiones.

## Cambio del usuario durante una tarea

Incorporarlo al alcance vigente y registrar el motivo del ajuste. Un pedido de estado o «continúa» no cancela la tarea anterior. No cambiar de tecnología, modo o arquitectura por falta de contexto: revisar primero lo documentado y avanzar dentro del alcance ya autorizado.
