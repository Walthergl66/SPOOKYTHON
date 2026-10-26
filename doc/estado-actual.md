# Estado actual y punto de reanudación

Última actualización: 2026-10-26. Último cambio: **CAM-008**, en [cambios.md](cambios.md).

## Hechos verificados

- Nombre oficial elegido por el usuario: **Navira**. Documentación vigente y paquete backend previsto `src/navira/` actualizados; decisión ADR-006. El directorio local sigue siendo `SPOOKYTHON`.

- Existe documentación modular en `doc/`, README raíz y protocolo de incorporación en `AGENTS.md`.
- El plan anterior se conserva como referencia histórica. La ubicación antigua `docs/PLAN_IMPLEMENTACION.md` ya no existe en el árbol comprobado; la fuente vigente es `doc/plan-implementacion.md`.
- Están documentados dos modos y los límites de la primera versión.
- Se conserva una copia local del reto proporcionado por el usuario.
- Existe `scripts/check_docs.py`, una utilidad de documentación con biblioteca estándar de Python; no es código de la aplicación.
- Existen PRD, TRD, ODDD (OO + DDD confirmado por el usuario), SDD, seis SPEC y matriz de trazabilidad. SPEC-006 verifica incorporación metodológica; SPEC-001 y SPEC-002 tienen implementación parcial sin verificación completa.
- Existe `scripts/check_sdd.py` con ocho pruebas de regresión en `tests/test_check_sdd.py`; son utilidades/pruebas documentales, no la aplicación.
- En `feat/navira-backend-base` existe la base FastAPI en `src/navira/`, `/salud`, `/paso` con autenticación y esquemas, y fixtures de contrato/mapa. El endpoint usa temporalmente una política de espera determinista; todavía no hay cálculo de rutas.
- En `feat/navira-map-graph` existe `src/navira/domain/mapa.py`: modelo de nodo/calle/refugio, carga JSON, adyacencia dirigida y validación de cierres por arista/segmento. Diez pruebas de dominio pasan. El fixture es sintético y no representa Manta.
- En `feat/navira-world-model` existe `src/navira/domain/modelo.py`: partida con modo/turno/fase fijos, sobrevivientes, zombies e intención ligada a su partida y fase. Siete pruebas pasan; todavía no hay resolutor de movimiento.

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
| Backend y `/paso` | Base implementada, arranque sin verificar | Instalar dependencias, ejecutar HTTP y completar pruebas de contrato; conectar planificador después. |
| Simulador | Pendiente | Turnos y escenarios ejecutados. |
| Grafo de Manta | Modelo genérico implementado; dataset pendiente | Área y exportación reproducible de OpenStreetMap con unas 300 intersecciones y cuatro refugios. |
| Frontend y juego | Pendiente | Compilación y recorrido de usuario. |
| Infraestructura AWS | Pendiente | Recursos, URL y comprobación de salud. |
| Budget con alerta | No verificado | Captura y configuración real. |
| Rendimiento/supervivencia | Sin medir | Reportes de las tres rondas. |
| Repositorio remoto y commits | No verificado | URL y comprobación del historial. |

El repositorio local tiene un remoto Git configurado. CAM-006 conserva la base del backend en su commit y rama; CAM-007 está en curso en una rama distinta. No se han publicado las ramas al remoto; el despliegue AWS sigue pendiente.

## Próxima acción concreta

Completar P1-01 desde `feat/navira-map-graph` con datos geográficos reproducibles y barrios/refugios reales; luego añadir entidades/intenciones y simulación según [SPEC-001](especificaciones/SPEC-001-mundo-simulacion.md). P0-01/P0-02 también requieren ejecutar y comprobar el endpoint HTTP antes de marcarlos verificados. No presentar la espera inicial como planificador. Configurar Budget cuando se disponga de acceso AWS autorizado.

Comandos documentales confirmados: `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py` y `python3 -m unittest discover -s tests -p 'test_check_sdd.py'`. `python -m pip install -e .` completó en el entorno temporal `/tmp/navira-env`; el comando de arranque del README aún no se ha ejecutado. Cuando se verifique, registrar versiones y resultados, sin confundir comandos previstos con ejecutados.

## Dependencias externas

Confirmación de región y reglas pendientes; acceso AWS y repositorio remoto no comprobados. Estas dependencias no impiden empezar el núcleo local. No pedir secretos en el chat ni guardarlos en Markdown.

## Trabajo en curso y transferencia

La base de API quedó en CAM-006; el modelo del mapa sigue parcial en CAM-007; entidades e intenciones siguen parciales en CAM-008. La rama actual es `feat/navira-world-model`. Continuar desde ella y mantener P1-01/P1-02 en curso hasta completar mapa real y resolver movimientos. Si hay cambios posteriores a CAM-008, inspeccionarlos antes de editar.
