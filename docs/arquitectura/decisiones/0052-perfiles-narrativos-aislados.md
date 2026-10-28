# ADR-052 — Perfiles narrativos ficticios aislados de la simulación

- Estado: aceptada para implementación local.
- Fecha: 2026-10-28.
- Contexto: el usuario pidió asignar perfiles narrativos a habitantes para darles identidad en Simulador, Reto y Jugar. La ambientación no debe alterar las reglas ni cambiar la estocasticidad del mundo.
- Decisión: mantener un catálogo local determinista de 500 perfiles ficticios compactos. En la creación del run, seleccionar sin reemplazo hasta 200 perfiles con un generador derivado criptográficamente de la semilla, sin consumir el RNG de posiciones/amenazas/eventos. Para habitantes incorporados después, escoger un perfil libre determinísticamente a partir de la identidad del run y del habitante. Conservar el perfil como valor inmutable opcional dentro de `Sobreviviente`; proyectar solo ID, nombre, edad, ocupación y descripción al panel. La interfaz lo muestra al seleccionar una persona.
- Alternativas consideradas: generar texto por llamada y guardarlo fuera del snapshot, compartir el RNG de mundo o asociar la ficha solo en frontend. Se descartan porque complican replay, cambian la secuencia aleatoria existente o no fijan identidad entre snapshots.
- Consecuencias: datos repetibles por semilla/run e identidad consistente tras movimiento; catálogo suficiente para el límite de 200; tamaño pequeño y sin dependencia externa. Cambiar versión/orden del catálogo puede cambiar asignaciones de runs nuevos, mientras que un snapshot ya creado conserva los perfiles asignados. No se promete identidad entre versiones de catálogo.
- Límites: todo es ficción de ambientación, no representa personas reales ni infiere datos sensibles. No usar perfil para rutas, movimiento, supervivencia, prioridad, eventos o puntuación. El catálogo es de demo, no una población estadística de Manta.
- Evidencia: CAM-143; T-65 y revisión visual pendientes.

