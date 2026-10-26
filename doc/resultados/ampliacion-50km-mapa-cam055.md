# Evidencia CAM-055 — ampliación de 50 km por lado

## Alcance

A petición del usuario, la ventana visible se amplía aproximadamente 50 km en cada dirección cardinal respecto de la ventana anterior. Los límites WGS84 configurados son oeste `-81.219`, sur `-1.434`, este `-80.211`, norte `-0.468`. MapLibre ajusta la cámara a estos límites y los reutiliza para restringir el pan, el zoom mínimo y la máscara de tiles exteriores.

La extensión corresponde al basemap. El fixture de simulación sigue limitado a 300 nodos y 599 aristas en torno al área central; no hay actores, calles de Navira ni rutas simuladas distribuidos por toda la nueva ventana. Esta ventana no es un límite administrativo oficial y la cartografía visual no valida rutas seguras.

## Verificación

- Build frontend: `npm run build` correcto; Vite conserva el aviso conocido del chunk de MapLibre mayor a 500 kB.
- Documentación: `python3 scripts/check_docs.py` correcto (79 Markdown y 81 archivos comprobados); `python3 scripts/check_sdd.py` correcto (ocho SPEC); regresiones `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` correctas (8); `git diff --check` correcto.
- Inspección en `http://localhost:5173/`: aplicación disponible, cartografía y atribución de OpenFreeMap/OpenStreetMap cargadas, escala indicada de 20 km y control de zoom-out deshabilitado al nivel general. La partida visible estaba pausada en turno 1.
- Build y verificación local; no se midió cobertura cartográfica exhaustiva ni disponibilidad del proveedor.
- Commit individual: `fix: expand Manta map by 50km` en `master`; consultar el historial Git para el hash final.

## Limitaciones

El proveedor público de tiles requiere conexión y no ofrece SLA. El encuadre grande reduce el nivel de zoom y, por tanto, edificios extruidos no serán visibles en todas las escalas. La cobertura de las calles simuladas no cambia.
