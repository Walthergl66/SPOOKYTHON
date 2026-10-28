# Auditoría local de latencia y carga — CAM-157

Fecha: 2026-10-28 (America/Guayaquil).

## Alcance

El usuario reporta una espera perceptible al entrar y al comenzar una simulación, y solicita acercar las respuestas a la meta interna de 150 ms. Se midieron por separado la salud/HTML, el endpoint estático grande del mapa y `POST /paso`. La prueba fue local; no representa red pública ni Lightsail. La inspección automatizada del navegador no estuvo disponible en esta sesión, así que no se midió «tiempo hasta mapa visible» ni el render completo de MapLibre.

## Hallazgos de partida

| Operación | Medición local inicial | Lectura |
|---|---:|---|
| `GET /` en Vite | TTFB 2,9 ms | El HTML del frontend no explica por sí solo una espera de varios segundos. |
| `GET /salud` backend | TTFB 0,9 ms | La salud simple responde rápidamente. |
| `GET /panel/estado` | 565 bytes, TTFB 10,1 ms | Snapshot pequeño; no es el cuello observado. |
| `GET /panel/mapa`, sin compresión | 16.077.219 bytes, TTFB 348–376 ms, total 375–410 ms | Geometría grande; ya supera 150 ms antes de que el navegador la convierta y renderice. |
| `GET /panel/mapa`, gzip predeterminado (nivel 9) | 1.558.625 bytes, TTFB/total 1.242 ms en una muestra | Ahorra bytes, pero ocupa CPU excesiva. |

Microbenchmark de compresión de los mismos 16.077.219 bytes, cinco corridas por nivel:

| Nivel gzip | Mediana de CPU | Salida |
|---:|---:|---:|
| 1 | 51,6 ms | 2.286.267 bytes |
| 3 | 70,9 ms | 2.136.795 bytes |
| 6 | 191,0 ms | 1.712.090 bytes |
| 9 | 742,8 ms | 1.558.625 bytes |

## Cambio y verificación

CAM-157 configura gzip nivel 1 y almacena hasta dos cuerpos comprimidos por `mapVersion`. ETag permite que una recarga valide la versión vigente y reciba 304 sin volver a proyectar, validar ni transferir el grafo. La caché conserva solo la proyección pública del mapa; no incluye snapshots ni actores. `Cache-Control: private` y `Vary: Cookie` limitan su uso a la sesión correspondiente. Los clientes sin gzip conservan el JSON no comprimido.

En una app aislada sobre el mapa Manta:

| Solicitud | Resultado |
|---|---:|
| Primera respuesta gzip, mapa frío | 200, TTFB 449 ms, 2.286.172 bytes (corrida ASGI aislada) |
| Respuestas gzip de la misma versión | 200, TTFB 0,76–1,16 ms (ASGI); 33,81 ms total con TestClient, que descomprime los 16 MB en el cliente |
| Revalidación con ETag coincidente | 304, TTFB 0,74 ms (ASGI); 2,72 ms total con TestClient, 0 bytes |
| `Accept-Encoding: gzip;q=0` | JSON sin `Content-Encoding`, comprobado en TestClient |

La campaña aislada de `/paso` usó semilla `20261026`, escenario sintético mixto, 200 habitantes, concurrencia máxima 200, 20 turnos a dos segundos y cliente/servidor loopback. Resultado: 3.944 respuestas HTTP 200, 0 fallas; p50 45,911 ms, p95 67,364 ms, p99 132,830 ms, máximo 136,040 ms. Los 20 ciclos midieron 692,9–894,9 ms, sin exceder los dos segundos. El entorno comparte host y no mide AWS o la red pública.

## Límites y siguiente paso

- `/paso` queda debajo de 150 ms p95 en esta muestra exploratoria, pero se requiere R3 sostenido, varias semillas y medición desde el entorno desplegado para cerrar TRD-02/T-11.
- El mapa frío sigue por encima de 150 ms en servidor local. La caché reduce recargas posteriores; todavía no se midió la carga inicial completa de red, descompresión, creación de GeoJSON, descarga de tiles ni primer fotograma. La demora de hasta nueve segundos reportada por el usuario no se puede atribuir completamente ni declarar resuelta con estas cifras.
- El build de producción pasa, pero advierte que el chunk cartográfico `addStreetNameLayers-*.js` mide 1.066,87 kB (289,86 kB gzip). El mapa es de carga diferida y el chunk no se ha dividido más porque esta auditoría no midió si el costo se desplaza al primer render; revisar tamaño/tiempo de descarga desde un navegador real.
- La app activa anterior en `127.0.0.1:5173`/`8000` no se reinició para no alterar su partida. La prueba del nuevo backend corrió aislada en otro puerto y se cerró.
- El navegador automatizado está deshabilitado por configuración de Work, por lo que queda pendiente revisar la selección de refugios visualmente y medir el mapa en el navegador real.

Verificación de esta unidad: `test_panel.py` 19/19; `test_api_http.py` 8/8; frontend 97/97; `npm run build`; `compileall`; `check_docs.py`; `check_sdd.py`; `git diff --check`. El build deja una advertencia por el chunk cartográfico grande. No se declara cumplida la meta global de 150 ms ni el tiempo total de carga. Este reporte conserva la distinción entre endpoint de decisión, endpoint de mapa y tiempo hasta el render.
