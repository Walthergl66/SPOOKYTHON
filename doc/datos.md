# Modelo de datos y consistencia

Estado: modelo lógico previsto; esquema físico pendiente de implementación y medición. Decisión: [ADR-003](decisiones/0003-estado-y-turnos.md).

Lenguaje común y límites de consistencia: [ODDD](ODDD.md). Este archivo conserva la fuente de campos/versiones; ODDD enlaza el modelo sin imponer otra base de datos o un item único para toda la partida.

| Entidad | Campos esenciales | Invariantes |
|---|---|---|
| Nodo | ID, latitud, longitud | ID único, coordenadas válidas. |
| Calle/segmento | ID físico, origen/destino, distancia, tipo, velocidad, dirección | Costo positivo; cruces reconocen el mismo segmento. |
| Refugio | ID, nodo; capacidad solo si se activa extra | Nodo existente. |
| Partida | `runId`, modo, escenario, versiones, semilla privada, estado | Un modo fijo y una partida activa. |
| Zombie | ID, tipo, nodo, fase, activación | Dormido oculto en proyección. |
| Sobreviviente | ID, nodo, control, estado, refugio objetivo | Control humano/automático; activo/mordido/evacuado. |
| Orden humana | Partida, turno, personaje, acción, secuencia, destino | Propiedad, idempotencia y cierre. |
| Snapshot | Partida, turno, fase, versión, datos | Inmutable una vez confirmado. |
| Evento de ciudad | ID, segmento, turno objetivo, causa | Aplicación única y trazable. |
| Resultado | Modo, versiones, decisiones, métricas y final | Separar pruebas automáticas de juego. |

## Estado real y observable

**Real privado:** todos los zombies, activaciones, generador aleatorio, estados de control y datos necesarios para recuperar. **Observable:** zombies visibles, trayectorias permitidas, sobrevivientes, bloqueos y datos públicos de refugios. Credenciales y estado aleatorio no pertenecen a ninguna respuesta de panel o recomendación.

El motor recibe información de todos los sobrevivientes necesaria para estimar persecución, pero nunca la información oculta. La selección inicial evita solapamiento con zombies usando validación privada del simulador; no explica al jugador la ubicación de dormidos excluidos.

## Versiones

Identidad mínima de una instantánea: `(runId, turno, fase, mapVersion)`. Mantener separados `zombies_movidos` y `resuelto`, no sobrescribir una fase bajo una misma clave. Decisiones incorporan esa identidad y sobreviviente/nodo actual. Un reinicio de partida genera nuevo `runId` aunque el turno vuelva a cero.

DynamoDB será la fuente de verdad prevista. Preparar una versión completa y confirmar un manifiesto/puntero de publicación; los consumidores no leen fragmentos a medio escribir. La lectura inmediata que depende de una escritura confirmada debe ser consistente en la tabla, no depender de un índice eventualmente actualizado.

Antes de fijar formato físico: medir tamaño de snapshots, límites vigentes del servicio y unidades facturables. Si un snapshot requiere fragmentos, publicar solo al confirmar el conjunto; no asumir que un item puede crecer sin límite. Definir retención y exportación; no borrar evidencia de evaluación mediante expiración prematura.

## Recuperación y reproducción

- Un solo escritor del mundo; proteger fase/turno esperado con condiciones de versión.
- Persistir orden aceptada antes del acuse y marcar aplicación para evitar dobles movimientos.
- Guardar configuración, versión de código/mapa, eventos, decisiones y estado aleatorio privado suficiente para reconstrucción.
- La semilla sola no reproduce decisiones humanas; también conservar su secuencia.
- Una semilla igual no garantiza idénticos zombies en políticas distintas si cambia el objetivo perseguido. Comparar escenarios con esa limitación explícita.
- Si recuperación segura no está implementada/verificada, reportarlo como limitación e interrumpir explícitamente tras un fallo.
