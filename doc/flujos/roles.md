# Roles y responsabilidades

Estado: diseño previsto. Los roles de producto no son roles IAM de AWS.

## Actores del producto

| Actor | Puede | No puede | Flujo |
|---|---|---|---|
| Espectador | Ver proyección, rutas y métricas permitidas | Mover, reiniciar, cambiar modo o ver dormidos | [Espectador](espectador.md). |
| Jugador | Controlar su personaje, esperar y pedir sugerencia | Controlar otros, alterar reloj o revelar información oculta | [Jugador](jugador.md). |
| Operador | Iniciar/finalizar, elegir escenario y programar cierres | Alterar resultados históricos sin dejar registro | [Operador](operador.md). |
| Simulador de servicio | Mover zombies, consultar `/paso`, aplicar decisiones y publicar | Compartir secretos o ejecutar dos coordinadores | [Simulador](simulador.md). |
| Motor | Recomendar un paso sobre una instantánea observable | Modificar el mundo o consultar dormidos privados | [Algoritmos](../algoritmos.md). |

La sesión de jugador acredita propiedad del personaje; no es una cuenta permanente. El operador usa una credencial distinta a la API key de servicio. El modo simulador no admite control humano en sus rondas oficiales.

## Roles de trabajo humano

| Responsabilidad | Documentos y áreas a mantener |
|---|---|
| Dominio/simulación | Reglas, datos, flujo simulador y pruebas de mordida. |
| Backend/rutas | API, algoritmos, módulos backend y medición. |
| Frontend/juego | Flujos jugador/espectador, módulos frontend y eventos. |
| Infraestructura/operación | AWS, seguridad, costos y evidencias. |
| Integración/entrega | Estado actual, plan, cambios, decisiones y README. |

Una persona puede asumir varias responsabilidades. Esto no autoriza a crear agentes o delegar automáticamente: se siguen las instrucciones vigentes del usuario y de la sesión. Todo colaborador debe dejar una transferencia escrita al interrumpir trabajo incompleto.
