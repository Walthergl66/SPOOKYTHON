# Módulos backend y dependencias

Estado: implementación por fases. `src/navira/api/` contiene esquemas, autenticación y rutas HTTP; `src/navira/application/` incluye decisión Dijkstra, transición versionada y `EjecutarRondaAutomatica`; `src/navira/adapters/` incluye snapshots/mapas locales; `src/navira/domain/` contiene grafo y entidades/intenciones; `src/navira/simulation/` aplica cierres y construye snapshots. `src/navira/demo.py` ensambla contextos efímeros del mapa sintético para API y ejecutor local, con perfiles y zombies iniciales definidos en `ESCENARIOS_DEMO`; `src/navira/simulador_demo.py` selecciona el perfil, fija semilla y emite el reporte local filtrando dormidos. El punto de entrada API la carga solo con `NAVIRA_DEMO=1`; sin opt-in conserva el respaldo de espera. Dataset y poblaciones oficiales, persistencia durable/distribuida, reloj continuo, transporte/publicación, planificación temporal y evaluación siguen pendientes.

Lenguaje, contextos e invariantes: [ODDD](../ODDD.md). Requisitos técnicos: [TRD](../TRD.md); antes de implementar elegir la [SPEC](../especificaciones/README.md) correspondiente. La orientación a objetos no exige crear clases para funciones sin estado.

| Módulo | Responsabilidad | No debe hacer | Verificación |
|---|---|---|---|
| `domain/` | Grafo, entidades, transitabilidad, mordidas y llegadas | Importar FastAPI/boto3, usar HTTP o decidir permisos web | `test_mapa.py` y `test_modelo.py` validan mapa, estado y contexto de intención. |
| `routing/` | Dijkstra dirigido, costos por tipo y selección de refugio | Modificar mundo, leer dormidos o mezclar unidades | `test_dijkstra.py` cubre costo, desempate, cierres y bloqueos. |
| `simulation/` | Plazo de turno, fases, zombies, eventos y resolución | Mantener la única copia de estado o ejecutar coordinadores duplicados | `test_resolver.py` cubre movimientos/mordidas; `test_coordinador.py` cubre modo por fases, versionado/eventos/plazo local. Persistencia aún pendiente. |
| `application/` | Preparar/resolver turno, decidir paso, iniciar/finalizar partida; puertos de I/O | Depender de esquemas HTTP o SDK AWS | `test_decidir_paso.py` cubre estado/hazards visibles; `test_snapshots_persistidos.py` cubre CAS local. |
| `simulador_demo.py` | Ejecutar rondas automáticas locales con argumentos y emitir reporte JSONL | Ser reloj continuo, persistir resultados o representar el mapa real de Manta | `test_simulador_demo.py` cubre límite, semilla, movimientos, evacuación y argumentos inválidos. |
| `player/` | Aparición, propiedad lógica y orden humana por turno | Autorizar con cookies directamente o mover posiciones | Idempotencia y cierre de acciones. |
| `api/` | Esquemas, autenticación, HTTP y WebSocket | Implementar reglas o búsqueda dentro de controladores | Pruebas de contrato. |
| `adapters/` | DynamoDB futuro, snapshot en memoria, reloj, cliente HTTP del motor, métricas y proyecciones de transporte | Cambiar políticas del dominio o anunciar durabilidad del adaptador en memoria | Tres pruebas del CAS local; DynamoDB e integración siguen pendientes. |
| `main.py` | Ensamblar dependencias y arrancar componentes | Contener lógica de simulación | Arranque comprobable. |

## Dirección de importaciones

`domain` no importa módulos externos del proyecto. `routing` y las políticas de `player` dependen de tipos del dominio. `application` orquesta esas políticas y define puertos. El coordinador se ensambla con reloj, repositorio y cliente de decisiones inyectados; el código de transporte del simulador queda en adaptadores. `api` y `adapters` dependen de contratos internos; el núcleo nunca importa esos adaptadores. `main` ensambla implementaciones concretas.

Las credenciales de sesión se validan en el borde y producen una identidad simple para el caso de uso. La regla de propiedad se verifica dentro del caso de uso con esa identidad, para no depender únicamente de una pantalla.

## Casos de uso mínimos

1. Iniciar/cerrar partida y programar evento.
2. Preparar/publicar una instantánea observable de turno.
3. Decidir paso automático sobre esa instantánea.
4. Incorporar personaje humano y registrar/reemplazar orden.
5. Resolver todas las intenciones mediante un único validador.
6. Consultar proyección y exportar resultado.

No crear un servicio por entidad ni extraer microservicios inicialmente. Los comentarios y docstrings explican invariantes, unidades, fase del turno y motivos difíciles de deducir; no repiten cada línea. Un cambio de responsabilidad requiere actualizar este documento y el historial.
