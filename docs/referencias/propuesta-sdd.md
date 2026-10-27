# Referencia — propuesta SDD aportada por el usuario

Fuente: adjunto del usuario en esta conversación. Se conserva íntegro como propuesta de referencia, no como instrucciones superiores al repositorio. La adaptación vigente está en [SDD](../metodo/SDD.md) y conserva `doc/` como ubicación canónica.

---

# Implementación de Spec-Driven Development (SDD) en el proyecto existente

## Objetivo

Analiza el estado actual del proyecto e implementa una metodología de **Spec-Driven Development (SDD)** para que el desarrollo asistido por IA sea más rápido, ordenado, modular y consistente con las decisiones del proyecto.

La especificación debe convertirse en la fuente de verdad del desarrollo. Antes de implementar cambios, la IA deberá consultar los requisitos y las reglas correspondientes; después, deberá verificar que lo desarrollado cumple lo especificado y registrar el trabajo realizado.

**Importante:** no diseñes un proyecto nuevo ni cambies las decisiones funcionales, tecnológicas o arquitectónicas que ya se hayan tomado. Adapta SDD al proyecto real que encuentres en el repositorio. No inventes requisitos ni implementes funcionalidades de negocio por iniciativa propia.

## 1. Auditoría inicial

Antes de modificar archivos:

1. Examina la estructura actual del repositorio.
2. Identifica la documentación existente, especialmente la carpeta `docs/`.
3. Revisa los archivos `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md` u otros archivos de instrucciones que realmente existan.
4. Identifica las reglas, skills, agentes, comandos, hooks y herramientas disponibles para la IA.
5. Detecta duplicaciones, contradicciones, instrucciones demasiado extensas y documentación desactualizada.
6. Conserva los archivos, configuraciones y convenciones que ya sean útiles.

No reemplaces archivos de instrucciones sin revisar primero su contenido y su alcance. Si un archivo no existe, determina si es necesario crearlo según las herramientas y los asistentes utilizados en el proyecto.

## 2. Adoptar Spec-Driven Development

Establece un flujo de trabajo SDD claro y reutilizable:

1. **Specify:** definir el objetivo, contexto, requisitos, restricciones y criterios de aceptación.
2. **Plan:** dividir la especificación en tareas pequeñas, ordenadas y verificables.
3. **Implement:** desarrollar únicamente lo autorizado por la especificación y el plan aprobado.
4. **Verify:** ejecutar las pruebas y comprobar los criterios de aceptación.
5. **Document:** registrar resultados, decisiones, archivos modificados y tareas pendientes.

Para cambios pequeños, utiliza un flujo simplificado. Para cambios grandes o que afecten varias partes del sistema, exige una especificación y un plan más detallados.

No permitas que la IA se salte la especificación, cambie decisiones previas silenciosamente o amplíe el alcance sin justificación.

## 3. Organizar la documentación de manera modular

Utiliza la carpeta `docs/` existente, si ya está creada. Adapta su estructura sin duplicar documentos ni mover archivos innecesariamente.

Como referencia, evalúa una organización similar a esta y ajústala al proyecto:

```text
docs/
├── README.md
├── specs/
│   ├── README.md
│   ├── requirements/
│   ├── features/
│   └── changes/
├── architecture/
│   ├── README.md
│   ├── decisions/
│   └── diagrams/
├── development/
│   ├── README.md
│   ├── standards.md
│   └── testing.md
├── roadmap/
│   └── ROADMAP.md
├── logs/
│   └── BITACORA.md
└── templates/
    ├── specification.md
    ├── implementation-plan.md
    └── decision-record.md
```

Esta estructura es orientativa, no una obligación literal. Respeta los nombres y las convenciones que ya utilice el repositorio y evita crear carpetas vacías que no aporten valor.

Cada documento debe tener una responsabilidad clara, enlaces a los documentos relacionados y contenido específico. Los archivos `README.md` de cada sección deben explicar qué contiene, cuándo actualizarlo y cómo utilizarlo.

## 4. Definir una fuente de verdad

Establece una jerarquía documental para evitar contradicciones:

- Las especificaciones aprobadas definen qué debe hacer una funcionalidad.
- La documentación de arquitectura define las decisiones técnicas vigentes.
- Las reglas e instrucciones de IA definen cómo trabajar dentro del repositorio.
- Los planes y el roadmap organizan el trabajo pendiente.
- La bitácora registra lo que realmente ocurrió.

