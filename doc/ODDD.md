# ODDD — Orientación a objetos y diseño guiado por dominio

Versión: 1. Fecha: 2026-10-26. Interpretación confirmada por el usuario: OO + DDD. Es la denominación local de este enfoque; no se afirma que ODDD sea una sigla universal. Estado: modelo de diseño implementado parcialmente en `src/navira/domain/`; reglas de simulación aún pendientes.

## Propósito y lenguaje común

Representar reglas de Navira con conceptos del juego, independientes de FastAPI y DynamoDB. Referencia conceptual: [DDD Reference de Eric Evans](https://www.domainlanguage.com/ddd/reference/). La aplicación concreta de este documento es una decisión del proyecto.

| Término | Significado e identidad |
|---|---|
| Partida | Ejecución con `runId`, modo fijo, versión y ciclo de vida. |
| Turno | Intervalo autoritativo; su fase forma parte de la identidad temporal. |
| Nodo | Intersección identificada, con coordenadas; no una posición libre de personaje. |
| Segmento | Calle física; puede tener sentidos dirigidos y un cierre común. |
| Intención | Próximo destino propuesto; no confirma que se haya ejecutado. |
| Movimiento resuelto | Resultado de validar y aplicar una intención en su fase. |
| Observación | Proyección permitida del estado; no el mundo privado completo. |
| Evacuado | Sobreviviente cuya llegada válida fue confirmada. |
| Reserva | Cupo provisional solo si se implementa el extra de capacidad. |

## Límites lógicos

| Contexto | Responsabilidad | Integración |
|---|---|---|
| Mundo y simulación | Grafo, zombies, eventos y resolución | Publica observación y resultado. |
| Planificación | Elegir paso/refugio y estimar riesgo | Consume observación, devuelve intención. |
| Participación humana | Propiedad, aparición y órdenes | Entrega intención al mismo resolutor. |
| Observación/evaluación | Panel, métricas y reportes | Consume resultados; no modifica posiciones. |

Son límites dentro de un monolito modular, no servicios nuevos. Las identidades compartidas son valores simples; no se pasa un objeto mutable del mundo al planificador o al navegador.

## Entidades, valores y autoridad

- Entidades con identidad: Partida, Zombie, Sobreviviente, Refugio y Orden humana.
- Valor de aplicación: `SesionJugador` vincula un token opaco verificado a una partida y un sobreviviente; no se envía la sesión como entidad mutable al frontend.
- Valores inmutables propuestos: NodeId, RunId, TurnNumber, SnapshotVersion, distancia en metros, velocidad y segmento dirigido. Validar unidades y valores antes de entrar al núcleo.
- Partida es la frontera lógica de consistencia del turno; el coordinador autoriza transiciones. No obliga a cargar/guardar todo el mundo como un único item de base de datos.
- Registro de órdenes es otra frontera de concurrencia: cada reemplazo tiene secuencia y versión; solo la sesión propietaria puede solicitarlo.
- Servicios de dominio puros: transitabilidad, detector de mordidas, resolución y elegibilidad de aparición. Usar una función si no necesita estado o identidad.
- Políticas intercambiables: controlador automático y humano producen intenciones. Tipos zombie pueden usar composición/estrategias; no se exige una clase hija por tipo.

El código implementa `Partida`, `Sobreviviente`, `Zombie` e `IntencionMovimiento` como valores inmutables. `validar_contexto_intencion()` comprueba partida, turno, fase, personaje y estado activo. `SnapshotMundo` y el coordinador de aplicación producen transiciones completas versionadas en memoria; la escritura atómica y el control de concurrencia entre procesos requieren un adaptador persistente futuro.

## Invariantes

1. Un `runId` no cambia de modo; un turno no se aplica dos veces.
2. Una intención pertenece a partida, personaje, turno y fase compatibles.
3. Un destino topológico es vecino habilitado o el propio nodo; la mordida se resuelve aparte.
4. Solo un coordinador modifica posiciones; aceptar orden no las cambia.
5. La horda, cruces, dormidos y refugios siguen [reglas](reglas-juego.md), incluidos sus supuestos explícitos.
6. Ningún consumidor observable recibe datos privados por compartir tipos o referencias mutables.
7. La aleatoriedad pertenece al estado privado versionado de la partida; nunca se consulta desde planificadores o proyecciones.
8. Repetir una decisión HTTP para la misma instantánea conserva su respuesta, aunque la trayectoria del mundo cambie en turnos posteriores.

## Casos de uso, repositorios y eventos

`IniciarPartida`, `PrepararTurno`, `DecidirPaso`, `RegistrarOrden`, `ResolverTurno` y `ConsultarPanel` pertenecen a aplicación. La aplicación define puertos para estados, órdenes, reloj y publicación; DynamoDB/HTTP los implementan fuera del núcleo. Nombres orientativos, no archivos que ya existan.

Los hechos internos «turno resuelto» y «sobreviviente evacuado» pueden proyectarse a [eventos de transporte](contratos/eventos.md). Un evento de dominio no es automáticamente un mensaje público. No se introduce event sourcing ni obligación de reconstruir toda la base desde un bus.

## Verificación

Probar invariantes con grafos pequeños, reloj controlado y adaptadores en memoria, antes de probar AWS. Reutilizar T-01 a T-18, especialmente paridad T-17 e idempotencia T-18. Cambiar modelo actualiza [datos](datos.md), [módulos backend](modulos/backend.md), especificaciones y ADR cuando corresponda.
