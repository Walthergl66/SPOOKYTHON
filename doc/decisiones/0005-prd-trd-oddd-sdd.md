# ADR-005 — PRD, TRD, OO + DDD y SDD sobre la documentación actual

Fecha: 2026-10-26. Estado: metodología incorporada; no implica aplicación implementada. Origen: solicitud explícita del usuario y confirmación de que ODDD significa orientación a objetos y diseño guiado por dominio.

## Contexto y decisión

Ya existen contratos, reglas, plan e historial. Añadir identificadores de producto y condiciones técnicas en PRD/TRD; documentar lenguaje, invariantes y límites en ODDD; incorporar SDD proporcional con SPEC, CA, tareas y pruebas enlazadas.

Conservar `doc/`, stack, alcance de dos modos y documentos especializados como fuentes de detalle. No crear otro roadmap/bitácora ni copiar instrucciones en archivos de herramientas no utilizadas. Mantener lectura inicial de Markdown solicitada por el usuario.

## Alternativas y consecuencias

Migrar toda la carpeta a una plantilla externa rompería enlaces y duplicaría trabajo. Instalar un framework/hook o skill no es necesario para el método local. La solución elegida añade metadatos y validador estructural con Python estándar, más pruebas negativas de ese validador.

La trazabilidad documental no prueba comportamiento; se necesitan pruebas reales al desarrollar. `lista` significa especificada, no implementada, y no reemplaza autorización. El alcance ya autorizado no obliga a aprobaciones repetidas. Cambios triviales usan registro reducido; los grandes actualizan especificación y plan.

## Evidencia y documentos

[SPEC-006](../especificaciones/SPEC-006-metodologia.md) registra criterios y evidencia de incorporación; [CAM-004](../cambios.md) registra intervención. Documentos propietarios: [PRD](../PRD.md), [TRD](../TRD.md), [ODDD](../ODDD.md), [SDD](../SDD.md) y [trazabilidad](../trazabilidad.md). No sustituye ADR-001 a ADR-004; los complementa.
