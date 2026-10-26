# Plantilla — especificación SDD

Crear `doc/especificaciones/SPEC-NNN-nombre.md`, enlazarlo desde su índice y registrar requisitos en la matriz. Sustituir marcadores por IDs reales existentes; no copiar esta plantilla como si ya estuviera verificada.

```text
# SPEC-NNN — Nombre concreto

ID: SPEC-NNN
Estado: borrador
Requisitos: IDs PRD/TRD definidos, separados por coma
Tareas: IDs existentes del plan, separados por coma
Pruebas: IDs T existentes, separados por coma
Cambio: pendiente
Evidencia: pendiente

## Objetivo y alcance
Origen, problema, resultado esperado, inclusiones y exclusiones.
Enlaces a contratos/reglas/modelo propietarios; no duplicarlos.

## Criterios de aceptación
Tabla: Criterio | Comportamiento verificable | Pruebas
Usar CA-NNN-01, CA-NNN-02... y pruebas T declaradas.
Incluir caminos normales, errores y límites relevantes.

## Plan y módulos
Tareas, dependencias, unidades pequeñas y documento de módulos afectado.

## Riesgos y verificación
Pendientes con ID, estrategia de pruebas y evidencia real al cerrar.
Para verificada: Cambio debe ser CAM existente y Evidencia ruta relativa a reporte real.
```

Un alcance ya autorizado no exige una aprobación humana adicional por cada tarea. Un borrador que amplía alcance no autoriza implementarlo. Estados y flujo: [SDD](../SDD.md).
