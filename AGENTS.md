# Instrucciones para agentes y colaboradores — Navira

Estas instrucciones aplican a todo este repositorio. Las instrucciones actuales del usuario y las reglas superiores de la sesión prevalecen. No sustituyen las autorizaciones de ejecución, acceso a servicios o publicación.

El nombre oficial del producto es **Navira**; usar `navira` para nuevos identificadores técnicos derivados del nombre. Conservar denominaciones antiguas solo al describir antecedentes históricos. No renombrar el directorio local `SPOOKYTHON` por iniciativa propia.

## 1. Primero revisar la documentación

**Antes de modificar código, configuración o documentación en una nueva tarea, revisar los archivos `.md` de `doc/`, incluidos sus subdirectorios. No empezar a implementar desde recuerdos del chat o solo leyendo este archivo.**

Orden de lectura inicial:

1. `doc/README.md`: índice, documentos propietarios y distinción entre vigente e histórico.
2. `doc/contexto.md`: objetivo, alcance y solicitudes del usuario.
3. `doc/estado-actual.md`: evidencia real, trabajo pendiente y siguiente paso.
4. `doc/continuidad.md`, `doc/cambios.md` y `doc/pendientes.md`.
5. `doc/PRD.md`, `doc/TRD.md`, `doc/ODDD.md`, `doc/SDD.md`, `doc/especificaciones/README.md` y `doc/trazabilidad.md`.
6. Todos los demás `.md` de `doc/`: arquitectura, reglas, modos, flujos por rol, módulos, contratos, datos, algoritmos, infraestructura, seguridad, pruebas, costos, plan, ADR, plantillas y referencias.

Inventariar con `rg --files doc -g '*.md'` y comparar con el índice para no omitir documentos nuevos. Si no hay `rg`, usar una alternativa equivalente. Leer los archivos; listar nombres no sustituye revisarlos. No es necesario releerlos antes de cada comando dentro de la misma tarea, salvo que cambien o falte contexto. Tras una transferencia o compactación, recuperar al menos el índice, estado, cambios y documentos de la tarea; completar cualquier lectura pendiente antes de editar.

Las referencias históricas explican el origen de decisiones, pero no reemplazan el contrato vigente. Si falta un documento necesario, inspeccionar lo disponible, registrar el hueco y reconstruirlo con evidencia; no inventar que se leyó o que existe una implementación.

## 2. Verificar el repositorio antes de actuar

- Contrastar `estado-actual.md` con archivos y resultados reales.
- No asumir que rutas de código previstas, comandos, dependencias, infraestructura o tests ya existen.
- Inspeccionar cambios previos y preservar trabajo ajeno. No revertir o borrar archivos sin comprenderlos.
- Distinguir requisito del reto, solicitud del usuario, decisión de diseño, supuesto, implementado y verificado.
- Elegir la tarea siguiente del plan y su criterio de aceptación. Avanzar dentro del alcance autorizado sin pedir confirmaciones repetidas para decisiones rutinarias y reversibles.

## 3. Invariantes del producto

Antes de implementar una tarea, identificar requisitos PRD/TRD y la SPEC aplicable. Seguir `doc/SDD.md`: especificar alcance/criterios, planificar tareas, implementar, verificar y registrar. Revisar `doc/ODDD.md` al modificar el dominio. Mantener vínculos requisito → SPEC/CA → tarea → prueba → CAM/evidencia.

Los cambios triviales pueden usar el flujo reducido en la tarea/CAM. La autorización ya existente persiste; no exigir otra aprobación humana por cada paso rutinario. `lista` no significa implementada ni concede permisos externos. Nuevos alcances requieren aclarar lo esencial; las dudas configurables documentadas no detienen trabajo independiente.

