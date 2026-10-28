# Roles y responsabilidades

Estado: espectador, operador de demo y servicio tienen flujos locales implementados parcialmente. Los roles de producto no son roles IAM de AWS.

## Actores del producto

| Actor | Puede | No puede | Flujo |
|---|---|---|---|
| Espectador | Ver proyección, rutas y métricas permitidas | Mover, reiniciar, cambiar modo o ver dormidos | [Espectador](espectador.md). |
| Jugador humano (alcance anterior) | Las API heredadas permiten sesión/personaje/orden cuando se ensamblan | No está disponible en la navegación principal actual | [Jugador](jugador.md). |
| Operador local | Iniciar/pausar/continuar el mundo, elegir una herramienta y agregar actores, refugios o incidentes | Modificar Reto, escribir desde el navegador posiciones confirmadas, eludir límites/reglas, operar fuera de loopback | [Operador](operador.md). |
| Simulador de servicio | Mover zombies, consultar `/paso`, aplicar decisiones y publicar | Compartir secretos o ejecutar dos coordinadores | [Simulador](simulador.md). |
| Motor | Recomendar un paso sobre una instantánea observable | Modificar el mundo o consultar dormidos privados | [Algoritmos](../../arquitectura/algoritmos.md). |

La sesión humana acredita propiedad del personaje; no es una cuenta permanente. El control local de operador requiere opt-in del proceso, loopback y Origin same-host. No se incluye una superficie productiva de administración. Reto no admite control humano ni intervenciones.

## Roles de trabajo humano

| Responsabilidad | Documentos y áreas a mantener |
|---|---|
| Dominio/simulación | Reglas, datos, flujo simulador y pruebas de mordida. |
| Backend/rutas | API, algoritmos, módulos backend y medición. |
| Frontend/juego | Flujos jugador/espectador, módulos frontend y eventos. |
| Infraestructura/operación | AWS, seguridad, costos y evidencias. |
| Integración/entrega | Estado actual, plan, cambios, decisiones y README. |

Una persona puede asumir varias responsabilidades. Esto no autoriza a crear agentes o delegar automáticamente: se siguen las instrucciones vigentes del usuario y de la sesión. Todo colaborador debe dejar una transferencia escrita al interrumpir trabajo incompleto.
