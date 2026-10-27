---
paths:
  - "backend/src/navira/domain/**"
  - "backend/src/navira/routing/**"
  - "backend/src/navira/simulation/**"
  - "backend/src/navira/application/**"
---
# Invariantes del juego

Fuentes: [reglas del mundo](../../docs/dominio/reglas-juego.md), [ODDD](../../docs/dominio/ODDD.md), [pendientes](../../docs/seguimiento/pendientes.md).

- El servidor es autoritativo: reloj, posición, legalidad, mordida y llegada. Aceptar una orden o calcular una ruta nunca mueve un personaje; solo el coordinador avanza el turno.
- Orden del turno (R-02): zombies primero, luego intenciones de sobrevivientes, todas con el mismo resolutor para humano y automático.
- Mordida por coincidencia de nodo al final del turno (R-09) y por cruce de la misma calle en sentido opuesto (R-10), incluidos ambos tramos del corredor. No declarar mordida en nodos intermedios.
- Movimiento inválido equivale a espera (R-03). Horda bloquea su nodo y todos los vecinos (R-06). Un mordido o evacuado no vuelve a decidir ni a ser mordido.
- Dormidos y estado del RNG privado nunca salen de la proyección observable, ni llegan a planificación, pronóstico o radio (R-07, invariantes 6 y 7 del ODDD). No compartir referencias mutables del mundo con consumidores.
- La aleatoriedad vive en el estado privado versionado de la partida; ningún planificador o proyección la consulta.
- `domain` no importa módulos del proyecto ni FastAPI/boto3. Preferir valores inmutables y funciones puras si no hay estado.
- Una solicitud repetida sobre la misma instantánea conserva su decisión (invariante 8).
- Las reglas PENDIENTES (P-01 a P-16) no se implementan como confirmadas: usar valores provisionales configurables, marcarlos en el código con el ID P-NN y no presentarlos como texto oficial.
- Cambiar una regla o supuesto exige registrar la aclaración con fecha y fuente en `docs/seguimiento/pendientes.md` y `docs/dominio/reglas-juego.md`, más CAM y ADR si es duradero.
- Documentar con docstring unidades, fase temporal e invariantes de las funciones públicas.
- Cubrir el cambio con pruebas T-01 a T-10, T-17 y T-24 según corresponda ([pruebas](../../docs/calidad/pruebas.md)).
