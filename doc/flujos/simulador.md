# Flujo del simulador y del turno

Estado: `resolver_turno()` y `avanzar_turno()` implementan en memoria movimiento zombie, cierres programados, decisiones y resolución conjunta con snapshots versionados. `VentanaTurno` calcula plazos monotónicos absolutos. No existe todavía bucle continuo, espera activa, almacenamiento condicional ni publicación de transporte. Fuente de reglas: [reglas](../reglas-juego.md). Identidades: [datos](../datos.md).

## Ciclo

```mermaid
flowchart TD
    Start[Partida habilitada y grafo validado] --> Tick[Inicio del turno: reloj monotónico]
    Tick --> Events[Aplicar eventos y activaciones]
    Events --> Zombies[Mover zombies y registrar tramos]
    Zombies --> Snapshot[Persistir y preparar estado observable]
    Snapshot --> Auto[Consultar /paso por cada automático activo]
    Snapshot --> Human[En juego: recibir orden humana hasta cierre]
    Auto --> Resolve[Cerrar decisiones y validar conjuntamente]
    Human --> Resolve
    Resolve --> Bites[Resolver mordidas y llegadas]
    Bites --> Save[Persistir resultado y publicar]
    Save --> End{¿Partida terminada?}
    End -->|No| Tick
    End -->|Sí| Report[Exportar reporte y cerrar]
```

`preparar_turno_versionado()` aplica cierres y mueve zombies una vez, devolviendo el snapshot completo de decisiones con la versión esperada. En simulador, `avanzar_turno()` puede completar ambas fases en memoria; en juego, el futuro caso de uso debe persistir/publicar decisiones, recoger órdenes y después llamar a `resolver_turno_versionado()` sin volver a mover zombies. Ese caso de uso y su transporte aún no están conectados.

En modo simulador no hay ventana humana. Cada solicitud tiene menos de 500 ms desde su envío. Se preparan datos antes de enviar y se solicitan decisiones concurrentemente. Repeticiones de red no deben cambiar decisiones ni aplicar movimientos dos veces.

En juego, zombies se mueven al inicio; después se aceptan acciones sobre esa instantánea. Cierre humano provisional: 1,7 segundos desde el inicio, reservando 300 ms para resolver/publicar. El plazo HTTP automático no se convierte en plazo humano. Todos los movimientos se resuelven tras el cierre correspondiente, sin reubicar zombies entre la publicación y esa resolución.

La duración de procesamiento forma parte de los dos segundos. `VentanaTurno` recibe el instante monotónico de inicio y deriva deadline, restante y retraso; no duerme ni programa la ejecución. El coordinador genera el snapshot de decisiones y el resultado antes de devolver la transición completa; aún no publica ni persiste. Planificar contra un plazo absoluto, no dormir dos segundos después de trabajar. Si el turno se retrasa, medirlo y registrar incumplimiento. No acumular avances instantáneos para ocultar retrasos ni pausar el mundo mientras se espera a un jugador.

## Fallos

- Decisión tardía o movimiento inválido: espera y contador de causa.
- No hay snapshot del turno: error medido; nunca usar silenciosamente otro turno.
- Persistencia fallida: no anunciar un estado confirmado que no pueda recuperarse. El control de versión del coordinador es un prechequeo local; el adaptador futuro debe aplicar compare-and-swap para evitar carreras reales.
- Reinicio: reanudar solo desde una fase confirmada y de forma idempotente; en caso contrario marcar interrupción.
- Mapa modificado por evento: invalidar planificación afectada antes de solicitar decisiones.

## Entrada y salida

Entrada: mapa validado, configuración de escenario, semilla, modo y eventos. Salida: estados versionados, decisiones recibidas, resultados y métricas. El estado aleatorio privado y las órdenes humanas registradas permiten reproducción; no se entregan al motor como conocimiento del futuro.
