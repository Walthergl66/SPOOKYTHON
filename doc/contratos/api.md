# Contratos HTTP

Estado: `/salud` y `/paso` tienen implementación local inicial; no hay endpoints desplegados. Solo el formato obligatorio de `/paso` y el estado mínimo provienen del reto; las rutas adicionales son diseño del equipo.

## API obligatoria del motor

```http
POST /paso
x-api-key: <secreto-de-servicio>
Content-Type: application/json

{"sobrevivienteId":"S-0089","nodoActual":"N-0117","turno":142}
```

```json
{"siguienteNodo":"N-0118"}
```

Éxito 200; respuesta menor a 500 ms. Conservar nombre, método, campos y cuerpo de éxito. Puede devolver el mismo nodo. Resolver partida activa en servidor sin exigir un campo adicional al evaluador. Mantener la misma decisión para una solicitud repetida sobre la misma instantánea. La ruta completa y las explicaciones van en otro canal.

Errores previstos: 401 por credencial ausente/incorrecta; 422 por esquema inválido; 404 por entidad inexistente; 409 por turno/fase incompatible; 503 si el estado confirmado no está disponible. En la base local, 401 y 422 los genera el adaptador HTTP; 503 indica que falta configurar `NAVIRA_API_KEY`. 404/409 dependen de la integración de estado y turno. Estos errores cuentan en la medición si aparecen en el flujo normal. Nunca responder con un turno anterior para ocultarlos.

## Rutas y permisos

| Ruta prevista | Identidad | Resultado |
|---|---|---|
| `GET /salud` | Lectura pública mínima | Salud, sin secretos o volcado interno. |
| `GET /mapa` | API key de servicio | Grafo técnico versionado. |
| `GET /estado` | API key de servicio | Estado observable del turno requerido/activo. |
| `GET /panel/mapa` | Lectura de panel limitada | Grafo público para visualización. |
| `GET /panel/estado` | Lectura de panel limitada | Proyección observable y métricas permitidas. |
| `WS /ws` | Sesión/canal de observación validado | Eventos observables, sin credencial maestra. |
| `POST /juego/unirse` | Creación/recuperación de sesión temporal | Personaje o estado pendiente de aparición. |
| `GET /juego/mi-personaje` | Sesión propietaria | Personaje y última orden. |
| `POST /juego/accion` | Sesión propietaria | Acuse de orden; no mueve posición. |
| `GET /juego/recomendacion` | Sesión propietaria | Sugerencia actual con límite de frecuencia. |
| `POST /admin/partidas` | Operador | Iniciar partida si no hay una activa. |
| `POST /admin/partidas/{runId}/finalizar` | Operador | Cierre explícito y motivo. |
| `POST /admin/eventos` | Operador | Evento validado para un turno. |

Las rutas de panel evitan enviar `x-api-key` maestra al navegador. Tienen proyección y límites propios; no son una puerta de entrada al estado real. La CLI administrativa tampoco conserva secretos en argumentos o ejemplos versionados.

## Orden humana

```json
{
  "runId": "juego-001",
  "turno": 12,
  "personajeId": "P-01",
  "siguienteNodo": "N-0118",
  "accionId": "orden-00031"
}
```

El servidor valida sesión, propiedad, modo, fase, turno y movimiento topológico. Genera una secuencia creciente. Repetir `accionId` con el mismo cuerpo devuelve el acuse existente; usarlo con otro cuerpo produce conflicto. La última orden válida aceptada antes del cierre sustituye la previa; la persistencia confirma el orden, no un timestamp del cliente. Si se permite concurrencia en reemplazos, usar una condición de versión para que una escritura tardía no revierta una más nueva.

Acuse previsto:

```json
{"accionId":"orden-00031","secuencia":31,"estado":"recibida","turno":12}
```

Rechazar órdenes tardías o de otra partida sin trasladarlas al turno siguiente. Falta de orden implica espera. Un acuse confirma recepción persistida; el movimiento se confirma al resolver el turno. No rechazar una orden solo por riesgo estimado, pero sí por transitabilidad/reglas de horda.

## Estado observable mínimo

```json
{
  "runId":"ejemplo",
  "turno":142,
  "fase":"zombies_movidos",
  "mapVersion":"manta-v1",
  "zombies":[{"id":"Z-01","tipo":"corredor","nodo":"N-0120"}],
  "aristasBloqueadas":["E-034"],
  "movimientosZombies":[{"id":"Z-01","trayecto":["N-0118","N-0119","N-0120"]}],
  "sobrevivientes":[{"id":"S-0089","nodo":"N-0117","estado":"activo"}]
}
```

Todos los IDs del ejemplo son ilustrativos. `movimientosZombies` amplía el estado mínimo para resolver cruces; nunca publica trayectos de dormidos que sigan ocultos. En implementación, fijar esquemas de solicitudes, respuestas y errores mediante OpenAPI y pruebas, sin romper el contrato obligatorio.