- Dos modos: simulador automático y juego humano, con reglas y resolutor compartidos.
- Las rondas oficiales son automáticas, con métricas separadas del juego.
- El servidor decide reloj, posición, legalidad, mordida y llegada; el navegador no modifica el mundo directamente.
- Conservar el contrato de `POST /paso`, API key y límite menor a 500 ms.
- Zombies antes que sobrevivientes; hordas bloquean nodo y vecinos; cruces opuestos se detectan por tramos.
- No revelar dormidos ocultos ni estado aleatorio privado al motor, radio o panel.
- Estado compartido persistido y versionado por partida/turno/fase. Caché reconstruible y coordinador único inicialmente.
- Una partida activa y un jugador humano por partida son límites iniciales; no anunciar multijugador o alta disponibilidad sin implementarlos y verificarlos.

Las reglas completas y sus dudas están en `doc/reglas-juego.md` y `doc/pendientes.md`; no resolver una ambigüedad presentándola como requisito confirmado.

## 4. Modularidad y comentarios

- Seguir `doc/arquitectura.md` y `doc/modulos/`. Reglas y rutas independientes de FastAPI, SDK AWS y UI.
- Casos de uso y puertos internos; transporte y persistencia en adaptadores; ensamblaje en el punto de entrada.
- Una única implementación de validación/resolución para humanos y automáticos.
- Documentar funciones públicas y lógica no evidente: propósito, unidades, fase temporal, invariantes y motivos de restricciones. Evitar comentarios que solo repitan la línea siguiente.
- Cada módulo nuevo debe tener responsabilidad, límites y pruebas descritos en su documento propietario. No crear capas o servicios sin una necesidad concreta.
- No introducir secretos, credenciales reales o datos privados en código, Markdown, ejemplos, capturas o logs.

## 5. Actualizar documentación como parte de cada cambio

Una tarea significativa no está cerrada hasta dejar documentación suficiente para otro agente:

1. Actualizar los documentos propietarios afectados; enlazar en vez de duplicar contratos.
2. Registrar qué cambió, por qué, origen de la solicitud, archivos, validación y pendientes en `doc/cambios.md` con ID `CAM-NNN`.
3. Actualizar `doc/estado-actual.md` con hechos reales y siguiente paso exacto, también si la tarea queda interrumpida.
4. Actualizar estados del plan y pendientes cuando corresponda; no marcar verificado sin evidencia.
5. Crear ADR para cambios duraderos de arquitectura, contratos, reglas o alcance. Una errata no requiere ADR.
6. Incluir cualquier nuevo `.md` en el índice correspondiente. Mantener `doc/` como ubicación canónica.

Conservar IDs existentes e historial. No modificar `doc/referencias/reto-original.md` para adaptarlo al código. No actualizar `doc/referencias/plan-previo.md` como si fuera el plan vigente. La antigua ruta `docs/PLAN_IMPLEMENTACION.md` no es fuente vigente y no existe en el árbol comprobado; no crear otra carpeta documental para duplicar `doc/`.

## 6. Verificar y reportar con honestidad

- Ejecutar `python3 scripts/check_docs.py` al cambiar documentación.
- Ejecutar también `python3 scripts/check_sdd.py` y, si cambia ese validador, `python3 -m unittest discover -s tests -p 'test_check_sdd.py'`. Son comprobaciones documentales; no prueban la app.
- No marcar SPEC `verificada` sin completar sus criterios, CAM existente y reporte de evidencia; una tarea parcial no completa toda la SPEC.
- Para código, ejecutar las pruebas relevantes de `doc/pruebas.md` y comandos realmente configurados; no inventar resultados o comandos disponibles.
- Registrar pruebas no ejecutadas y su causa. Metas de p95, supervivencia o costos no son mediciones.
- La documentación actual no constituye una app desplegada. Budget y recursos deben comprobarse antes de declararlos existentes.
- Al terminar, comunicar resultado, verificación y límites materiales. No hacer commits, crear agentes, enviar mensajes o publicar por el solo hecho de que estos documentos nombren roles o fases; seguir el alcance y las autorizaciones vigentes.

## 7. Punto de reanudación

Comenzar siempre por `doc/estado-actual.md`, no por la última tarea que se recuerde. Usar las plantillas de `doc/plantillas/` para registros y transferencia. Ningún agente debe depender de tener acceso a este chat para saber qué falta.
