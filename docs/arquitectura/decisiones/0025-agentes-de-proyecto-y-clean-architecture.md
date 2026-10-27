# ADR-025 — Subagentes de proyecto y Clean Architecture como destino

Fecha: 2026-10-26 (Ecuador continental).
Estado: aceptada para diseño; la guía y los subagentes existen, el código aún no cumple la guía (CAM-066).
Origen: el usuario pidió subagentes de proyecto para desarrollar más rápido y una guía para armar backend y frontend en Clean Architecture. Dijo primero que se hiciera sin tocar código, con los subagentes y la guía, y que se preguntara lo que faltara.

## Contexto y restricciones

- [ADR-023](0023-configuracion-de-agentes.md) dejó dicho que no se configuraba ningún subagente. Esta decisión lo completa.
- Solo `planner` e `implementer` de los globales leen el `CLAUDE.md` del proyecto; `software-architect` y `code-reviewer` no. Sin subagentes de proyecto, las revisiones de arquitectura no tienen contexto de Navira.
- La exploración de 2026-10-26 encontró violaciones de la regla de dependencias en el backend (una dura) y en el frontend (una llamada de red en un componente). Están en la línea base de [la guía](../guia-clean-architecture.md).
- No hay pruebas ni lint en el frontend, así que una migración de lógica de negocio no tiene red de seguridad automática.
- `AGENTS.md` exige ADR para cambios duraderos de arquitectura.

## Decisión

1. Cuatro subagentes de proyecto en `.claude/agents/`:
   - `arquitecto-backend` y `arquitecto-frontend`: Opus, solo lectura. Diagnostican y proponen pasos.
   - `revisor-arquitectura`: Sonnet, solo lectura. Ejecuta las búsquedas de la guía y compara con la línea base.
   - `documentador-sdd`: Sonnet. Registra el cambio en la documentación y ejecuta los validadores; no toca código.
2. La guía canónica está en `docs/arquitectura/guia-clean-architecture.md`, con la regla de dependencia, las capas objetivo, la línea base y los pasos de migración B1–B6 y F1–F6.
3. La skill `navira-clean-architecture` enlaza la guía y define el flujo de un paso de migración. No duplica su contenido.
4. Ningún paso de migración se hace dentro de la configuración de agentes. Cada paso es un cambio propio con su CAM.

## Alternativas consideradas

- **Solo la skill, sin subagentes:** descartada; no separa el diagnóstico (lectura) de la edición y no aporta contexto de proyecto a los revisores.
- **Un único subagente de arquitectura para backend y frontend:** descartado; las reglas y los archivos de cada lado son distintos y mezclarlos reduce la profundidad.
- **Opus también en el revisor:** descartado; la comprobación es mecánica y se apoya en búsquedas reproducibles.
- **Migrar el código en esta misma decisión:** descartado por instrucción del usuario, que pidió hacerlo primero sin tocar código.

## Consecuencias, límites y costos

- Los subagentes de `.claude/agents/` se cargan al iniciar una sesión. Su carga real no se comprobó en la sesión donde se crearon.
- Opus tiene mayor coste por llamada. Si el coste pesa, bajar `arquitecto-*` a Sonnet cambiando el campo `model`.
- Los subagentes con `Bash` deben usar `env PYTHONDONTWRITEBYTECODE=1` al ejecutar Python: `__pycache__` está versionado en git.
- La guía describe un destino. No afirma que el código actual cumpla Clean Architecture.

## Supuestos y pendientes relacionados

- F6 (pruebas unitarias y lint del frontend) es una decisión aparte que requiere aprobación del usuario.
- Dejar de versionar `__pycache__` es una decisión aparte; no se incluye aquí.

## Documentos y módulos propietarios afectados

`docs/arquitectura/guia-clean-architecture.md` (nuevo), `.claude/agents/` (nuevo), `.claude/skills/navira-clean-architecture/` (nuevo), `docs/metodo/SDD.md` (enlace en la línea 59), `docs/arquitectura/decisiones/0023-configuracion-de-agentes.md` (completado por esta decisión), `.claude/rules/backend-capas.md`, `.claude/rules/frontend-panel.md`, `.agents/` y `CLAUDE.md` (enlaces a la guía).

## Evidencia de implementación/verificación

CAM-066: archivos creados, validadores documentales y comprobación de enlaces. La carga de los subagentes en una sesión nueva queda pendiente.

## Sustituye / sustituida por

Completa [ADR-023](0023-configuracion-de-agentes.md) en el punto sobre subagentes; no sustituye nada más.