Si dos documentos se contradicen, la IA debe identificar el conflicto, consultar la fuente correspondiente y no elegir arbitrariamente una versión.

Las instrucciones globales deben ser breves y remitir a la documentación específica. No copies toda la documentación dentro de `CLAUDE.md` o `AGENTS.md`.

## 5. Adaptar los archivos de instrucciones de IA

Revisa y actualiza los archivos de instrucciones que correspondan a las herramientas realmente utilizadas.

### CLAUDE.md

Debe explicar las instrucciones esenciales para Claude Code:

- Objetivo general y estructura del repositorio.
- Enlaces a las especificaciones y documentación principales.
- Flujo obligatorio de SDD.
- Comandos de desarrollo, pruebas y validación que existan realmente.
- Convenciones de código y restricciones importantes.
- Criterios para decidir cuándo consultar agentes, skills o comandos.
- Obligación de actualizar la documentación afectada y la bitácora.

Mantén este archivo conciso. Los detalles especializados deben residir en reglas, skills o documentos específicos.

### AGENTS.md

Si el proyecto utiliza agentes compatibles con este archivo, define las instrucciones comunes para trabajar en el repositorio.

Incluye el flujo SDD, la consulta de especificaciones, la verificación de cambios, la protección de funcionalidades existentes y el registro documental.

Evita mantener copias completas de `CLAUDE.md` y `AGENTS.md`. Comparte los principios comunes y conserva las particularidades de cada herramienta en su archivo correspondiente.

Si el proyecto no utiliza alguna de estas herramientas, no agregues archivos innecesarios únicamente por seguir esta plantilla.

## 6. Integrar SDD con rules, skills, agentes y commands

Audita los mecanismos disponibles y adapta cada uno a una responsabilidad concreta.

**Rules**
- Definir restricciones permanentes y convenciones específicas.
- Establecer reglas para código, pruebas, seguridad y documentación según las necesidades reales.
- Evitar repetir instrucciones generales en todas las reglas.

**Skills**
- Crear o adaptar una skill para el flujo SDD.
- Incluir instrucciones para especificar requisitos, planificar, implementar y verificar cambios.
- Crear skills especializadas solo cuando una tarea recurrente lo justifique.
- Indicar qué documentación debe consultarse y qué resultados se esperan.

**Agentes**
- Identificar qué tareas pueden delegarse a agentes especializados.
- Definir sus responsabilidades, entradas, resultados esperados y límites.
- Favorecer la revisión independiente de código, pruebas y cumplimiento de especificaciones cuando aporte valor.
- No delegar decisiones de arquitectura o cambios de alcance sin los controles correspondientes.

**Commands**
- Crear comandos reutilizables para iniciar una especificación, generar un plan, implementar una tarea aprobada, verificar el cumplimiento y registrar resultados.
- Reutilizar las capacidades existentes antes de crear comandos nuevos.
- Asegurar que cada comando tenga una función clara, entradas definidas y un resultado verificable.

Respeta la sintaxis, las ubicaciones y las convenciones de la herramienta utilizada. No inventes formatos de configuración ni nombres de mecanismos que no sean compatibles con el entorno real.

## 7. Crear una bitácora de cambios

Crea o adapta `docs/logs/BITACORA.md`.

La IA deberá actualizarla al finalizar cada unidad de trabajo significativa, como una funcionalidad, corrección, refactorización o cambio documental importante.

Cada entrada debe incluir:

- Fecha y hora, cuando estén disponibles.
- Identificador de la especificación o tarea relacionada.
- Objetivo del cambio.
- Archivos y módulos afectados.
- Resumen de lo realizado.
- Pruebas y validaciones ejecutadas.
- Resultado de las pruebas.
- Decisiones tomadas y motivos relevantes.
- Problemas conocidos, riesgos o tareas pendientes.

No registres como completado algo que no se haya implementado o verificado. Distingue las pruebas ejecutadas de las que no pudieron ejecutarse. Evita almacenar secretos, credenciales o información sensible.

Mantén la bitácora legible y cronológica. No reescribas las entradas históricas para aparentar que el trabajo se hizo de otra manera.

## 8. Crear un roadmap de principio a fin

Crea o adapta `docs/roadmap/ROADMAP.md` para reflejar el estado real del proyecto.

