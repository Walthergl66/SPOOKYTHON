# Evidencia CAM-095 — Foco urbano y reinicio de Reto

Fecha de ejecución: 2026-10-27, Ecuador continental. Evidencia local sobre el fixture OSM de Manta; no representa medición oficial, de supervivencia ni de AWS.

Commit de implementación: `79bc5d6` (`feat(reto): add restart and centralize threats`).

## Comportamiento verificado

- Cada perfil Reto (R1/R2/R3) ubica al menos `round(0,8 × cantidad_del_tipo)` zombies de cada tipo dentro de 3.500 m del ancla aproximada Parque La Dolorosa/R-03. La cuota se aplica también a hordas y dormidos; no expone dormidos en la proyección pública.
- R2 elige su puente y R3 elige sus dos segmentos dentro del foco central cuando hay candidatos. El fixture actual sí ofrece suficientes segmentos; el algoritmo conserva un fallback a toda la ventana para otros mapas/versiones sin suficientes candidatos.
- Semilla igual conserva tipo, ubicación y eventos del mundo Reto. Simulador libre conserva el muestreo estratificado de la ciudad completa y sus incidentes generales; la concentración se activa solo en el flujo Reto sobre Manta.
- `POST /reto/reiniciar` conserva ronda/población, sustituye un run Reto activo o pausado por un `runId` nuevo y genera otra semilla por defecto. Sin partida Reto responde 409. La UI muestra «Reiniciar Rn» cuando el estado Reto tiene un run, adopta inmediatamente la respuesta y mantiene visible la ronda actual.

## Pruebas ejecutadas

- Pruebas focalizadas backend: 5/5 (`test_presets_de_reto_respetan_tipos_y_eventos_reproducibles`, `test_reto_concentra_cada_tipo_de_zombie_y_eventos_en_el_centro`, `test_simulador_libre_no_usa_el_foco_urbano_de_reto`, `test_ruta_reto_reinicia_la_ronda_actual_en_un_run_nuevo`, `test_reiniciar_reto_sin_ronda_devuelve_conflicto`).
- Suite backend completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py'`: 227/227. Un test CLI imprime su salida de ayuda esperada para validar argumentos inválidos.
- Frontend: `npm test -- --run` 95/95; `npm run build` correcto. Se mantiene la advertencia existente de chunk `mapArea` de 1.065,62 kB.
- `python3 -m compileall -q src tests` correcto; `python3 backend/scripts/check_docs.py` correcto (124 Markdown en `docs/`, 126 archivos comprobados); `python3 backend/scripts/check_sdd.py` correcto (9 SPEC con trazabilidad estructural); regresiones `test_check_sdd.py` 8/8; `git diff --check` correcto.
- Smoke HTTP en el proceso nuevo: `/salud` respondió 200; el control local reconoció R2 con 80 sobrevivientes; `POST /reto/reiniciar` respondió 200, conservó ronda/población y cambió `runId`. El intento anterior de `/reto/iniciar` devolvió 409 al detectar la partida activa existente, respetando la protección. El navegador local en `http://localhost:5173/` confirmó en el árbol de accesibilidad «Reiniciar R2», estado de simulación activa y API disponible; el mapa seguía mostrando «Cargando mapa de Manta…» durante esta inspección.

## Límites

Centro, radio de 3,5 km y cuota del 80% son parámetros provisionales de presentación espacial. El reto no fija densidad zombie ni distribución de amenazas. Mantener P-09/P-15 abiertos; no afirmar que la ciudad modela riesgo o densidad real.
