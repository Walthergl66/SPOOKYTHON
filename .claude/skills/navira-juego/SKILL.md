---
name: navira-juego
description: Usar al modificar reglas del mundo, simulación, rondas, resolutor, juego humano, endpoint /paso o panel de Navira, para proteger invariantes, determinismo y límite de latencia.
---

# Cambios en reglas, simulación, juego y panel

Fuentes: [reglas](../../../docs/dominio/reglas-juego.md), [pendientes](../../../docs/seguimiento/pendientes.md), [pruebas](../../../docs/calidad/pruebas.md). Usar `docs/`, no `docs/`.

1. **Reglas**: leer las R-xx de `reglas-juego.md` que afecta el cambio. Una regla confirmada no se altera por conveniencia.
2. **Pendientes**: leer los P-xx afectados en `pendientes.md`. Si el cambio depende de uno, tratarlo como supuesto configurable y declararlo; no presentarlo como requisito confirmado.
3. **Sin filtrar estado oculto**: comprobar que motor, radio, panel y respuestas HTTP/WebSocket no exponen zombies dormidos (ID, nodo, movimiento) ni estado aleatorio privado (T-04).
4. **Prueba primero**: identificar el T-NN correspondiente en `pruebas.md` y escribir (o ampliar) su prueba antes del código; confirmar que falla por la razón esperada.
5. **Un solo resolutor**: humanos y automáticos comparten validación y resolución; el servidor decide reloj, posición, legalidad, mordida y llegada. Zombies antes que sobrevivientes (T-06, T-16, T-17).
6. **Determinismo**: la misma semilla y el mismo snapshot deben dar el mismo resultado; ninguna caché cruza partidas (T-10, T-24). Verificarlo con una prueba, no por inspección.
7. **Límite de `/paso`**: conservar el contrato (API key) y comprobar que la latencia sigue por debajo de 500 ms; si no se midió, decirlo (T-11). Las metas p95 no son mediciones.
8. **Ejecutar**: `cd backend && python -m unittest discover -s tests -p 'test_*.py' -v` (o el módulo concreto) en el `.venv`; si toca el panel, `cd frontend && npm ci && npm run build`.
9. **Registrar** con el flujo de `navira-cambio-sdd` (CAM, estado, SPEC) y actualizar `pruebas.md` si cambia la cobertura de un T-NN.

## Límites a recordar

- Dos modos (simulador automático y juego humano) con reglas compartidas; las rondas oficiales no mezclan humanos.
- Estado compartido versionado por partida/turno/fase; una partida activa y un humano por partida son límites iniciales.
- No anunciar multijugador ni alta disponibilidad sin implementarlos y verificarlos.
