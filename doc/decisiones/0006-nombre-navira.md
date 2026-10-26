# ADR-006 — Nombre oficial Navira

Fecha: 2026-10-26. Estado: decisión explícita del usuario, aplicada a documentación vigente. Cambio: CAM-005.

## Contexto y decisión

El usuario establece que la app se llamará **Navira**. Este nombre sustituye la propuesta provisional MantaSafe para el producto y las nuevas referencias técnicas. Usar `navira` como identificador derivado y `src/navira/` como paquete backend previsto.

## Consecuencias y límites

Actualizar README, instrucciones para agentes, contexto, PRD/TRD, modelo ODDD y rutas propuestas. Conservar el nombre anterior en documentos históricos para no alterar cómo se originó el proyecto. No cambiar alcance, stack, contratos, IDs de requisitos, especificaciones o tareas.

No hay aplicación o paquete implementados que migrar. El directorio de trabajo `SPOOKYTHON` conserva su nombre. Esta decisión no crea recursos AWS, dominios o un repositorio remoto.

Fuentes vigentes: [contexto](../contexto.md), [PRD](../PRD.md), [módulos backend](../modulos/backend.md). Resultado y validación: [historial](../cambios.md) y [estado actual](../estado-actual.md).
