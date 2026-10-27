# TRD — Requisitos técnicos de Navira

Versión: 1. Fecha: 2026-10-26. Estado: requisitos documentados, sin implementación de producto. En este repositorio TRD significa Technical Requirements Document. Se deriva del [PRD](PRD.md), [reto](../referencias/reto-original.md) y decisiones vigentes; no selecciona un stack nuevo.

## Condiciones verificables

### TRD-01 — Contrato obligatorio

Mantener método, ruta y cuerpos exactos de `POST /paso`, con `x-api-key`. Un paso es vecino por calle habilitada o mismo nodo; los errores se miden. Esquemas y rutas auxiliares: [API](../arquitectura/contratos/api.md). No exigir campos adicionales al evaluador.

### TRD-02 — Latencia y carga

Límite obligatorio: respuesta menor a 500 ms por solicitud. Meta interna: p95 ≤150 ms y errores/timeouts <0,5 %. Probar ráfagas de 20/80/200, no solo promedios. Medir desde el cliente y declarar su ubicación/ruta; no confundir tiempo interno con HTTP público. Fuente de umbrales: [pruebas](../calidad/pruebas.md).

### TRD-03 — Tiempo y resolución

Turnos de dos segundos con procesamiento incluido, zombies antes que sobrevivientes y resolución conjunta. El humano no adelanta reloj ni obtiene pasos por clics. Cierre humano inicial 1,7 segundos y reserva de 300 ms son parámetros de diseño a medir, no una regla oficial. Detalle: [simulador](../dominio/flujos/simulador.md).

### TRD-04 — Consistencia y recuperación

Estado persistido y versionado por partida/turno/fase/mapa; caché reconstruible, coordinador único y órdenes confirmadas solo tras persistir. No publicar snapshots parciales o aplicar dos veces un turno. Reanudar solo si hay recuperación idempotente verificada; si no, interrumpir explícitamente. Detalle: [datos](../dominio/datos.md).

### TRD-05 — Información observable

Motor, radio y panel reciben únicamente la proyección permitida. No revelar dormidos ocultos, estado aleatorio privado ni credenciales. Persistencia privada no equivale a permiso de lectura pública. Detalle: [datos](../dominio/datos.md), [seguridad](../operacion/seguridad.md).

### TRD-06 — Autorización y transporte

Separar credencial de servicio, operador y sesión propietaria. Validar origen, propiedad, turno, entrada y límites de frecuencia. Ninguna clave maestra en el frontend. Resolver TLS/origen antes de publicar autenticación. Detalle: [seguridad](../operacion/seguridad.md); pendientes P-11/P-12.

### TRD-07 — Tiempo real y acceso a la interfaz

Eventos identificados por partida, fase y secuencia; recuperación sin huecos y marca visible de desconexión. Juego operable con mouse y teclado, foco visible y estados no dependientes solo del color. Detalle: [eventos](../arquitectura/contratos/eventos.md), [frontend](../arquitectura/modulos/frontend.md).

### TRD-08 — AWS y presupuesto

Desplegar en cuenta/región permitidas, establecer Budget con alerta desde el inicio y conservar evidencia. Stack previsto en [arquitectura](../arquitectura/arquitectura.md) e [infraestructura](../operacion/infraestructura.md); no sustituirlo sin motivo/ADR. El tamaño inicial no garantiza capacidad. Gasto real y estimación completa separados en [costos](../operacion/costos.md).

### TRD-09 — Modularidad del código

Dominio y rutas sin dependencia de HTTP/AWS/UI; casos de uso y adaptadores con puertos internos. Un único resolutor para control humano/automático. DTO de transporte separado del dominio. Orientación a objetos pragmática y modelo: [ODDD](../dominio/ODDD.md). No imponer jerarquías de herencia o microservicios.

### TRD-10 — Observabilidad y evidencia

Registrar latencia del cliente, errores, timeouts, duración/fase de turnos, retraso del reloj y versión de código/mapa/escenario. Exportar resultados reales y distinguir juego de simulación. Sin resultados ficticios o selección de ejecuciones favorables. Detalle: [pruebas](../calidad/pruebas.md).

### TRD-11 — Reproducción

Cada partida nueva sin semilla explícita obtiene una semilla impredecible. Para reproducir una partida, conservar semilla, estado privado del generador, versiones de código/mapa, configuración, eventos, órdenes humanas y decisiones externas. Con entradas idénticas en la misma versión de reglas se reproduce la misma secuencia; cambiar entradas, estado o versión puede producir una cascada distinta. Una semilla sola no promete reproducción entre versiones del algoritmo. El generador y su estado nunca son observables para jugador, panel o motor. Detalle: [datos](../dominio/datos.md).

### TRD-12 — Peligros y calles

Validar horda y vecinos, cierres, nodos finales y tramos opuestos de ambos pasos de un corredor. Identificar el segmento físico sin confundir calles paralelas. Separar validez topológica de riesgo de mordida. Detalle: [reglas](../dominio/reglas-juego.md).

### TRD-13 — Desarrollo y continuidad verificables

Aplicar [SDD](../metodo/SDD.md), leer `docs/` antes de editar y enlazar requisitos, criterios, tareas, pruebas y cambios. Usar comandos reales de validación y conservar incertidumbres. La validación estructural no prueba rendimiento ni semántica de negocio. Detalle: [continuidad](../metodo/continuidad.md), [trazabilidad](../metodo/trazabilidad.md).

### TRD-14 — Prioridad de supervivencia en rutas

En cada decisión, la política temporal minimiza primero la exposición estimada en la ventana observable; turnos, costo de calle y desempates solo se consideran después. Comparar resultados reales en orden lexicográfico `(mordidos ascendente, evacuados descendente)`. La predicción usa solo amenazas observables, respeta el presupuesto configurado y recurre a Dijkstra si no obtiene una ruta completa; `/paso` conserva su contrato. Reportar puntaje estimado y conteo real como conceptos separados. Detalle: [algoritmos](../arquitectura/algoritmos.md), [ADR-018](../arquitectura/decisiones/0018-politica-riesgo-prioritario.md).

### TRD-15 — Límite geográfico jugable

Las partidas sobre el fixture Manta usan una proyección del grafo dentro de la caja WGS84 `[-80.807, -1.082]`–`[-80.621, -0.897]`. Solo nodos internos y calles con ambos extremos internos participan en apariciones, amenazas, rutas y movimiento. El selector de refugios enfoca esa misma caja y solo acepta nodos internos; el backend vuelve a validar la selección antes de iniciar. El fixture OSM fuente completo no se modifica. Esta ventana estimada no es frontera administrativa. Detalle: [SPEC-008](../metodo/especificaciones/SPEC-008-mapa-cartografico-3d.md), [ADR-030](../arquitectura/decisiones/0030-ventana-urbana-zona-jugable.md).

## Riesgos y aceptación

Reglas ambiguas, región, TLS y sesiones siguen en [pendientes](../seguimiento/pendientes.md); ningún documento nuevo las cierra por inferencia. Verificar con las especificaciones y pruebas correspondientes antes de marcar implementado/verificado. Una discrepancia con código se investiga, no se resuelve adaptando silenciosamente los requisitos al fallo.
