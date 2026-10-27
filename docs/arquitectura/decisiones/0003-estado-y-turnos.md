# ADR-003 — Estado versionado y autoridad única

Fecha: 2026-10-26. Estado: aceptada para diseño; implementación pendiente.

## Contexto

Solicitudes concurrentes, zombies móviles, cruces de calles y múltiples fases hacen incorrecto usar cualquier «estado más reciente» sin identidad. Memoria aislada o coordinadores duplicados pueden generar decisiones y movimientos inconsistentes.

## Decisión

Una partida activa y un coordinador autoritativo. Snapshot identificado por `(runId, turno, fase, mapVersion)`, persistido antes de anunciar disponibilidad. Separar mundo real privado de proyección observable. Órdenes confirmadas se persisten con identidad, secuencia e idempotencia antes del acuse. Cachear solo datos reconstruibles.

Zombies se mueven antes de la fase de decisión; registrar trayectos completos, no solo extremos. Todos los sobrevivientes deciden sobre la misma fase y se resuelven conjuntamente. Reloj absoluto de dos segundos con procesamiento incluido. Reinicio solo reanuda si hay un checkpoint completo y lógica idempotente verificada; si no, declarar interrupción explícita.

## Alternativas y consecuencias

Estado mutable solo en memoria simplifica al inicio pero impide recuperar y compartir correctamente. Leer siempre «último» omite fase/turno y puede aplicar un cierre a unos personajes y no a otros. Versionar añade almacenamiento y coordinación; se medirá tamaño, costo y publicación de snapshots sin imponer un esquema físico aún no comprobado.

No escalar réplicas del simulador sin liderazgo/particionado. Recuperación robusta no se considera existente por estar descrita. Documentos propietarios: [datos](../../dominio/datos.md), [flujo simulador](../../dominio/flujos/simulador.md) y [pruebas](../../calidad/pruebas.md).
