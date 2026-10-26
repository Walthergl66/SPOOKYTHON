# Estado actual y punto de reanudación

Última actualización: 2026-10-26. Último cambio: **CAM-005**, en [cambios.md](cambios.md).

## Hechos verificados

- Nombre oficial elegido por el usuario: **Navira**. Documentación vigente y paquete backend previsto `src/navira/` actualizados; decisión ADR-006. El directorio local sigue siendo `SPOOKYTHON`.

- Existe documentación modular en `doc/`, README raíz y protocolo de incorporación en `AGENTS.md`.
- El plan anterior se conserva como referencia histórica. La ubicación antigua `docs/PLAN_IMPLEMENTACION.md` ya no existe en el árbol comprobado; la fuente vigente es `doc/plan-implementacion.md`.
- Están documentados dos modos y los límites de la primera versión.
- Se conserva una copia local del reto proporcionado por el usuario.
- Existe `scripts/check_docs.py`, una utilidad de documentación con biblioteca estándar de Python; no es código de la aplicación.
- Existen PRD, TRD, ODDD (OO + DDD confirmado por el usuario), SDD, seis SPEC y matriz de trazabilidad. SPEC-006 verifica incorporación metodológica; SPEC-001 a SPEC-005 siguen sin implementación funcional.
- Existe `scripts/check_sdd.py` con ocho pruebas de regresión en `tests/test_check_sdd.py`; son utilidades/pruebas documentales, no la aplicación.

## Verificación histórica de CAM-003

- `python3 scripts/check_docs.py`: correcto, 35 Markdown en `doc/` y 38 archivos Markdown comprobados; sin enlaces locales inexistentes ni documentos inaccesibles desde el índice.
- Copia del reto: comparada íntegramente con el adjunto del usuario; coincide.
- Sintaxis del comprobador: validada con `ast.parse`.
- Alcance: no se comprobaron URLs externas, renderizado, aplicación, despliegue ni costos reales.

## Verificación de CAM-004

Comprobación documental y SDD correctas: 52 Markdown en `doc/`, 54 archivos comprobados, seis SPEC y 22 requisitos identificados. SPEC-006 verificada; las otras cinco continúan listas, sin código. Ocho regresiones ejecutadas correctamente y comando enfocado a SPEC-004 comprobado. Propuesta SDD preservada íntegramente. Revisión, comandos, conteo por pasada y límites en [evidencia](resultados/verificacion-sdd.md).

## Verificación de CAM-005

`python3 scripts/check_docs.py` correcto: 53 Markdown en `doc/` y 55 archivos comprobados. `python3 scripts/check_sdd.py` correcto: seis especificaciones mantienen su trazabilidad y estado. Búsqueda de nombres revisada: la denominación anterior solo permanece en antecedentes explícitos y referencia histórica. No cambian scripts ni comportamiento funcional, por lo que no se añaden pruebas de aplicación.

## Lo que todavía no existe o no está verificado

| Área | Estado | Evidencia pendiente |
|---|---|---|
| Backend y `/paso` | Pendiente | Código, pruebas y respuesta HTTP real. |
| Simulador | Pendiente | Turnos y escenarios ejecutados. |
| Grafo de Manta | Pendiente | Exportación y validación. |
| Frontend y juego | Pendiente | Compilación y recorrido de usuario. |
| Infraestructura AWS | Pendiente | Recursos, URL y comprobación de salud. |
| Budget con alerta | No verificado | Captura y configuración real. |
| Rendimiento/supervivencia | Sin medir | Reportes de las tres rondas. |
| Repositorio remoto y commits | No verificado | URL y comprobación del historial. |

La existencia de un directorio `.git` no demuestra que haya un repositorio operativo o publicado. No se han creado commits ni se ha desplegado nada en esta tarea documental.

## Próxima acción concreta

Empezar **P0-01** y **P0-02** de [plan de implementación](plan-implementacion.md) con [SPEC-002](especificaciones/SPEC-002-motor-paso.md), PRD/TRD y modelo ODDD: inspeccionar herramientas disponibles, crear base mínima de Python/FastAPI y fijar esquemas/fixtures de contratos. Preparar frontend y despliegue mínimo después de esa base. Configurar el Budget en cuanto haya acceso autorizado a AWS; no posponerlo hasta la demo.

Comandos documentales confirmados: `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py` y `python3 -m unittest discover -s tests -p 'test_check_sdd.py'`. No hay comandos de desarrollo de aplicación confirmados todavía. Cuando se creen, registrarlos aquí y en el README junto con sus versiones y resultados, sin confundir ejemplos previstos con comandos ejecutados.

## Dependencias externas

Confirmación de región y reglas pendientes; acceso AWS y repositorio remoto no comprobados. Estas dependencias no impiden empezar el núcleo local. No pedir secretos en el chat ni guardarlos en Markdown.

## Trabajo en curso y transferencia

Ninguna implementación de aplicación iniciada. La metodología documental está incorporada y comprobada; el nombre a usar es Navira. Siguiente agente: leer `AGENTS.md`, revisar `doc/`, elegir SPEC y contrastar este estado contra los archivos antes de actuar. Si encuentra cambios posteriores a CAM-005, inspeccionarlos y actualizar este resumen, sin sobrescribir trabajo ajeno.
