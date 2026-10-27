# Fluidez del pronóstico — CAM-086

Fecha: 2026-10-27 (America/Guayaquil).

## Cambio

Se agrupan antes de propagar las distribuciones de caminantes (por nodo y fase) y corredores (por nodo), puesto que sus transiciones son lineales. Se construye una sola vez el índice de sobrevivientes por nodo en cada pronóstico y se cachea el índice de aristas inversas para grafos inmutables (dos entradas máximas). Las hordas continúan procesándose como bloqueos y no se incorporan dormidos al pronóstico.

## Verificación ejecutada

- `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_prediccion_rutas.py' -v`: 7 pruebas correctas.
- `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_decidir_paso.py' -v`: 15 pruebas correctas.
- `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py'`: 214 pruebas correctas en 90,870 s. Un test negativo imprime su mensaje de uso esperado; la suite finaliza con `OK`.
- Fixture local mediano (35.518 nodos, 75.548 aristas dirigidas, 176 zombies y 20 sobrevivientes): tres rondas de 1,266 s, 1,388 s y 1,443 s. El backend de demo activo en el mismo host competía por CPU. Un perfil bajo esa contención mostró propagación de caminantes y búsqueda de objetivos de corredor como zonas costosas; el agregado reduce las propagaciones de corredor de una por zombie a una por pronóstico/tipo.
- CAM-079 midió históricamente 1,172–1,361 s por turno con otra muestra y tampoco demostró el objetivo de 500 ms. Las condiciones y versiones no son idénticas; esto no constituye una comparación controlada ni prueba aceleración del ciclo completo.
- `/salud` respondió HTTP 200 en `127.0.0.1:8001/salud` al finalizar las mediciones.

## Límites y siguiente medición

La agregación conserva la exposición agregada de nodos/aristas mediante una prueba de equivalencia en grafos pequeños, pero no certifica todos los efectos de un turno bajo carga. Uvicorn no se reinició para preservar la partida de demo en memoria; por ello la partida viva continúa ejecutando la versión anterior del módulo hasta su próximo reinicio. Repetir la medición comparando el mismo mapa, escenario, población, semilla y velocidad con la versión anterior y la optimizada, sin otra carga local relevante, y reportar mediana/p95 por etapa y duración total. La cadencia oficial objetivo sigue sin verificarse.
