# Contexto del proyecto

Estado: alcance acordado y diseño pendiente de implementación. Fecha: 2026-10-26.

## Problema y objetivo

Track A «Escape de Manta Zombie»: construir en AWS un motor que recomiende el siguiente movimiento hacia un refugio mientras zombies y cierres de calles cambian el mapa. Es una demostración de rutas dinámicas aplicables a evacuación y despacho; no es un sistema validado para emergencias reales.

Nombre de trabajo propuesto: **MantaSafe**, todavía modificable. El repositorio local está en `SPOOKYTHON`; ese nombre no obliga a cambiar el nombre del producto.

## Solicitudes explícitas del usuario

1. Analizar el reto y proponer una solución viable.
2. Preparar un plan de implementación.
3. Incorporar dos modos: simulador automático y juego en el que una persona aparece aleatoriamente y lleva su personaje a un refugio.
4. Modularizar toda la documentación en `doc/`, registrar el contexto de cada cambio y crear un `AGENTS.md` que exija revisar los `.md` antes de trabajar.
5. Incorporar PRD, TRD, ODDD y SDD. El usuario confirmó ODDD como orientación a objetos y diseño guiado por dominio (OO + DDD); la adopción conserva stack, modos y alcance existentes.

Documentos de producto y método: [PRD](PRD.md), [TRD](TRD.md), [ODDD](ODDD.md), [SDD](SDD.md). Criterios por funcionalidad: [especificaciones](especificaciones/README.md).

La versión mínima de juego contempla un personaje humano activo por partida, supuesto de implementación comunicado en la conversación. Multijugador simultáneo y múltiples partidas concurrentes no forman parte de la primera versión; ampliar si el usuario lo solicita.

## Obligaciones del reto

- Grafo de Manta de unas 300 intersecciones, calles con distancia/tipo/velocidad y cuatro refugios.
- Turnos de dos segundos; zombies antes que sobrevivientes; cuatro tipos de zombie y cierres en vivo.
- `POST /paso` con el contrato exacto, API key y respuesta en menos de 500 ms.
- Simulador propio que publica estado y consulta al motor; mapa vivo y despliegue AWS.
- AWS Budget con alerta desde el primer día, repositorio público e historial real de commits.
- README, arquitectura exportada, costos, endpoint, ejecución/medición documentadas y pitch.

Fuente completa y rúbrica: [reto original](referencias/reto-original.md). Reglas detalladas: [reglas del juego](reglas-juego.md).

## Prioridades

Primero reglas correctas, nivel base completo, supervivencia y latencia. Después predicción demostrable y juego humano mínimo. Capacidad de refugios y camionetas solo después de estabilizar las rondas. El juego es un complemento solicitado, no un sustituto de la evaluación automática.

Prueba: tres rondas de cinco minutos, con 20, 80 y 200 sobrevivientes. Dentro de la prueba: supervivencia 50 %, eficiencia 20 %, latencia 15 % y disponibilidad 15 %. La prueba pesa 40 % de la nota total. Objetivos internos: p95 ≤150 ms, errores/timeouts <0,5 %, cero decisiones inválidas y reloj dentro de su período. Todavía no hay resultados.

## Fechas proporcionadas

Entrega: miércoles 28 de octubre de 2026 a las 10:00, Ecuador continental (UTC−5). Demo: viernes 30, ULEAM, cinco minutos de pitch y tres de preguntas. Conservar estas fechas como datos del documento; si hay una prórroga, registrar la fuente antes de cambiarlas.

## Límites actuales

No existe aplicación, mapa ni despliegue verificados. Las aclaraciones de reglas y región están en [pendientes](pendientes.md). El trabajo de código debe empezar desde [estado actual](estado-actual.md), sin asumir que los archivos previstos en el plan ya existen.