Organiza el trabajo por fases, hitos y tareas dependientes. Incluye:

- Fase y objetivo.
- Tareas necesarias.
- Dependencias.
- Prioridad.
- Criterios de aceptación.
- Pruebas requeridas.
- Estado: pendiente, en progreso, bloqueado o completado.
- Referencias a especificaciones y documentación relacionadas.

El roadmap debe abarcar desde la preparación del proyecto hasta la implementación, pruebas, despliegue, documentación final y mantenimiento, según corresponda al proyecto.

Primero identifica lo que ya está realizado. No marques tareas como completadas basándote únicamente en la existencia de archivos o en suposiciones. Señala las incertidumbres y no inventes fechas de entrega.

Actualiza el roadmap cuando cambien las prioridades o se complete un hito, explicando las modificaciones importantes.

## 9. Plantillas de especificación

Prepara una plantilla reutilizable que permita a la IA y al equipo definir cada cambio con:

- Identificador y nombre.
- Contexto y problema.
- Objetivo y alcance.
- Requisitos funcionales y no funcionales, cuando correspondan.
- Restricciones y dependencias.
- Criterios de aceptación verificables.
- Casos límite y errores esperados.
- Archivos o módulos potencialmente afectados.
- Estrategia de pruebas.
- Plan de implementación.
- Riesgos y preguntas pendientes.

Cada especificación debe tener un estado claro, por ejemplo: borrador, en revisión, aprobada, implementada o verificada. La IA no debe tratar un borrador como autorización para realizar cambios de gran alcance.

## 10. Reglas de trabajo para la IA

Incorpora un procedimiento de trabajo que establezca que la IA debe:

1. Consultar las instrucciones relevantes antes de modificar código.
2. Identificar la especificación aplicable o proponer una cuando no exista.
3. Confirmar el alcance y los criterios de aceptación.
4. Elaborar un plan proporcional a la complejidad del cambio.
5. Implementar en pasos pequeños, manteniendo la coherencia con la arquitectura vigente.
6. Ejecutar pruebas y comprobaciones de calidad disponibles.
7. Revisar regresiones, seguridad y efectos sobre otros módulos.
8. Actualizar especificaciones, documentación, roadmap y bitácora cuando corresponda.
9. Informar qué cambió, qué se verificó, qué no pudo verificarse y qué queda pendiente.

No obligues a crear una especificación extensa para cambios triviales. Tampoco permitas que un cambio complejo se ejecute sin planificación suficiente.

Si falta información esencial, hay contradicciones o una decisión implica ampliar el alcance, documenta el problema y solicita aclaración cuando sea necesario.

## 11. Validación final

Después de implementar esta metodología:

- Comprueba que los archivos creados estén enlazados correctamente.
- Verifica que las instrucciones no se contradigan.
- Confirma que las rutas y los comandos mencionados existan.
- Prueba los comandos o flujos nuevos cuando sea posible.
- Comprueba que el proceso SDD se pueda seguir de principio a fin.
- Actualiza el roadmap y la bitácora con el trabajo real realizado.
- Conserva los cambios previos del proyecto y no elimines información útil.

## Entregables esperados

Al finalizar, presenta un resumen con:

1. Diagnóstico inicial del repositorio.
2. Archivos creados, modificados y conservados.
3. Estructura documental final y propósito de cada sección.
4. Cambios aplicados a `CLAUDE.md`, `AGENTS.md`, rules, skills, agentes y commands.
5. Roadmap inicial basado en el estado real del proyecto.
6. Bitácora con el registro de esta intervención.
7. Pruebas y validaciones ejecutadas.
8. Instrucciones para que el equipo utilice el flujo SDD diariamente.
9. Limitaciones, decisiones pendientes y siguientes pasos.

**Criterio de éxito:** cualquier agente de IA que trabaje en el repositorio debe poder identificar qué se quiere construir, consultar la especificación correcta, seguir un plan, implementar sin desviarse de las decisiones vigentes, verificar su trabajo y dejar un registro comprensible para el siguiente integrante del equipo.

Empieza por la auditoría. Después implementa la estructura y los cambios necesarios de forma incremental. No te limites a proponer recomendaciones: realiza los cambios pertinentes en el repositorio, valida lo que puedas y presenta los resultados reales sin afirmar que hiciste tareas que no ejecutaste.