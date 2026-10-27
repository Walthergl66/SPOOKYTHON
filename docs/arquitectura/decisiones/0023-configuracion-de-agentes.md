# ADR-023 — Configuración de agentes: .claude/ y .agents/

Fecha: 2026-10-26 (Ecuador continental).
Estado: aceptada e implementada localmente (CAM-064).
Origen: el usuario pidió reglas, skills y comandos para mejorar el juego, la arquitectura y las mejoras completas, un `CLAUDE.md` y guías por carpeta con su propia carpeta `.agents/`.

## Contexto y restricciones

- `docs/metodo/SDD.md` indicaba: «No se crean hooks, skills, subagentes o archivos para otras herramientas sin una necesidad real».
- El usuario ha pedido explícitamente esa configuración, lo que constituye la necesidad real.
- Las guías por carpeta dentro de `src/navira/`, `frontend/`, `tests/` y `scripts/` no son el lugar adecuado: el usuario pidió concentrarlas fuera de cada carpeta de código.
- Las reglas de Claude Code se aplican según rutas de archivo; las guías de texto requieren que el agente las lea.

## Decisión

1. `CLAUDE.md` en la raíz importa `AGENTS.md` y añade solo lo específico de Claude Code. No duplica contratos.
2. `.agents/` contiene una guía por área de código (`backend.md`, `frontend.md`, `pruebas.md`, `scripts.md`) y su índice `README.md`. Cada guía enlaza a `docs/` como fuente.
3. `.claude/rules/` contiene reglas con `paths:` para dominio, backend, frontend, pruebas y documentación.
4. `.claude/skills/` contiene tres procesos: cambio SDD, cambios de juego y verificación.
5. `.claude/commands/` contiene tres comandos: arrancar el proyecto, verificar y registrar un cambio.

Ningún hook ni subagente se configura en esta decisión.

## Alternativas consideradas

- **Un `AGENTS.md` por carpeta de código:** lo pidió el usuario en un primer momento, pero se desechó para no mezclar instrucciones con el código.
- **Todo en `AGENTS.md` raíz:** mezcla reglas de juego, pruebas y frontend; no se carga por área.
- **Configuración en la carpeta global del usuario:** descartada, porque las reglas son específicas de este proyecto.

## Consecuencias, límites y costos

- Claude Code no carga `.agents/` automáticamente; las guías se leen cuando las cita una regla, un comando, una skill o el usuario.
- Las reglas de `.claude/rules/` apuntan a `docs/` y a las guías de `.agents/`; si un documento se mueve, hay que actualizar esos enlaces.
- La configuración no se ha probado en una sesión nueva de Claude Code en esta conversación; su carga real queda por comprobar.

## Supuestos y pendientes relacionados

- Las reglas de `.claude/rules/` no están probadas con un parser YAML completo; se comprobó el formato a mano y que los enlaces apuntan a archivos existentes.

## Documentos y módulos propietarios afectados

`CLAUDE.md`, `AGENTS.md`, `.agents/`, `.claude/`, `docs/metodo/SDD.md` (la frase citada se completa con este ADR).

## Evidencia de implementación/verificación

CAM-064: validadores documentales correctos y comprobación de enlaces de la configuración sin enlaces rotos.

## Sustituye / sustituida por

Completa la frase de `docs/metodo/SDD.md` sobre skills y subagentes; no sustituye el resto del procedimiento SDD.
