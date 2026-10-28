# ODDD — Orientación a objetos y diseño guiado por dominio

Versión: 1. Fecha: 2026-10-26. Interpretación confirmada por el usuario: OO + DDD. Es la denominación local de este enfoque; no se afirma que ODDD sea una sigla universal. Estado: modelo de diseño implementado parcialmente en `backend/src/navira/domain/`; reglas de simulación aún pendientes.

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
| Perfil narrativo | Valor ficticio inmutable usado solo por presentación; no participa en reglas, planificación ni identidad de personas reales. |

## Límites lógicos

| Contexto | Responsabilidad | Integración |
|---|---|---|
| Mundo y simulación | Grafo, zombies, eventos y resolución | Publica observación y resultado. |
| Planificación | Elegir paso/refugio y estimar riesgo | Consume observación, devuelve intención. |
| Participación humana | Propiedad, aparición y órdenes | Entrega intención al mismo resolutor. |
| Operación interactiva | Valida inserción de entidades/refugios y cierres sobre una partida automática viva | Persiste una nueva versión completa por el puerto CAS; la UI no es autoridad. |
| Observación/evaluación | Panel, métricas y reportes | Consume resultados; no modifica posiciones. |

Son límites dentro de un monolito modular, no servicios nuevos. Las identidades compartidas son valores simples; no se pasa un objeto mutable del mundo al planificador o al navegador.

## Entidades, valores y autoridad

- Entidades con identidad: Partida, Zombie, Sobreviviente, Refugio y Orden humana.
- Valor de aplicación: `SesionJugador` vincula un token opaco verificado a una partida y un sobreviviente; no se envía la sesión como entidad mutable al frontend.
- Valores inmutables propuestos: NodeId, RunId, TurnNumber, SnapshotVersion, distancia en metros, velocidad y segmento dirigido. Validar unidades y valores antes de entrar al núcleo.
- `PerfilNarrativo` es un valor opcional de `Sobreviviente`. La fábrica de demo lo asigna una vez al crear el run; la selección usa un flujo pseudoaleatorio derivado aparte de la semilla del mundo. Incorporaciones posteriores eligen un perfil libre; el panel recibe solo los campos narrativos necesarios. Nunca alimentar este valor a movimiento, rutas o resolución.
- Partida es la frontera lógica de consistencia del turno; el coordinador autoriza transiciones. No obliga a cargar/guardar todo el mundo como un único item de base de datos.
- Registro de órdenes es otra frontera de concurrencia: cada reemplazo tiene secuencia y versión; solo la sesión propietaria puede solicitarlo.
- Intervención de operador no crea un agregado de mundo paralelo: modifica `Partida`/`SnapshotMundo` inmutables usando el grafo versionado y una escritura CAS. Reto queda fuera de este caso de uso.
- Servicios de dominio puros: transitabilidad, detector de mordidas, resolución y elegibilidad de aparición. Usar una función si no necesita estado o identidad.
- Políticas intercambiables: controlador automático y humano producen intenciones. Tipos zombie pueden usar composición/estrategias; no se exige una clase hija por tipo.

El código implementa `Partida`, `Sobreviviente`, `Zombie` e `IntencionMovimiento` como valores inmutables. `validar_contexto_intencion()` comprueba partida, turno, fase, personaje y estado activo. `SnapshotMundo` y el coordinador de aplicación producen transiciones completas versionadas en memoria; la escritura atómica y el control de concurrencia entre procesos requieren un adaptador persistente futuro.

## Invariantes

1. Un `runId` no cambia de modo y un turno no se aplica dos veces. El control local mantiene un solo run; una acción explícita de inicio en otro modo crea otro `runId` y sustituye el anterior, nunca migra su estado.
2. Una intención pertenece a partida, personaje, turno y fase compatibles.
3. Un destino topológico es vecino habilitado o el propio nodo; la mordida se resuelve aparte.
4. Solo un coordinador modifica posiciones; aceptar orden no las cambia.
5. La horda, cruces, dormidos y refugios siguen [reglas](reglas-juego.md), incluidos sus supuestos explícitos.
6. Ningún consumidor observable recibe datos privados por compartir tipos o referencias mutables.
7. La aleatoriedad pertenece al estado privado versionado de la partida; nunca se consulta desde planificadores o proyecciones.
8. Repetir una decisión HTTP para la misma instantánea conserva su respuesta, aunque la trayectoria del mundo cambie en turnos posteriores.
9. Para mapas Manta, el grafo de la partida es una proyección acotada: ninguna intención, aparición o ruta puede referir un nodo exterior; el recorte es inmutable y el mapa fuente permanece separado.
10. Un compromiso de ruta automática es parte del snapshot versionado y solo avanza con el movimiento confirmado por CAS. El panel no lo modifica; el sistema lo reemplaza por amenaza visible cercana o si cualquier nodo restante queda bloqueado por horda/zombie o pierde transitabilidad por cierre.

## Casos de uso, repositorios y eventos

`IniciarPartida`, `PrepararTurno`, `DecidirPaso`, `RegistrarOrdenHumana`, `ResolverTurno` y `ConsultarPanel` son responsabilidades de aplicación. Algunos casos existen como servicios/clases y otros como funciones coordinadas; la lista no exige un archivo por cada nombre. La aplicación define puertos para estados, órdenes, reloj y publicación; adaptadores de memoria/DynamoDB/HTTP se ubican fuera del dominio.

`RegistrarOrdenHumana` ya valida propiedad/contexto topológico y utiliza el puerto `RepositorioOrdenes`; `RepositorioOrdenesMemoria` serializa clave idempotente y reemplazo en el adaptador local. El caso de uso devuelve un acuse, no mueve el mundo. El coordinador aún no consume ese puerto: antes de integrar debe cerrar atómicamente el turno respecto de nuevas órdenes y resolverlas como `IntencionMovimiento` mediante el mismo resolutor.

Los hechos internos «turno resuelto» y «sobreviviente evacuado» pueden proyectarse a [eventos de transporte](../arquitectura/contratos/eventos.md). Un evento de dominio no es automáticamente un mensaje público. No se introduce event sourcing ni obligación de reconstruir toda la base desde un bus.

## Verificación

Probar invariantes con grafos pequeños, reloj controlado y adaptadores en memoria, antes de probar AWS. Reutilizar T-01 a T-18, especialmente paridad T-17 e idempotencia T-18. Cambiar modelo actualiza [datos](datos.md), [módulos backend](../arquitectura/modulos/backend.md), especificaciones y ADR cuando corresponda.
