# Módulos backend y dependencias

Estado: estructura prevista; aún no existen estos módulos. Raíz de código propuesta: `src/mantasafe/`.

Lenguaje, contextos e invariantes: [ODDD](../ODDD.md). Requisitos técnicos: [TRD](../TRD.md); antes de implementar elegir la [SPEC](../especificaciones/README.md) correspondiente. La orientación a objetos no exige crear clases para funciones sin estado.

| Módulo | Responsabilidad | No debe hacer | Verificación |
|---|---|---|---|
| `domain/` | Grafo, entidades, transitabilidad, mordidas y llegadas | Importar FastAPI/boto3, usar HTTP o decidir permisos web | Pruebas puras con grafos pequeños. |
| `routing/` | Dijkstra, A* temporal, riesgos y selección de refugio | Modificar mundo, leer dormidos o mezclar unidades | Casos de ruta y comparación de políticas. |
| `simulation/` | Reloj, fases, zombies, eventos y resolución | Mantener la única copia de estado o ejecutar coordinadores duplicados | Escenarios y reproducción. |
| `application/` | Preparar turno, decidir paso, iniciar/finalizar partida; puertos de I/O | Depender de esquemas HTTP o SDK AWS | Casos de uso con adaptadores en memoria. |
| `player/` | Aparición, propiedad lógica y orden humana por turno | Autorizar con cookies directamente o mover posiciones | Idempotencia y cierre de acciones. |
| `api/` | Esquemas, autenticación, HTTP y WebSocket | Implementar reglas o búsqueda dentro de controladores | Pruebas de contrato. |
| `adapters/` | DynamoDB, reloj, cliente HTTP del motor, métricas y proyecciones de transporte | Cambiar políticas del dominio | Integración y fallos de dependencias. |
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
