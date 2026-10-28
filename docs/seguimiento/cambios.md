## CAM-130 — Aplicar el puente de R2 desde el inicio

- Fecha: 2026-10-28, America/Guayaquil.
- Solicitud o problema de origen: el usuario informó que el incidente del puente no se habilitaba correctamente en la ronda R2.
- Relación: SPEC-009/CA-009-03, ADR-048, P-15 y T-47.
- Motivo del cambio: R2 programaba el cierre para el turno 50 (aprox. 100 s); una ronda que terminara antes no publicaría el incidente ni calcularía rutas considerando el puente colapsado.
- Resultado: R2 programa el puente determinístico en turno 0; la preparación inicial lo aplica antes de la primera decisión, movimiento de habitantes o proyección del panel. R3 conserva sus cierres provisionales en vivo en turnos 50/100. La UI describe ambos calendarios sin llamar oficial al turno.
- Archivos: `backend/src/navira/simulation/escenarios.py`, `backend/tests/test_demo.py`, `backend/tests/test_panel.py`, `frontend/src/app/App.tsx`, SPEC-009, reglas, T-47, pendientes, ADR-048, índices, estado e historial.
- Verificación ejecutada: dos pruebas focalizadas (`test_presets_de_reto_respetan_tipos_y_eventos_reproducibles`, que prueba turno 0 y aplicación, y `test_reto_r2_publica_el_puente_cerrado_desde_la_primera_decision`, que comprueba alerta de panel, tipo puente y segmento bloqueado) pasan (2/2, 31.874 s). `git diff --check` pasa antes de actualizar esta CAM.
- Verificación pendiente: suites completas backend/frontend, build y validadores docs/SDD por ejecutar.
- Límites: la organización no define el turno del colapso. Turno 0 es la interpretación local de “puente colapsado” como condición inicial, documentada y revisable. No se ha desplegado ni reiniciado la demo pública.
- Siguiente acción concreta: ejecutar las suites afectadas y validadores; luego actualizar el resultado en CAM/estado.
- Commit o PR: ninguno creado.

## CAM-129 — Automatizar la actualización de Lightsail desde GitHub Actions

- Fecha: 2026-10-28, America/Guayaquil.
- Solicitud o problema de origen: el usuario preguntó si podía haber una conexión con GitHub que actualice el despliegue y pidió implementarla.
- Especificación, requisitos, criterios CA y tareas relacionados: SPEC-005, SPEC-011; P0-04/P5-02; ADR-047.
- Motivo del cambio: reducir publicación manual y asegurar que el deploy solo ocurra después de CI en el commit exacto.
- Alcance y comportamiento resultante: CI ahora ofrece job `Deploy to Lightsail` solo para `master` y `workflow_dispatch` en `master`, después de backend/frontend; imágenes por SHA; transferencia SSH con host key fijada; script remoto preserva env servidor, comprueba configuración del perfil público, hace health checks local y restaura imágenes anteriores si falla. Acción posterior valida salud/UI pública.
- Archivos y documentos propietarios afectados: `.github/workflows/ci.yml`, `deploy/lightsail/deploy-release.sh`, ADR-047, infraestructura, seguridad, guía paso a paso, SPEC-005/SPEC-011, índices, plan y estado actual.
- Decisiones/ADR relacionadas o motivo por el que no requiere ADR: ADR-047 registra la topología automatizada, seguridad del canal, rollback y límites de estado volátil.
- Validación ejecutada: `bash -n deploy/lightsail/deploy-release.sh`; `python3 -c 'import yaml; yaml.safe_load(...)'` parseó el workflow; `python3 backend/scripts/check_docs.py` (140 Markdown/142 archivos), `python3 backend/scripts/check_sdd.py` (11 SPEC), `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py' -v` (8/8), `git diff --check` pasan.
- Validación no ejecutada y causa: `actionlint` no está instalado; no se ejecutaron suites de aplicación porque solo cambian CI/deploy/docs. No se ejecutó GitHub Actions ni Lightsail desde esta tarea; faltan secrets/variable y la regla SSH actual solo permite IP administrativa, no runners hospedados. No se abrió la regla del firewall.
- Limitaciones, riesgos y pendientes con ID: P-21: confirmar método de conectividad segura para runner GitHub; primer run/rollback remoto; prueba de pérdida de partidas al reiniciar es comportamiento previsto por SPEC-011. No exponer SSH globalmente.
- Estado real al cerrar: implementación local preparada; automatización remota no activa hasta configurar acceso y secrets en GitHub.
- Siguiente acción concreta: configurar secrets/variable del repositorio y decidir una ruta de red compatible con firewall restringido; validar el fingerprint SSH desde un canal confiable y observar el primer workflow en `master`.
- Commit o PR: ninguno creado.

## CAM-128 — Enrutar Jugar en el proxy y verificar los tres modos públicos

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el smoke HTTPS de CAM-127 encontró que el Nginx de frontend no reenviaba `/juego/`; el usuario autorizó despliegue público y actualización de la aplicación.
- Relación: PRD-13, TRD-19, SPEC-011; P4-07/P5-02; ADR-046; CAM-126/127.
- Resultado: Nginx de frontend reenvía `/juego/` al backend; se desplegó `navira-frontend:public-128` junto al backend `navira-backend:public-127`. La URL [https://3.17.253.59.nip.io](https://3.17.253.59.nip.io) entrega UI por TLS. Smoke HTTPS recorrió Jugar y Reto en una sesión, Simulador en otra; observó tres `runId` diferentes, `Secure`/`HttpOnly` en cookie y rechazo 403 a Origin ajeno. `GET /panel/estado` conservó el run esperado; browser accessibility snapshot mostró selector Reto/Simulador/Jugar, Reto listo y panel “En vivo”. La capacidad se reinició al terminar smoke para liberar cookies de prueba; quedó abierta una sesión limpia de navegador.
- Archivos: `deploy/lightsail/nginx.conf`, SPEC-011, T-58, infraestructura y este historial.
- Verificación: build frontend y 99 pruebas pasan; imagen frontend construida con Podman y `nginx -t` pasa; suite backend 245/245; health HTTPS, multisesión/modos, cookie/origen y panel pasan externamente. El intento de publicar otra etiqueta ECR fue denegado (`ecr:GetAuthorizationToken`); se transfirió la imagen por SSH a Lightsail y se ejecutó como contenedor con reinicio automático.
- Límites: solo se verificó una carga manual con dos sesiones; no es prueba de carga/abuso o SLA. Lightsail es un solo proceso/worker con estado volátil y límite de tres sesiones. `aws lightsail:GetInstance` está denegado a la CLI, así que no se pudo confirmar control-plane ni factura. La URL usa nip.io, no dominio propio.
- Siguiente paso exacto: revisar visualmente el modo Jugar en la pestaña pública; monitorear el límite de sesiones y cargos; al concluir los tres días, detener/eliminar la instancia y revisar la Static IP.
- Commit o PR: `0bc8b65`; imágenes runtime construidas desde `3b2efce` (`backend public-127`, `frontend public-128`).

## CAM-127 — Habilitar los tres modos en la demo pública y publicar la revisión

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario quiere que cualquier visitante pueda probar Reto, Simulador y Jugar; mantuvo autorización para modificar, hacer commit y desplegar públicamente.
- Relación: PRD-13, TRD-19, SPEC-011; P4-07/P5-02; ADR-046; CAM-126.
- Resultado: las sesiones públicas crean un contexto Jugar aislado de forma diferida y los endpoints de Juego/panel/órdenes resuelven servicios por cookie; el reloj empieza tras la aparición y se detiene al cambiar al modo automático. El smoke ASGI recorrió Juego → Reto y dejó otro navegador en Simulador con un `runId` distinto. La aparición humana usa un campo inverso de rutas para evitar una búsqueda Dijkstra completa por cada nodo candidato; los tests del campo y de la sesión pasan. Lightsail VM `navira-public-demo` responde en [https://3.17.253.59.nip.io](https://3.17.253.59.nip.io) con certificado Let's Encrypt. La revisión desplegada antes del cierre de esta CAM aún debe reemplazarse con la imagen backend construida desde el commit que incluye Juego público; registrar digest y smoke externo después del reemplazo.
- Archivos: `backend/src/navira/main.py`, `backend/src/navira/application/juego.py`, `backend/src/navira/routing/dijkstra.py`, pruebas de rutas/sesiones; SPEC-011/README, ADR-046, matriz T-58, seguridad, infraestructura, costos, plan y estado.
- Verificación: pruebas focalizadas Dijkstra (10) y sesión humana (12) pasan; prueba ASGI pública de inicio Jugar, cambio a Reto, Simulador en segundo navegador y `runId` aislados pasa; build de imagen/backend y suites completas en ejecución. Primer smoke de HTTPS comprobó índice y `/salud`; falta repetir con la nueva imagen, validar cookie segura y probar WebSocket/modos remotos y revisión visual.
- Límites: la instancia es un proceso único con memoria volátil, límite configurado de tres sesiones y nombre nip.io de tercero; no hay persistencia, bot protection, carga concurrente externa ni métricas CloudWatch validadas. La cuenta deniega `lightsail:GetInstance` a AWS CLI; no se puede confirmar el estado actual desde control plane. El costo sigue siendo aproximado y el Budget es solo alerta.
- Siguiente paso exacto: publicar imagen backend de `3b2efce`, sustituir el contenedor, ejecutar smoke HTTPS de cookie/3 modos/WebSocket y confirmar que Docker/Nginx se recuperan tras reinicio; luego revisar visualmente la URL y preparar retirada de la VM tras los tres días.
- Commit o PR: `dfb630c` y `3b2efce`; publicación de imagen/contendor pendiente de confirmación.

## CAM-126 — Preparar aislamiento anónimo para la demo pública

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario autorizó que personas externas prueben los tres modos con partidas independientes.
- Relación: PRD-13, TRD-19, SPEC-011; P4-07/P5-02; ADR-046.
- Resultado: se implementó registro efímero por token anónimo, hash SHA-256 en servidor, cookie `HttpOnly`/`SameSite=Strict`/`Secure` según HTTPS, máximo configurable de sesiones, TTL, validación Origin y bootstrap frontend. El perfil público mantiene `/paso` cerrado sin API key.
- Archivos: backend sesión/seguridad/dependencias, frontend bootstrap/estado de capacidad, imágenes Docker/Nginx y documentación de SPEC-011/ADR-046.
- Verificación: pruebas focalizadas de aislamiento, límite, TTL y cierre; pruebas previas del control local; suite frontend y build; imágenes construidas con Podman, `nginx -t`, smoke local de salud y dos controles simulador con `runId` independientes. Las evidencias no incluían aún Jugar público ni un smoke HTTPS externo.
- Límites: el primer perfil público enrutaba solo los controles de simulación; Jugar público se completa en CAM-127. La sesión es temporal de un proceso, y no había una URL pública hasta el despliegue Lightsail de CAM-127.
- Siguiente paso exacto: conectar el servicio de Jugar a la sesión anónima antes de ofrecer los tres modos públicamente; ejecutado parcialmente en CAM-127.
- Commit o PR: `1186c4d`, `4be7659`, `20bf1e3`, `5bfdca1`, `b3bd38a`.

## CAM-125 — Desplegar y ejecutar campaña efímera de evaluación en Ohio

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario autorizó aplicar la infraestructura revisada y completar el despliegue de Navira con urgencia.
- Relación: SPEC-005, P5-02/P5-03; P-06/P-11/P-19/P-20; ADR-045; CAM-116/CAM-124.
- Resultado: se ejecutó el Change Set del runner y quedó un stack ECS/ECR/CloudWatch/IAM/security group. La imagen Debian inicial reveló vulnerabilidades altas/medias/bajas en el escaneo; se sustituyó por `python:3.12-alpine3.24` fijada al digest oficial de Alpine 3.24.3, se reconstruyó y el escaneo del digest publicado no mostró hallazgos. La task definition quedó fijada a imagen por digest con 4 vCPU y 8 GiB. Una tarea Fargate completó R1/R2/R3, terminó con exit code 0 y no quedan tareas activas. Las tres ventanas fueron 300.127/300.103/300.159 s; hubo 22.767 respuestas HTTP 200, cero fallos, evacuados 20/65/171 y mordidos 0/2/2. R1 utilizó 142 turnos activos y ocho slots ociosos; R2/R3 usaron 150. Reporte: [campaña AWS CAM-125](../calidad/resultados/campana-aws-cam125.md).
- Alcance de despliegue: esto despliega el ejecutor efímero de evaluación, no el sitio/app. El intento App Runner fue denegado por política de la organización. No hay frontend público, servicio persistente, ALB, URL, TLS ni almacenamiento durable; conservar la restricción de ADR-045 y no abrir el control local.
- Archivos: `infra/aws/campaign.yml`, reporte CAM-125, SPEC-005, índice de especificaciones, índice general, infraestructura, costos, guía de despliegue, plan, estado, pendientes e historial.
- Verificación: CloudFormation `UPDATE_COMPLETE`; los recursos enumerados incluyen ECR, cluster, logs, roles, SG y task definition. Task `STOPPED`, contenedor exit code 0; `list-tasks` confirmó cero tareas ejecutándose. R1/R2/R3 registraron sus ventanas y solicitudes exitosas en CloudWatch. `cfn-lint` no reportó diagnósticos. La suite backend 240/240 y frontend 99/99/build ya habían pasado en esta preparación; smoke local del contenedor Alpine pasó. Checks documentales y `git diff --check` se ejecutan al cierre de esta actualización.
- Costo: Fargate 4 vCPU/8 GiB por 924.611 s se estima en aproximadamente US$0,051 con las tarifas indicativas de `costos.md`; no es dato de facturación. ECR/logs y otros cargos no están contabilizados. Recursos base permanecen para reuso.
- Límites: el cliente y ASGI corrieron en loopback dentro de la tarea, así que esta medición no representa latencia de Internet/ALB/CloudFront. La ejecución no atribuye un SHA Git porque el checkout estaba sin commits de despliegue. El presupuesto tiene correo `Inactive`; se sigue con monitoreo manual aceptado por el usuario. No es prueba oficial ni verifica elegibilidad/cobertura de crédito.
- Siguiente paso exacto: cerrar el trayecto seguro de publicación que sí permita la organización: confirmar un hosting permitido por política, preparar servicio/staging con TLS y acceso restringido, y medir `/paso` desde un cliente externo. La autorización del usuario para desplegar persiste; no crear un endpoint público inseguro para superar la denegación de App Runner.
- Commit o PR: no creado; cambios locales sin commit.

## CAM-124 — Autenticar AWS CLI y preparar Change Set de campaña

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario confirmó que inició sesión en AWS y mantiene la autorización previa para continuar la preparación del despliegue.
- Relación: SPEC-005, P0-05/P5-02; P-06; CAM-118/121/123.
- Resultado: el perfil local `navira` en `us-east-2` quedó autenticado mediante `aws login`. `aws sts get-caller-identity` confirmó acceso sin registrar identidad, cuenta ni ARN. AWS aceptó `cloudformation:ValidateTemplate` para `infra/aws/campaign.yml`; se creó el Change Set `navira-foundation-review-20261028c` en estado `CREATE_COMPLETE` / `AVAILABLE`. Propone seis altas: repositorio ECR, cluster ECS, grupo de logs CloudWatch, dos roles IAM y un security group. No contiene tarea Fargate porque aún no hay URI inmutable de imagen. `list-stack-resources` devolvió una lista vacía: no se han creado recursos de aplicación. La preparación no incluyó `execute-change-set` ni otras operaciones de creación.
- Configuración auxiliar: el instalador configuró el servidor global `aws-mcp` para Codex. No se instalaron los paquetes de skills opcionales. Esta configuración no sustituye la revisión del Change Set ni equivale a despliegue.
- Archivos: estado actual, pendientes, guía de despliegue, infraestructura e historial.
- Verificación: AWS CLI 2.37.0; `sts get-caller-identity` exitoso sin divulgar resultado sensible; `cloudformation validate-template` exitoso; Change Set consultado y sus seis acciones revisadas; `list-stack-resources` vacío. No hay medición de costo real ni creación de recursos.
- Límites: el Change Set solo describe el runner efímero; no publica la app, no crea API/ALB/frontend, no lanza tareas ni resuelve TLS/dominio. Al ejecutarlo sí se crearían los seis recursos descritos; revisar su compatibilidad con las restricciones/cuotas del Free Plan y presupuesto. La sesión temporal de `aws login` vence; no compartir tokens o archivos de credenciales.
- Siguiente paso (superado por CAM-125): se ejecutó el Change Set autorizado; ver reporte de campaña y bloqueos restantes de publicación.
- Commit o PR: no creado; evidencia local y AWS documentada, pendiente de revisión.

## CAM-123 — Usar inicio CLI de la nueva experiencia AWS

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario aclaró que su cuenta AWS Free/Blank Canvas no permite entrar a IAM Identity Center ni obtener un Start URL; pidió un medio para conectar AWS y continuar la configuración.
- Relación: SPEC-005, P0-05/P5-02; P-06; CAM-122.
- Resultado: la nueva experiencia AWS no requiere configurar un perfil IAM Identity Center para iniciar CLI. La CLI local es `aws-cli/2.37.0`; se inició `aws login --profile navira --region us-east-2` en un perfil nuevo para preservar `default`. El sign-in completado y el acceso posterior se registran en CAM-124.
- Archivos: `docs/seguimiento/estado-actual.md`, `docs/seguimiento/pendientes.md`, guía de despliegue e historial.
- Verificación: versión local AWS CLI 2.37.0; AWS requiere mínimo 2.32.0 para `aws login`. Fuente oficial: [inicio de sesión CLI con credenciales de consola](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html) y [comparación de experiencias de cuenta](https://docs.aws.amazon.com/accounts/latest/reference/sign-up-for-aws.html). CAM-122 queda corregido: no buscar IAM Identity Center Start URL para la nueva experiencia.
- Límites: el inicio de sesión requiere interacción y autorización del usuario en el navegador; AWS indica que credenciales temporales pueden durar hasta 12 horas. La disponibilidad de acciones AWS seguirá sujeta a permisos de proyecto/SCP.
- Siguiente paso: continuar desde CAM-124; no compartir la URL temporal ni datos de identidad.
- Commit o PR: no creado; preparación local sin publicación.

## CAM-122 — Diagnosticar configuración SSO ausente en el perfil CLI

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario intentó renovar la sesión SSO siguiendo CAM-121; AWS CLI reportó ausencia de `sso_start_url` y `sso_region`.
- Relación: SPEC-005, P0-05/P5-02; P-06; CAM-119/CAM-121.
- Resultado: inspección local de `~/.aws/config` confirma que el perfil `default` no tiene configuración SSO ni hay secciones `sso-session`. Se consultó la guía oficial vigente: `aws configure sso --profile default` solicita URL de acceso/issuer, región de IAM Identity Center, cuenta/rol y región CLI. La región SSO corresponde al directorio Identity Center; la región de despliegue sigue siendo Ohio (`us-east-2`).
- Archivos: `docs/seguimiento/estado-actual.md`, `docs/seguimiento/pendientes.md`, `docs/operacion/guia-paso-a-paso-despliegue.md` e historial.
- Verificación: la configuración se inspeccionó mostrando solo presencia/ausencia de campos, sin imprimir URL, cuenta, rol o credenciales. Referencia: [configuración SSO oficial de AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html).
- Límites: no se ejecutó `aws configure sso` porque requiere que el usuario provea el portal y elija cuenta/rol en su flujo interactivo. No se obtuvo una sesión nueva ni se reintentó CloudFormation.
- Nota de vigencia: el consejo inicial de configurar IAM Identity Center se corrigió en CAM-123 tras la aclaración del usuario sobre la nueva experiencia Free/Blank Canvas; seguir `aws login` en CAM-123, no buscar un SSO Start URL para esta cuenta.
- Commit o PR: no creado; guía/documentación local.

## CAM-121 — Reintentar CloudFormation tras el permiso reportado

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario informó que concedió permiso a CloudFormation y pidió continuar.
- Relación: SPEC-005, P0-05/P5-02; ADR-045; P-06/P-19; CAM-119/CAM-120.
- Resultado: con el perfil CLI `default`, AWS volvió a denegar `cloudformation:DescribeStacks` y `cloudformation:CreateChangeSet` (`AccessDenied`), incluso al usar un nombre de stack nuevo. El usuario puede haber concedido la política en consola, pero el permiso efectivo en esta sesión no está demostrado. No se creó Change Set ni recurso AWS.
- Archivos: `docs/seguimiento/estado-actual.md`, `docs/seguimiento/pendientes.md`, `docs/operacion/infraestructura.md`, guía de despliegue e historial.
- Verificación: reintento de lectura de stack y solicitud de Change Set en `us-east-2`; ambos fueron rechazados por AWS. Ningún Change Set se ejecutó.
- Límites: el resultado refleja el principal/sesión CLI actual; no prueba qué política fue editada en consola ni si una política superior (SCP/permissions boundary) bloquea la acción.
- Siguiente paso: renovar la sesión SSO del perfil `default` (`aws sso logout --profile default` y `aws sso login --profile default`) y reintentar. Si persiste, pedir al administrador que compruebe `cloudformation:DescribeStacks`, `cloudformation:CreateChangeSet`, `cloudformation:DescribeChangeSet`, `cloudformation:ValidateTemplate` y la identidad/rol que usa ese perfil; revisar SCP y permissions boundary. Mantener separados la autorización de Change Set y cualquier ejecución posterior.
- Commit o PR: no creado; preparación local sin publicación.

## CAM-120 — Aceptar limitación de correo Budget y registrar plan gratuito

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: aclaración del usuario y captura de AWS Billing; solicita dar por aceptado el tema de confirmación de correo y continuar con despliegue en su cuenta Free Plan.
- Relación: SPEC-005, P0-03/P0-05; P-06; CAM-117/CAM-119.
- Resultado: para el plan del proyecto se acepta que el Budget y sus tres alertas están configurados; el usuario autoriza continuar sin confirmación de correo y con seguimiento manual del gasto. La captura actual muestra el destinatario con estado **Inactive**, tres alertas (50/80/100 %) y ninguna acción asociada; por ello no se declara el email verificado ni se presume entrega. La captura del panel de cuenta compartida por el usuario indica US$120 de créditos, US$0 por pagar, 177 días restantes y fin del plan el 2027-04-21. Es evidencia visual aportada por el usuario, no lectura directa de AWS CLI.
- Archivos: `docs/seguimiento/estado-actual.md`, `docs/seguimiento/pendientes.md`, `docs/operacion/costos.md`, `docs/operacion/infraestructura.md`, guía de despliegue e historial.
- Verificación: la documentación oficial indica que los destinatarios Budget `Inactive` aún no reciben notificaciones, que el Free Plan tiene acceso solo a servicios/características seleccionados y finaliza a los seis meses o al agotarse créditos, lo que ocurra primero. CloudFormation, ECS y ECR figuran entre servicios admitidos de la nueva experiencia, sujeto a sus límites y permisos. Referencias: [verificación de destinatarios Budget](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-email-recipients.html), [planes Free/Paid](https://docs.aws.amazon.com/us_en/awsaccountbilling/latest/aboutv2/free-tier-plans.html), [servicios admitidos en la nueva experiencia](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html).
- Límites: un saldo de créditos no prueba que cada característica, cuota o recurso esté disponible ni garantiza cobertura universal; confirmar antes del Change Set. El usuario acepta monitoreo manual por falta de verificación del destinatario. No se crearon recursos.
- Siguiente paso: continuar con el bloqueo IAM CloudFormation registrado en CAM-119; cuando el acceso funcione, validar la plantilla, generar y revisar el Change Set y contrastar el costo elegible restante con saldo/fin del plan. No ejecutar infraestructura sin revisión final.
- Commit o PR: no creado; preparación local sin publicación.

## CAM-119 — Revisar permisos AWS y preparar Change Set

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: continuación solicitada por el usuario para avanzar con el despliegue en `us-east-2`; la verificación del correo de alertas permanece pendiente y se mantiene el seguimiento manual autorizado.
- Relación: SPEC-005, P0-05/P5-02; ADR-045; P-06/P-19/P-20.
- Resultado: las consultas EC2 de solo lectura identifican una VPC predeterminada con tres subredes públicas candidatas distribuidas en tres zonas de disponibilidad. La identidad AWS no puede consultar el stack de revisión (`cloudformation:DescribeStacks`) ni crear el Change Set (`cloudformation:CreateChangeSet`, AccessDenied). No se creó Change Set ni recurso AWS. No se guardan identificadores de cuenta, VPC o subredes en la documentación.
- Archivos: `docs/seguimiento/estado-actual.md`, `docs/seguimiento/pendientes.md`, `docs/seguimiento/plan-implementacion.md`, `docs/operacion/infraestructura.md`, `docs/operacion/guia-paso-a-paso-despliegue.md` e historial.
- Verificación: lecturas EC2 confirmaron las subredes candidatas; `DescribeStacks` y `CreateChangeSet` fueron denegados. `cfn-lint` local de CAM-118 sigue siendo la única validación de la plantilla; AWS no evaluó el Change Set. Ningún stack fue ejecutado.
- Límites: falta permiso para inspeccionar y revisar infraestructura en CloudFormation. El Change Set requiere revisión previa a cualquier creación. Staging público/TLS/dominio/red siguen pendientes y el Budget no detiene gastos.
- Siguiente paso: el administrador de la cuenta debe habilitar la lectura de stacks y Change Sets, `cloudformation:ValidateTemplate`, y `cloudformation:CreateChangeSet` sobre el stack dedicado con `CAPABILITY_IAM`; después revisar el plan y costos. No ejecutar el plan hasta presentarlo al usuario como revisión concreta.
- Commit o PR: no creado; preparación local sin publicación.

## CAM-116 — Empaquetar backend para smoke local

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: continuación de la preparación de despliegue Fase 3; el usuario autorizó avanzar aunque la verificación del correo de alertas Budget siga pendiente.
- Relación: SPEC-005, P0-05/P5-02; ADR-045; P-20.
- Resultado: se añadió imagen backend Python 3.12 con imagen base fijada por digest, dependencias runtime fijadas en lock, usuario no root, un worker Uvicorn, `/salud` como health check y mapa de Manta incluido. El script de smoke construye, ejecuta, comprueba salud/fixture/usuario y detención SIGTERM; admite Docker o Podman. El frontend sigue como build estático y no necesita Dockerfile. Docker Engine no estaba activo; la verificación se hizo con Podman.
- Archivos: `backend/Dockerfile`, `backend/.dockerignore`, `backend/requirements-container.lock`, `backend/scripts/smoke_docker.sh`, `backend/README.md`, infraestructura, guía de despliegue, pendientes, estado e historial.
- Decisiones/ADR: aplica ADR-045 sin exponer controles locales; no cambia topología/contrato y no requiere ADR.
- Validación ejecutada: `CONTAINER_ENGINE=podman backend/scripts/smoke_docker.sh` — build correcto, `GET /salud` HTTP 200, mapa Manta presente, usuario `navira`, apagado SIGTERM correcto. El segundo build usó formato Docker para que Podman no omitiera la instrucción HEALTHCHECK.
- Validación no ejecutada: CloudFormation no se valida porque no existe aún la plantilla; AWS/ECR no se usaron. No se ejecutó suite backend, pues no cambió código Python.
- Límites/pendientes: el lock captura las dependencias runtime para el contenedor; el backend se ejecuta desde el código copiado por `PYTHONPATH` sin compilar un wheel en la imagen. No hay plantilla, TLS/dominio o recursos. El Budget no muestra alertas (CAM-115).
- Estado real al cerrar: empaquetado local inicial probado; Fase 3 no completa. No se cambió AWS.
- Siguiente acción: configurar alerta y confirmar destinatarios en Budgets; elaborar plantilla parametrizada con TLS/red obligatorios para revisión antes de cualquier creación.
- Commit o PR: no creado; preparación local sin publicación.

## CAM-118 — Preparar CloudFormation para campaña efímera

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: continuar el despliegue pese a la verificación pendiente del correo Budget, manteniendo la preparación local y revisable.
- Relación: SPEC-005, P0-05/P5-02/P5-03; ADR-045; P-06/P-19.
- Resultado: plantilla `infra/aws/campaign.yml` acotada a ECR, logs con retención, ECS cluster, roles, security group sin entrada y definición opcional de tarea Fargate R1/R2/R3 anclada por URI inmutable SHA256. No crea ALB, listener, servicio persistente, NAT o frontend. Requiere VPC/subredes públicas existentes; la tarea se lanzaría explícitamente con IP pública y salida HTTPS. La definición de tarea se activa tras subir imagen y pasar su digest al stack.
- Archivos: `infra/aws/campaign.yml`, documentos de infraestructura/guía/pendientes/estado e historial.
- Decisiones/ADR: materializa la tarea efímera sin listener de ADR-045; topología pública de staging queda aparte porque TLS/dominio/origen no están definidos.
- Validación ejecutada: `/tmp/navira-cfnlint-env/bin/cfn-lint -r us-east-2 -t infra/aws/campaign.yml` sin diagnósticos. `CONTAINER_ENGINE=podman backend/scripts/smoke_docker.sh` ya validó la imagen referenciada como patrón del runner.
- Validación no ejecutada: AWS `cloudformation:ValidateTemplate` denegado al perfil activo; no se creó Change Set ni stack. Las consultas EC2 de solo lectura sí encontraron una VPC predeterminada y tres subredes con ruta pública candidata; no se registran sus IDs. Falta revisar permisos y costos efectivos.
- Límites/pendientes: el lint local no valida la cuenta, cuotas ni topología real. La plantilla crea un repo con política Retain y log group; revisar limpieza/retención antes de aplicar. Budget alerts están configuradas pero el usuario reporta correo pendiente de verificación (CAM-117). No hay staging web.
- Estado real al cerrar: artefacto local revisable, no desplegado; no se modificó AWS.
- Siguiente acción: conceder `cloudformation:ValidateTemplate`/permisos para crear Change Set e IAM PassRole necesarios; revisar costos y generar un Change Set con las subredes candidatas, sin ejecutar su creación hasta revisión final.
- Commit o PR: no creado; preparación local sin publicación.

## CAM-117 — Confirmar alertas y suscriptores del Budget

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario indicó que las alertas estaban configuradas y que solo faltaba verificar el correo; pidió continuar.
- Relación: SPEC-005, P0-03; P-06.
- Resultado: las APIs dedicadas `DescribeNotificationsForBudget` y `DescribeSubscribersForNotification` muestran tres notificaciones ACTUAL con umbrales 50 %, 80 % y 100 %, y un suscriptor EMAIL por cada una. `DescribeBudgets.NotificationsWithSubscribers` había devuelto lista vacía, por lo que se registró la discrepancia entre operaciones. El usuario reporta que la verificación del correo sigue pendiente; la API consultada no expone el estado de verificación/entrega.
- Archivos: `docs/seguimiento/estado-actual.md`, `docs/seguimiento/pendientes.md`, `docs/operacion/infraestructura.md`, `docs/operacion/costos.md`, guía de despliegue e historial.
- Verificación: consultas de solo lectura STS, `describe-notifications-for-budget` y `describe-subscribers-for-notification`; salida resumida sin cuenta, ARN ni dirección de correo. Sin cambios al Budget ni a recursos AWS.
- Límites: existencia de umbrales y suscriptores no demuestra que el destinatario haya confirmado el correo ni que las alertas estén llegando. El Budget mensual tampoco impide exceder el gasto.
- Decisión operativa: el usuario autoriza continuar la preparación del despliegue mientras se verifica el correo. Mantener seguimiento manual del gasto; revisar el costo y el Change Set antes de cualquier creación de infraestructura.
- Siguiente paso: preparar una plantilla CloudFormation revisable; no afirmar que el correo de alertas está verificado.
- Commit o PR: no creado; preparación local sin publicación.

## CAM-115 — Verificar detalle real del Budget de AWS

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario pidió leer y comprobar el Budget desde la sesión AWS recién configurada.
- Relación: SPEC-005, P0-03; P-06.
- Resultado inicial: la sesión SSO del perfil `default` consulta AWS Budgets en `us-east-2`. `Hackathon-Budget` existe con límite `10.0 USD`, período `MONTHLY`; la operación `DescribeBudgets` devolvió cero `NotificationsWithSubscribers`. La comprobación posterior de APIs específicas se registra en CAM-117.
- Archivos: `docs/seguimiento/estado-actual.md`, `docs/seguimiento/pendientes.md`, `docs/operacion/infraestructura.md`, `docs/operacion/costos.md`, guía de despliegue e historial.
- Verificación: `aws sts get-caller-identity` y `aws budgets describe-budgets` ejecutados mediante CLI; la salida se filtró para no registrar cuenta, ARN ni direcciones. `us-east-2` configurada. No se modificó el Budget ni se crearon recursos.
- Límites: esa operación no confirmó el estado de alertas ni entrega de correos; CAM-117 verificó notificaciones mediante llamadas específicas. El presupuesto es mensual; no constituye límite de gasto.
- Siguiente paso: consultar notificaciones y destinatarios por sus operaciones específicas, realizado en CAM-117.
- Commit o PR: no creado; preparación local sin publicación.

## CAM-114 — Verificar perfil AWS y tarifa del ALB en Ohio

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario terminó de configurar AWS CLI y preguntó el siguiente paso de despliegue.
- Relación: SPEC-005, P0-03/P5-02; P-06.
- Resultado: `aws sts get-caller-identity` pasó con el perfil `default`; la región configurada es `us-east-2`. No se guardó cuenta ni ARN. La llamada de solo lectura a AWS Budgets devuelve AccessDenied, así que los detalles de alertas no pudieron auditarse con ese perfil. El perfil `navira` no existe en la configuración; no es necesario, ya que `default` está autenticado. El archivo público AWS Price List `AWSELB` de Ohio confirma ALB US$0,0225/h y LCU US$0,008/h; no cambia el modelo estimado.
- Archivos: `docs/operacion/costos.md`, guía de despliegue, pendientes, estado e historial.
- Verificación: consulta STS satisfactoria y consulta Budgets denegada; lectura de Price List regional. Sin creación ni cambio de recursos.
- Límites: STS prueba identidad actual, no permisos de creación. AccessDenied de Budgets tampoco prueba que los demás permisos estén ausentes. El costo total sigue siendo aproximado, sujeto a exportación de Calculator, uso real y cuotas.
- Siguiente paso: confirmar en consola el detalle del Budget o solicitar al administrador de cuenta permiso de lectura; antes de crear recursos, validar el permiso de despliegue mediante revisión del Change Set.
- Commit o PR: no creado; preparación local sin publicación.

## CAM-113 — Alcance privado de staging y campaña AWS efímera

- Fecha: 2026-10-28, America/Guayaquil.
- Origen: el usuario autorizó continuar las fases de despliegue y pidió avanzar a Fase 2.
- Especificación/tareas: SPEC-005; P5-02/P5-03; CA-005-01..03; ADR-045.
- Resultado: se eligió staging privado con restricción de red y API key en `/paso`, sin endpoints remotos de operador. La campaña completa se ejecutará como tarea ECS Fargate efímera desde el mismo SHA/digest, con ASGI loopback; la carga remota al staging será evidencia separada porque `/paso` no modifica ni avanza el mundo. El staging es volátil para smoke: reiniciar invalida el run. Un coordinador por proceso, `desiredCount=1`.
- Archivos: ADR-045 e índices, SPEC-005, guía de despliegue, infraestructura, seguridad, pendientes, plan, estado e historial.
- Validación: `python3 backend/scripts/check_docs.py` (136 Markdown), `python3 backend/scripts/check_sdd.py` (10 SPEC), `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'` (8/8), backend `test_api_http.py` (7/7), `test_control_simulador_demo.py` (19/19) y `git diff --check` pasan. La consulta segura de disponibilidad de identidad AWS no se pudo ejecutar porque `aws` CLI no está instalado. AWS, red/TLS y campaña Fargate no se ejecutaron porque no hay recursos.
- Límites: define la Fase 2 pero no crea staging, aplica red/TLS ni implementa recuperación. P-06, P-11, P-19 y persistencia durable siguen pendientes. La campaña loopback no mide ALB/CloudFront.
- Siguiente paso: instalar/configurar AWS CLI mediante el proveedor de credenciales autorizado (sin compartir claves) y validar permisos/costos de `us-east-2`; iniciar Fase 3 después de cerrar ese gating de Fase 1.
- Commit o PR: no creado; el usuario pidió preparar el despliegue sin publicar estos cambios.

## CAM-106 — Cambio limpio entre modos

- Fecha: 2026-10-28, Ecuador continental.
- Origen: el usuario reportó que una partida en Jugar impedía iniciar Reto y pidió que cada modo nuevo comience desde cero.
- Requisitos/criterios/tareas: PRD-06; SPEC-009 CA-009-10/12; SPEC-010 CA-010-09; P4-05/P4-06; T-49/T-57. ADR-044 sustituye la restricción de ADR-040.
- Rama: `master`; cambios locales sin commit ni publicación.
- Resultado: cambiar pestaña reinicia controles/selección locales y oculta el snapshot, mapa con actores y métricas que no correspondan al modo seleccionado; no detiene ni elimina la partida por sí mismo. El inicio explícito del destino sustituye el run anterior por uno nuevo. Reto puede reemplazar una partida Simulador/Jugar activa o pausada, pero no pisa otra ronda Reto activa; Jugar inicia mundo vacío al salir de Reto; Simulador conserva su asistente.
- Archivos: `backend/src/navira/application/control_simulador_demo.py`, `backend/tests/test_control_simulador_demo.py`, `frontend/src/app/App.tsx`; SPEC-009/010, ODDD, modos, contratos API, módulo frontend, calidad, trazabilidad, plan, ADR-040/044 e índices.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_control_simulador_demo -v` (19/19); `cd frontend && npm test -- --run` (99/99) y `npm run build` pasan. `python3 backend/scripts/check_docs.py` (135 Markdown), `python3 backend/scripts/check_sdd.py` (10 SPEC), regresiones `test_check_sdd.py` (8/8) y `git diff --check` pasan. El bundle mantiene la advertencia conocida de `mapArea` (~1,066 kB). Se reinició backend `8001` preservando su configuración y se confirmó `/salud` y `/demo/simulador` por Vite `5173`; el smoke API inició R2 y la reemplazó por Jugar vacío con otro `runId` y cero actores. En el navegador, el árbol accesible muestra R2 habilitado, mapa/estadísticas limpias y Jugar activo en el backend; falta pulsar los controles visuales para verificar el ciclo completo desde UI.
- Límites: un solo run local en memoria; iniciar otro modo descarta el run anterior tras la acción confirmada. No se prueba persistencia, concurrencia entre procesos o un despliegue público. La prueba de reinicio de refugios que usa cero zombies reportada previamente sigue sin estar corregida y es independiente.
- Siguiente paso: en el navegador, pulsar «Iniciar R2», comprobar el nuevo `runId` y luego iniciar Jugar desde Reto; cambiar de pestaña sin iniciar y confirmar que el mundo del servidor permanece. El smoke API ya verificó esos endpoints y dejó Jugar activo/vacío. No crear commits ni publicar.

## CAM-107 — Reinicio libre con cero zombies y región AWS elegida

- Fecha: 2026-10-28, Ecuador continental.
- Origen: verificación de preparación para despliegue encontró que `POST /demo/simulador/reiniciar` fallaba con 422 cuando el escenario `libre` tenía cero zombies; el usuario pidió corregirlo, repetir la suite y eligió AWS `us-east-2`.
- Requisitos/criterios/tareas: flujo de reinicio del Simulador local; SPEC-007/T-51; preparación operativa según SPEC-005. Sin cambio de contrato público.
- Rama: `master`; cambios locales sin commit ni publicación.
- Resultado: al reiniciar sin conteo explícito, un cero guardado como resultado de un perfil vacío se traduce a `None`, para que el escenario genere su composición predeterminada y no se reenvíe el cero como parámetro inválido. Se agregó una aserción de regresión que confirma que `libre` continúa en cero zombies. La región elegida para el despliegue queda documentada como `us-east-2` (Ohio); la estimación previa de `us-east-1` se conserva como referencia histórica y no se considera válida para Ohio.
- Archivos: `backend/src/navira/application/control_simulador_demo.py`, `backend/tests/test_refugios_simulador.py`, `docs/operacion/infraestructura.md`, `docs/operacion/costos.md`, `docs/operacion/guia-paso-a-paso-despliegue.md`, estado e historial.
- Verificación: prueba enfocada de refugios con aserción de cero zombies (7/7); suite completa backend (240/240, 221,673 s); `python3 backend/scripts/check_docs.py` (135 Markdown), `python3 backend/scripts/check_sdd.py` (10 SPEC), ocho regresiones `test_check_sdd.py` y `git diff --check` correctos. Frontend no se repitió porque el cambio no lo afecta; la última corrida disponible fue 99/99 y build correcto.
- Límites: cuenta, región habilitada, permisos, Budget, destinatarios, costo actualizado y recursos AWS siguen sin comprobarse; no se creó infraestructura ni se publicó el código. El build frontend conserva la advertencia de bundle del mapa >1 MB.
- Siguiente paso: el usuario configura un Cost Budget para la cuenta AWS en la consola, con límite definido según duración/arquitectura y alertas verificadas; luego se actualiza el cálculo para `us-east-2` en AWS Pricing Calculator. Solo después se inicia la preparación de recursos.

## CAM-108 — Confirmación visual del Cost Budget

- Fecha: 2026-10-28, Ecuador continental.
- Origen: el usuario confirmó que creó el AWS Cost Budget y aportó una captura de la lista de presupuestos.
- Alcance: avance operativo de Fase 1 de SPEC-005; no cambia código ni crea recursos de aplicación.
- Resultado: la captura muestra `Hackathon-Budget` con US$10 listados y un banner de creación exitosa. Se registra como evidencia aportada por el usuario, no archivada para evitar conservar información de su consola.
- Archivos: `docs/operacion/costos.md`, `docs/operacion/infraestructura.md`, `docs/operacion/guia-paso-a-paso-despliegue.md`, `docs/seguimiento/estado-actual.md` y este historial.
- Límites: la captura no demuestra período, umbrales, destinatarios ni entrega de alertas; tampoco demuestra cuenta/permisos para despliegue. AWS Budgets es alerta, no límite rígido de gasto. El cálculo anterior corresponde a `us-east-1`, por lo que aún no se puede comparar con el presupuesto para `us-east-2`.
- Siguiente paso: crear una estimación en AWS Pricing Calculator con región `us-east-2`, arquitectura y horas reales de uso; contrastar el total con US$10 y ajustar el Budget/alcance antes de crear recursos.

## CAM-109 — Estimación parcial de Fargate

- Fecha: 2026-10-28, Ecuador continental.
- Origen: el usuario compartió el cálculo de una tarea diaria de 1 vCPU/2 GB activa 12 horas al día y su subtotal mensual de Fargate.
- Alcance: avance operativo de la estimación de costos en Fase 1 de SPEC-005; sin cambio de código ni creación de recursos.
- Resultado: se documentan 30,42 ejecuciones/días equivalentes, aproximadamente 365 horas de tarea, y US$18,03/mes según tarifas aportadas; el cálculo con horas exactas arroja cerca de US$18,02 por redondeo. Para 730 horas/mes, el mismo tamaño sería aproximadamente US$36,04 con las tarifas usadas. US$18,03 excede el Budget listado de US$10 en US$8,03 y solo cubre Fargate.
- Archivos: `docs/operacion/costos.md`, `docs/seguimiento/estado-actual.md` y este historial.
- Límites: no se aportó captura de la calculadora, región seleccionada ni detalle de tarifas, por lo que no se valida el precio de `us-east-2`. ALB, IPv4, S3, CloudFront, ECR, CloudWatch, tráfico y persistencia no están incluidos. El funcionamiento solo 12 h/día implica API inaccesible fuera del horario si se detiene la única tarea.
- Siguiente paso: confirmar en la calculadora `us-east-2`, Linux/x86, concurrencia y horas de servicio; completar el resto de servicios y acordar si el Budget debe ajustarse antes de crear recursos.

## CAM-110 — Ajuste de estimación a ventana de tres días

- Fecha: 2026-10-28, Ecuador continental.
- Origen: el usuario aclaró que el despliegue será en Ohio y que la aplicación se usará solo durante tres días.
- Alcance: actualiza la estimación/ventana de Fase 1 de SPEC-005; no cambia código ni crea recursos.
- Resultado: para una tarea Fargate de 1 vCPU/2 GB a 12 h/día durante tres días (36 horas), el costo con las tarifas aportadas es aproximadamente US$1,78; si corre las 72 horas, cerca de US$3,55. La comparación mensual previa de US$18,03 no representa el uso puntual de tres días.
- Archivos: `docs/operacion/costos.md`, `docs/operacion/guia-paso-a-paso-despliegue.md`, `docs/seguimiento/estado-actual.md` y este historial.
- Límites: el total AWS sigue pendiente porque faltan horas/consumos de ALB, IPv4, S3, CloudFront, ECR, CloudWatch, transferencia y persistencia. Los recursos que sigan activos pueden facturar durante las 72 h aunque Fargate esté detenido. El Budget de US$10 no constituye un límite de gasto.
- Siguiente paso: completar AWS Pricing Calculator para Ohio y una ventana de tres días, según el horario real de disponibilidad; comparar el costo total con el Budget antes de crear recursos.

## CAM-111 — Estimación parcial de LCU del ALB

- Fecha: 2026-10-28, Ecuador continental.
- Origen: el usuario compartió la estimación del componente variable LCU para un ALB.
- Alcance: avanza el cálculo de costos de Fase 1 de SPEC-005; no crea recursos ni altera código.
- Resultado: los supuestos ingresados dan `max(0,01; 0,04; 0,000333; 0) = 0,04 LCU`. A US$0,008 por LCU-hora, 730 horas representan US$0,23/mes; las 72 horas previstas en tres días representan cerca de US$0,02 en cargos LCU.
- Archivos: `docs/operacion/costos.md`, `docs/seguimiento/estado-actual.md` y este historial.
- Límites: la cifra no incluye la tarifa base por hora/fracción del ALB, IPv4, transferencia ni otros servicios. Conexiones/bytes son valores de entrada del estimador, no telemetría observada. La tarifa fija para Ohio todavía debe tomarse del calculador regional.
- Siguiente paso: sumar el precio fijo del ALB para 72 h en Ohio y terminar estimaciones de IP, frontend, logs, almacenamiento y transferencia para la ventana real.

## CAM-112 — Modelo provisional del costo total de tres días

- Fecha: 2026-10-28, Ecuador continental.
- Origen: el usuario pidió calcular y documentar directamente el costo del despliegue de tres días en `us-east-2`.
- Alcance: estimación de costos de Fase 1 de SPEC-005; sin cambios de código y sin creación de recursos AWS.
- Resultado: se modeló una topología breve con 1 tarea Fargate Linux/x86 1 vCPU/2 GB, un ALB por 72 h, 0,04 LCU promedio, dos IPv4 del ALB por 72 h, una IP de tarea por 36 h (12 h/día), una imagen ECR de 1 GB y 1 GB de logs. Como alternativa de frontend se usa el plan gratuito CloudFront dentro de sus cuotas actuales, 5 GB de almacenamiento S3 acreditado y sin dominio propio. Subtotal aproximado: US$4,83 para 12 h/día o US$6,78 con tarea 24/7. Presupuestos anteriores de solo Fargate/LCU se conservan como desglose.
- Archivos: `docs/operacion/costos.md`, `docs/seguimiento/estado-actual.md` y este historial.
- Límites: no es una cotización/exportación de AWS Pricing Calculator. El cargo ALB de US$0,0225/h procede del ejemplo público de `us-east-1`, debe confirmarse en Ohio. Logs/imagen/tráfico son cantidades de escenario, no mediciones. CloudFront Free requiere que distribución y uso respeten el plan; no se modelan dominio, DynamoDB (no implementado), NAT, impuestos, ni cargos por encima de cuotas. AWS Budgets alerta, no bloquea gastos.
- Siguiente paso: confrontar este modelo con el calculador en Ohio y la tarifa ALB exacta de la cuenta; revisar período/destinatarios del Budget y permisos. Antes de crear staging, completar controles de autenticación/operación y definir cómo se aceptará el estado temporal en memoria.

# Historial de cambios y contexto

Registro acumulativo. No reemplaza commits; al existir un repositorio operativo, enlazar revisión real sin inventarla. Las dos primeras entradas se reconstruyen de esta conversación, no de un historial Git comprobado.

## CAM-105 — Iniciar una nueva partida desde Jugar

- Fecha: 2026-10-27, Ecuador continental.
- Origen: el usuario pidió un botón en Jugar para iniciar una partida nueva.
- Especificación/requisitos/tarea: SPEC-010 CA-010-07/08; P4-06; T-56. El endpoint local de inicio vacío existente se reutiliza.
- Rama: `master`; código `d3579a9`, commit documental pendiente.
- Resultado: el panel del operador mantiene Pausar/Continuar y muestra «Iniciar nueva partida» mientras una partida de Jugar esté activa o pausada. El click sustituye el run por otro `runId` vacío y activo, limpia la herramienta/selección local y conserva excluido el modo Reto. Al no existir run, el inicio inicial también se rotula «Iniciar nueva partida».
- Archivos: `frontend/src/app/App.tsx`, `frontend/src/features/operator/OperatorControls.tsx`, `backend/tests/test_control_simulador_demo.py`; SPEC-010, módulo frontend, flujo de operador, calidad, contexto, trazabilidad, plan, índices, estado e historial.
- Verificación: prueba HTTP focal de reemplazo del run y T-54 (2/2), frontend (97/97), `npm run build` correcto; persiste la advertencia conocida del chunk MapLibre >500 kB. En `localhost:5173` se vio el botón junto a «Continuar mundo» en un run operador pausado (turno 337); no se pulsó para conservar ese estado. Los validadores docs/SDD se ejecutan al cierre.
- Límites: nueva partida reemplaza el mundo actual en memoria sin diálogo de confirmación, según la acción explícita del usuario; no se conserva estado del run anterior. El comportamiento sigue siendo local y requiere control demo habilitado.
- Siguiente acción: registrar validadores y separar commits de código/documentación. La instancia local actual sigue pausada e intacta; el frontend ya refleja el cambio por Vite/HMR.

## CAM-104 — Reglas de riesgo y rutas compartidas en Juego

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario de unificar las reglas para evitar incidentes, hordas y zombies próximos, tras observar que Juego no respetaba los otros modos.
- Especificación/tareas: PRD-03/10, TRD-14, ODDD invariant 10, R-06/R-08/R-10, SPEC-002 CA-002-14, SPEC-010; P3-03/P4-06; T-55. ADR-043 registra la política.
- Rama: `master`; código `b769e48`, commit de documentación pendiente.
- Motivo: endurecer filtros de peligros actuales sin declarar la proximidad de un zombie como mordida, mantener horda bloqueando su nodo y todos los vecinos topológicos aun junto a cierres, y evitar continuar rutas confirmadas que quedan bloqueadas más adelante.
- Archivos: `backend/src/navira/application/decidir_paso.py`, `domain/visibilidad.py`, `routing/prediccion.py`, `backend/tests/test_decidir_paso.py`; PRD, TRD, ODDD, reglas, algoritmos, módulo backend, calidad, SPEC-002/010, trazabilidad, plan, ADR-043, índices, estado e historial.
- Resultado: las calles/segmentos incidentados y nodos bloqueados siguen siendo filtros duros del planificador compartido. Una horda bloquea nodo y vecinos entrantes/salientes independientemente de cierres. Caminantes y corredores activos elevan en 0.4 la exposición estimada de nodos abiertos a un salto como preferencia blanda; no impide el paso si no hay alternativa y no cambia la regla de mordida por misma casilla/cruce opuesto. La ruta comprometida se invalida si cualquier nodo restante queda bloqueado; simulador y Juego consumen el mismo resolutor.
- Verificación: `test_decidir_paso.py` (18/18), `test_prediccion_rutas.py` (7/7), `git diff --check`, `python3 backend/scripts/check_docs.py` (133 Markdown), `check_sdd.py` (10 SPEC) y regresiones SDD (8/8) pasan. La suite backend completa corrió 238 pruebas y tuvo un fallo ajeno al cambio: `test_refugios_simulador.RefugiosSimuladorTests.test_reiniciar_con_refugios_validos_usa_el_mapa_personalizado` recibió 422 porque el caso existente reinicia con cero zombies, rechazados por la validación del control de demo. No se midió la latencia de una ronda ni el comportamiento del proceso local con este código aún cargado.
- Límites: presión de vecindad y factor 0.4 son una preferencia heurística no calibrada, no una probabilidad de mordida ni garantía de ruta óptima/segura. No se cierra T-11, T-22 ni SPEC-002/SPEC-010.
- Commits: código `b769e48`; documentación `366df6d`.
- Siguiente acción: cargar el backend actualizado en una sesión local controlada para probar la paridad visual; reiniciar puede perder el estado volátil de la partida actual.

## CAM-103 — Identificador estable al colocar incidente

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: el usuario reportó que al seleccionar «Incidente» y hacer clic en una calle del mapa, el backend rechazaba la selección con «La calle seleccionada no pertenece al mapa de la partida».
- Especificación/tarea/prueba: SPEC-010 CA-010-05; P4-06; T-53.
- Resultado: cada feature GeoJSON de calle incluye el `segmentoId` explícito del mapa y MapLibre lo promueve como ID de feature. El hit-test de incidente envía ese `segmentoId` desde `properties` al backend; no depende de una conversión del ID renderizado.
- Archivos: `frontend/src/features/map/CityMap.tsx`, `mapFeatures.ts`, `mapFeatures.test.ts`; módulo frontend, T-53, trazabilidad, SPEC-010, plan y estado.
- Validación: prueba focal `mapFeatures` 13/13; suite frontend 97/97; `npm run build`; `check_docs.py`, `check_sdd.py` (10 SPEC), regresiones SDD 8/8 y `git diff --check` pasan. Smoke manual en `localhost:5173`: seleccionar Incidente y hacer clic en calle urbana produjo acuse `incidente agregado`; `GET /panel/estado` confirmó un evento aplicado y un segmento cerrado (`S-OSM-32308390-177-4-5`). El mundo permaneció activo. No se probó cada herramienta ni el rechazo visual de clics fuera de calle.
- Límites: el smoke usa el mapa/juego local en memoria; no valida despliegue público ni otros proveedores. Al terminar se reinició el backend para recuperar el proceso local, así que el run de smoke se perdió; se inició un nuevo mundo operador vacío para dejar la app lista.
- Commits: pendientes; separar código y documentación conforme a la instrucción previa del usuario.
- Siguiente acción: la app local quedó activa en un nuevo mundo vacío; completar el resto del smoke T-53 y repetir el clic de incidente a otros niveles de zoom si aparece otra discrepancia.

## CAM-102 — Juego inicia con el mapa vacío

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: el usuario pidió que al empezar un nuevo juego el mapa aparezca vacío.
- Especificación/requisitos/tarea: SPEC-010 CA-010-07; PRD-12, TRD-18; P4-06; T-54. ADR-042 amplía la decisión de operador.
- Resultado: el botón de inicio de Jugar llama a un endpoint dedicado que conserva las calles/cartografía de Manta, pero no crea habitantes, zombies, refugios ni incidentes. El reloj local sigue avanzando con cero sobrevivientes, el estado permanece `activa` para admitir colocaciones posteriores y Simulador/Reto mantienen sus flujos.
- Archivos: `backend/src/navira/demo.py`, `application/control_simulador_demo.py`, `application/reloj_simulador.py`, `api/routes.py` y prueba de integración; `frontend/src/app/App.tsx`, `features/operator/OperatorControls.tsx`, cliente y prueba HTTP; SPEC-010, ADR-042, PRD/TRD, flujo de operador, contrato API, módulo backend, calidad, trazabilidad, plan y estado.
- Validación: prueba de módulo backend 17/17 y repetición focalizada T-54 tras corregir el estado vacío (turno y control continúan activos; colocación posterior de refugio/habitante); suite frontend 97/97, build, validadores docs/SDD y `git diff --check` pasan. Smoke en `localhost:5173` sobre API reiniciada confirmó Jugar en curso, mapa OSM de Manta cargado, 0 activos, 0 amenazas y sin marcadores iniciales. Build mantiene advertencia conocida del chunk MapLibre.
- Límites: estado/reloj siguen en memoria y el endpoint solo se debe ensamblar para demo local, loopback y opt-in; esto no constituye despliegue público ni valida visualmente cartografía.
- Commits: pendientes; crear commits independientes de código y documentación según la instrucción previa del usuario.
- Siguiente acción: usar la paleta para colocar refugio/actores y probar incidente desde el mapa; la partida se dejó activa y vacía. T-53 aún requiere confirmar visualmente colocación de incidente antes de cerrar SPEC-010.

## CAM-101 — Juego como modo de operador interactivo

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: el usuario pidió que Juego mantenga la simulación en ejecución y permita elegir una herramienta para colocar habitantes, caminantes, corredores, hordas, dormidos, refugios e incidentes en el mapa; confirmó que busca una experiencia «más de operador».
- Especificación/tareas: SPEC-010 CA-010-01…06; PRD-12, TRD-18; P4-06, T-52 y T-53.
- Resultado: Jugar arranca el mundo automático local de operador (20 habitantes, 42 amenazas mixtas, 4×), ofrece pausa/continuación y una paleta de herramientas. Los actores/refugios se colocan sobre nodos del mapa y los incidentes cierran una calle visible. Las mutaciones se validan y versionan en servidor; los dormidos permanecen ocultos al panel.
- Límites de seguridad y alcance: endpoint de intervención disponible solo con opt-in local, loopback y origen local; rechaza Reto, partidas pausadas/inexistentes, ubicaciones inválidas y límites de cantidad. No se habilita control remoto ni se cambia el modo Simulador o la evaluación Reto. El bloqueo compartido con el reloj mantiene atómica la intervención frente al ciclo automático.
- Archivos: backend de control, reloj y ejecución; endpoint/schemas y pruebas; nueva paleta, cliente de colocación, integración de mapa y navegación; SPEC-010, ADR-042 y documentos propietarios de producto, dominio, contratos, módulos, calidad y trazabilidad.
- Validación: suite backend de control 16/16; dos pruebas de integración focalizadas 2/2; frontend 96/96; build correcto con advertencia existente de chunk grande; `check_docs.py` (132 Markdown/134 archivos), `check_sdd.py` (10 SPEC), regresiones SDD 8/8 y `git diff --check` pasan. Smoke en navegador aislado `5174/8002`: Jugar abrió la paleta, inició mundo automático con mapa de Manta visible, y colocar un caminante devolvió confirmación `caminante agregado` mientras el turno seguía avanzando y el snapshot se actualizó. El clic visual para crear incidente no quedó confirmado; su validación backend está en las pruebas de integración. La corrida local alcanzó al menos el turno 102; no demuestra cadencia sostenida ni evaluación oficial.
- Commits: código `c27d576` (`feat(juego): add live operator mode`); esta entrada se registra en el commit documental independiente.
- Siguiente acción: mantener intacta la partida anterior en 5173/8001. Antes de marcar SPEC-010 verificada, completar T-53 confirmando visualmente colocación de incidente y actualización cartográfica; probar además concurrencia bajo carga y pausa prolongada.

## CAM-100 — Asistente de inicio y configuración del Simulador

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: el usuario pidió que Simulador muestre al inicio solo «Iniciar simulación»; tras el clic, primero escoger puntos seguros y luego cantidades de habitantes/zombies. La velocidad queda fija en 4× y desaparece su selector.
- Especificación/requisitos/tarea: SPEC-007 CA-007-09/10; PRD-02, TRD-17; P4-03 parcial; T-51. ADR-041 conserva la decisión.
- Rama: `master`; commits separados de código y documentación según instrucción previa del usuario, aún no creados en este registro.
- Motivo: el panel anterior abría refugios automáticamente y mostraba escenario, población, intensidad y velocidad antes de iniciar; zombies se configuraban por intensidad y no por conteo exacto.
- Archivos de código: `frontend/src/app/App.tsx`, `frontend/src/application/useSimulator.ts`, `frontend/src/domain/simulator.ts`, `frontend/src/features/map/RefugePicker.tsx`, `frontend/src/styles.css`, `backend/src/navira/api/schemas.py`, `backend/src/navira/api/routes.py`, `backend/src/navira/application/control_simulador_demo.py`, `backend/src/navira/demo.py`, `backend/src/navira/simulation/escenarios.py`; pruebas frontend/backend relevantes.
- Resultado: el panel inicial presenta inicio explícito; un asistente obliga asignar los cuatro refugios antes de abrir los campos 1–200 de habitantes y zombies. Al confirmar, se envían en la misma solicitud con escenario mixto, se genera el conteo solicitado en el servidor (si hay nodos disponibles) y el estado del control expone la cantidad inicial. El valor inicial del tablero es 20 habitantes/42 zombies; la aleatoriedad de semilla, composición y ubicaciones continúa. El panel informa 4× fijo. El campo `zombies` es opcional para clientes existentes, que conservan intensidad como fallback; `/paso`, Reto y Jugar no cambian.
- Verificación: `cd frontend && npm test -- --run` (96 pruebas) y `npm run build` pasan; build conserva advertencia de bundle MapLibre grande. Backend focalizado `cd backend && PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_demo tests.test_control_simulador_demo` (33 pruebas) pasa; `PYTHONPATH=src /tmp/navira-env/bin/python -m compileall -q src/navira` pasa. `python3 backend/scripts/check_docs.py`, `python3 backend/scripts/check_sdd.py` y `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'` pasan (8 pruebas de regresión SDD). `git diff --check` pasa. T-51 fue recorrido visualmente hasta el paso de cantidades; no se confirmó la creación del run porque el usuario debe seleccionar los refugios y confirmar.
- Límite operativo: durante la verificación, el proceso backend anterior dejó de responder y el run Reto pausado ya no estaba disponible; no se terminó manualmente. Se levantó el código actual en loopback `127.0.0.1:8001` con `NAVIRA_LOCAL_DEMO_CONTROL=1` y el mapa Manta. `/salud` respondió 200 y `GET /demo/simulador` confirmó `sin_partida` y velocidad 4×; `zombiesIniciales: null` es correcto mientras no exista run. Vite responde en `localhost:5173`; no se creó una partida real porque falta que el usuario elija los cuatro refugios y confirme las cantidades. No hay despliegue.
- Siguiente paso: cerrar commits separados de código/documentación. El smoke de creación final queda para cuando el usuario seleccione sus cuatro refugios y pulse «Iniciar simulación».

## CAM-099 — Repetir campaña local Reto con tres semillas

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: continuar la validación de T-11 después de CAM-098 y medir si el comportamiento se mantiene entre semillas.
- Especificación/requisitos: SPEC-005 CA-005-02, SPEC-009 CA-009-11, P2-03/P4-05/P5-01/P5-03 y T-11/T-50.
- Método: tres campañas secuenciales completas con semillas base 20261026, 20261027 y 20261028, 150 turnos/300 s por ronda, cadencia objetivo 2 s, máximo 200 workers, cliente y Uvicorn en loopback. CAM-098 contiene la primera campaña; esta CAM agrega las otras dos, sin carga paralela.
- Resultado: nueve rondas completaron 150 turnos activos, sin slots ociosos, fuera de período ni fallas. Total 69.572 solicitudes HTTP 200. p95 `/paso` entre 10,625 y 64,313 ms, máximo individual 127,566 ms; ciclo p95 máximo 1.378,374 ms, duración máxima 1.676,531 ms. Puente R2 y dos cierres R3 se aplicaron en cada campaña. Los números de evacuados/mordidos variaron por semilla.
- Archivos: [reporte de repeticiones](../calidad/resultados/repeticiones-reto-cam099.md), T-11/T-50, SPEC-005/009, trazabilidad, plan, índices, estado e historial.
- Validación: `python3 backend/scripts/check_docs.py` (129 Markdown/131 archivos), `python3 backend/scripts/check_sdd.py` (9 SPEC), `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'` (8/8) y `git diff --check` pasan. La suite backend 231/231, compileall y smoke CLI están registrados en CAM-098; CAM-099 no cambia código.
- Límites: tres semillas son evidencia repetible local, no prueba de variabilidad estadística amplia o AWS. Configuración de densidad y turnos de eventos continúa provisional. T-11 y las SPEC no se marcan completas; la evaluación oficial/entorno AWS sigue pendiente.
- Siguiente acción: ejecutar la misma campaña en el entorno oficial/AWS luego de comprobar permisos, presupuesto, seguridad y endpoint; conservar versión, mapa y reporte.

## CAM-098 — Ejecutar campaña local Reto R1/R2/R3 con ventana completa

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: el usuario decidió mantener la regla formal de horda (nodo y vecinos) y continuar cerrando las pruebas de las tres rondas de cinco minutos.
- Especificación/requisitos: SPEC-009 CA-009-11, SPEC-005 CA-005-02, PRD-07, TRD-02/TRD-10, P2-03/P4-05/P5-01/P5-03 y T-11/T-50.
- Motivo: el evaluador anterior medía cohortes `mixto` aisladas y no consumía los presets Reto R1/R2/R3 como una campaña secuencial. CAM-087 ya completaba la ventana luego de terminación con slots ociosos transparentes.
- Resultado de implementación: `ejecutar_campana_reto_local()` ejecuta los presets existentes en orden 1→2→3, poblaciones 20/80/200, semilla derivada por ronda, 150 slots por defecto y cadencia objetivo de 2 s. Cada ronda usa HTTP loopback `/paso`, crea un run independiente y conserva ventana aunque el mundo termine. El reporte identifica run/mapa/semilla, latencias/errores, turnos activos, slots ociosos y eventos programados/aplicados; progreso de cada ronda va a stderr, JSON consolidado a stdout. La evaluación no genera movimiento o solicitudes ficticias tras estado terminal.
- Regla de horda: el usuario aclaró que «Lo que el jurado va a buscar» lista errores comunes y no requisitos alternativos. Pasar por un vecino tras esquivar solo el nodo cuenta como error; R-06 (nodo y todos los vecinos bloqueados) es el criterio, P-18 queda resuelto, y el código/T-03 ya lo cumplen. No se altera código ni texto del reto original.
- Archivos: `backend/src/navira/evaluacion_local.py`, `backend/tests/test_evaluacion_local.py`, `backend/README.md`, reglas, pendientes, SPEC-005/009, T-11/T-50, trazabilidad, plan, este historial, estado y [reporte CAM-098](../calidad/resultados/campana-reto-cam098.md).
- Validación de código: campaña real 3×5 min con 150 turnos por ronda; R1/R2/R3 enviaron 1.420/5.741/15.394 solicitudes, total 22.555, todas HTTP 200 y 0 fallas. p95 de `/paso`: 10,625/26,184/64,313 ms; p95 de resolución de turno: 463,409/1.104,635/1.378,374 ms; ningún turno fuera del período de 2 s. Eventos de R2/R3 se aplicaron en turnos 50/100. Resultado: R1 19 evacuados/0 mordidos; R2 65/2; R3 167/7. La campaña tardó 913,964 s frente a 900 s objetivo. Backend completo 231/231, compileall y `git diff --check` pasan. Reporte: [campaña CAM-098](../calidad/resultados/campana-reto-cam098.md).
- Validación documental: `check_docs.py` (128 Markdown/130 archivos), `check_sdd.py` (9 SPEC), pruebas del validador SDD (8/8) y `git diff --check` pasan. La primera ejecución de SDD reveló metadato T-50 faltante en SPEC-009; se corrigió y el validador final pasó. No se marcan SPEC-005/009 ni T-11 completas: se requiere repetición y AWS/entorno oficial.
- Límites: loopback, no AWS, una campaña y semilla por ronda; no prueba latencia remota, sostenibilidad/repetibilidad estadística ni el entorno del jurado. El preset mantiene supuestos de densidad/eventos. Se alcanzaron 150 transiciones por ronda; no se afirma rendimiento o supervivencia general. P5-03 y evaluación AWS siguen pendientes.
- Siguiente acción: repetir la campaña con varias semillas y medir en el entorno oficial/AWS cuando estén disponibles sus permisos y presupuesto.

### Aclaración incorporada durante CAM-098 — regla de horda

El usuario precisó que la sección «Lo que el jurado va a buscar» enumera errores comunes, no requisitos alternativos: pasar por un vecino de la horda tras esquivar solo su nodo cuenta como error. R-06 (nodo y vecinos intransitables) es el criterio oficial aplicable; P-18 queda resuelto, el código y T-03 ya lo implementan. No se edita la referencia original del reto.

## CAM-097 — Unificar controles y permitir nueva simulación desde Reto pausado

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: el usuario pidió un único botón que cambie entre iniciar, pausar y continuar; mantener reinicio y permitir iniciar una partida nueva cuando Reto esté pausado.
- Especificación: SPEC-009 CA-009-09/10, P4-05 parcial, T-48/49; ADR-040 define cuándo se sustituye una partida.
- Motivo: la UI mostraba controles iniciar/continuar separados y deshabilitaba «Iniciar» en pausa; además el endpoint rechazaba iniciar cualquier ronda cuando existía una Reto pausada.
- Resultado: un botón primario cambia por estado entre iniciar, pausar y continuar; al pausar Reto, aparece «Nueva simulación Rn» para reemplazar la ronda actual por el preset seleccionado y «Reiniciar Rn» permanece separado. El backend permite reemplazar solo un Reto pausado; una partida activa o una demo libre pausada siguen protegidas con 409.
- Archivos: `frontend/src/app/App.tsx`, `backend/src/navira/application/control_simulador_demo.py`, pruebas backend/frontend; contrato API, ADR-040/índice, módulo frontend, SPEC-009/índice, T-49, plan, trazabilidad, README, este registro, estado y [evidencia](../calidad/resultados/reto-nueva-simulacion-pausada-cam097.md).
- Decisión: ADR-040; se conserva `POST /reto/iniciar` como endpoint y se extiende solo su regla para un reto pausado, dentro del control local.
- Validación: backend `tests.test_control_simulador_demo` 14/14; incluye reemplazo de Reto pausado por R3 con `runId` distinto/población 200, rechazo 409 mientras activa y protección de demo libre pausada. Frontend `npm test -- --run` 96/96 y `npm run build` correcto, con advertencia conocida de chunk `mapArea` 1.065,62 kB. `check_docs.py` 127 Markdown/129 archivos, `check_sdd.py` 9 SPEC, regresiones SDD 8/8 y `git diff --check` correctos. Smoke browser: botón unificado cambió Continuar→Pausar; «Nueva simulación R2» inició otro run con 80 personas; pausa regresó a «Continuar R2». API/UI HTTP 200.
- Validación no ejecutada: suite backend completa no se repitió; se ejecutó la suite completa del módulo de control (14 pruebas) más el caso enfocado. No se probó el modo público/producción.
- Límites: al iniciar una nueva ronda se reemplaza el mundo pausado, que es volátil; no hay historial/recuperación de ese mundo. No se permite reemplazar una partida activa.
- Siguiente acción: crear commits separados de código y documentación; la API y Vite locales quedan activos con R2 pausada en turno 4.
- Commits separados en `master`: código `f32e705` (`feat(reto): start new round from paused challenge`) y documentación en el commit posterior del historial local.

## CAM-096 — Pausar y continuar la ronda del modo Reto

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: el usuario indicó que en el panel Reto veía reinicio pero no la opción para parar/pausar la partida; pidió confirmar si era una versión anterior.
- Especificación/tarea: SPEC-009 CA-009-09, P4-05 parcial, T-48.
- Motivo: el control de reinicio se había incorporado sin exponer en Reto los endpoints de pausa/continuación que ya usa el Simulador.
- Resultado: el panel del Reto muestra «Pausar Rn» mientras el run está activo y «Continuar Rn» si está pausado; conserva disponible «Reiniciar Rn». Reutiliza `POST /demo/simulador/pausar` y `/reanudar`, así la pausa conserva `runId`, ronda y mundo, y el reinicio genera uno nuevo.
- Archivos: `frontend/src/app/App.tsx`, `backend/tests/test_control_simulador_demo.py`; SPEC-009, módulo frontend, T-48, plan, índice de SPEC, este historial, estado y [reporte de evidencia](../calidad/resultados/control-reto-pausa-cam096.md).
- Decisiones: no requiere ADR; reutiliza el control local y la semántica existente de CAM-050/ADR-015.
- Validación: test backend Reto pausa/continúa 1/1; `cd frontend && npm test -- --run` 95/95; `npm run build` correcto (advertencia conocida del bundle `mapArea`); navegador local: se continuó R2, apareció «Pausar R2», se pausó y apareció «Continuar R2», conservando `rondaReto=2`. El estado quedó pausado en turno 6. `/salud` y UI respondieron HTTP 200; `check_docs.py` (125 Markdown/127 archivos), `check_sdd.py` (9 SPEC), regresiones SDD 8/8 y `git diff --check` correctos.
- Validación no ejecutada: suite completa backend no se repitió por ser un cambio focalizado.
- Límites: es una pausa reanudable, no finaliza ni elimina una partida. El reinicio sigue creando un run nuevo. Control local solamente.
- Siguiente acción: crear commits separados de código y documentación; luego retomar el diagnóstico cartográfico pendiente.
- Commits separados en `master`: código `9e8cc5f` (`feat(reto): add pause and resume controls`) y documentación en commit posterior del historial local.

## CAM-095 — Centrar amenazas del Reto y permitir reiniciar la ronda

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: el usuario reportó que faltaba reinicio en modo Reto y que zombies, hordas e incidentes dejaban vacío el centro del mapa.
- Especificación: SPEC-009 CA-009-07/08, P4-05 parcial, T-47; ADR-038 fija distribución espacial sintética; ADR-039 fija semántica/contrato de reinicio.
- Rama: `master`; commit de código `79bc5d6` (`feat(reto): add restart and centralize threats`) y commit documental separado `143acc1` (`docs(reto): document restart and urban threat focus`).
- Decisión/resultado: en Manta Reto, muestrear por tipo al menos `round(80% de la cantidad de ese tipo)` dentro de 3.500 m de la referencia central de Parque La Dolorosa/R-03 y ubicar el resto fuera cuando existan nodos. R2/R3 prefieren puentes/calles del mismo foco, con fallback si faltan candidatos. La demo libre conserva exactamente la selección global anterior, sus conteos y generador de cierres. El botón «Reiniciar Rn» llama `POST /reto/reiniciar`; el backend recrea el mismo preset con un run/semilla nuevos y responde 409 si no hay una ronda Reto que reiniciar.
- Archivos: `backend/src/navira/simulation/escenarios.py`, `backend/src/navira/demo.py`, `backend/src/navira/application/control_simulador_demo.py`, `backend/src/navira/api/routes.py`, pruebas backend, `frontend/src/app/App.tsx`, `frontend/src/application/useSimulator.ts`, cliente/tests frontend; SPEC-009, ADR-038/039, contratos, mapa Manta, modos, pruebas, plan, contexto, pendientes, trazabilidad, índices, reporte y estado.
- Verificación: pruebas backend focalizadas 5/5 y suite completa 227/227; frontend 95/95 y build correcto con advertencia existente de chunk `mapArea` (1.065,62 kB); compileall; `check_docs.py` (124 Markdown/126 archivos); `check_sdd.py` (9 SPEC); regresiones SDD 8/8; `git diff --check`. En proceso API reiniciado, `/salud` 200 y `POST /reto/reiniciar` 200 manteniendo R2/80 con `runId` nuevo. El árbol de accesibilidad del navegador confirmó «Reiniciar R2» y API disponible; cartografía aún indicaba carga. El `POST /reto/iniciar` previo devolvió el 409 esperado ante una ronda activa.
- Límites: el centro, radio, cuota del 80%, densidad y proporción zombie son supuestos de presentación y no reglas oficiales o modelo de riesgo. El foco no aumenta el conteo total; redistribuye los zombies existentes. No demuestra menos mordidos, balance oficial, campaña 3×5 min, T-11 ni AWS. P-09/P-15 quedan abiertos.
- Siguiente paso: diagnosticar la carga cartográfica que quedó pendiente en el navegador y verificar visualmente la ubicación de las amenazas/eventos del Reto.

## CAM-094 — Iniciar habitantes del Reto en los cuatro sectores establecidos

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: continuación del usuario para ubicar el spawn de habitantes del Reto en los lugares establecidos por el enunciado. La fuente original nombra Tarqui, Los Esteros, Barbasquillo y Jocay.
- Especificación/tareas: SPEC-009 CA-009-06, P4-05 parcial, T-47; ADR-037. No completa toda SPEC-009, la campaña consecutiva ni T-11.
- Rama: `master`; código `d327c5a` (`feat: spawn reto survivors in four Manta sectors`) y documentación en commit individual separado.
- Motivo: antes del cambio, el preset del Reto sorteaba habitantes por toda la zona jugable, sin respetar las cuatro zonas del enunciado.
- Archivos: `backend/src/navira/demo.py`, `backend/tests/test_demo.py`; documentación de contexto, modos, mapa Manta, SPEC-009, T-47, trazabilidad, plan, pendientes, ADR-037, índices, estado e historial.
- Resultado: para partidas Reto sobre el mapa Manta, el servidor asigna cada nodo a su referencia sectorial OSM más cercana dentro de un radio local de 1.500 m, distribuye cohortes casi igual por las cuatro áreas y muestrea nodos viales distintos con el RNG privado. Las rondas 20/80/200 quedan en 5/20/50 personas por sector. Los nodos tienen ruta dirigida hacia refugios y excluyen los propios refugios. La misma semilla reproduce las posiciones; otra semilla altera la muestra. El Simulador libre y mapas sintéticos mantienen su algoritmo anterior.
- Verificación: `cd backend && PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_demo tests.test_control_simulador_demo -v` (26 OK) y suite backend completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py'` (223 OK); incluye balance R1/R2/R3, elegibilidad, nodos únicos, replay/variación por semilla, continuidad del spawn libre y contrato `/reto/iniciar`. También pasan `compileall`, `python3 backend/scripts/check_docs.py` (121 Markdown/123 archivos), `python3 backend/scripts/check_sdd.py` (9 SPEC), ocho pruebas de `test_check_sdd.py` y `git diff --check`. API reiniciada; Vite proxió `/salud` con HTTP 200 y se inició R2 por `/reto/iniciar` con 80 habitantes; el mismo run quedó activo en turno 8. La comprobación espacial HTTP se hizo después de que avanzó el mundo y un habitante ya se había alejado de su zona inicial; la ubicación al inicio se valida desde el snapshot inicial mediante pruebas, no desde el snapshot posterior. No se midió supervivencia ni ronda completa.
- Límites: el enunciado no define polígonos o cuotas por barrio. Los radios de 1.500 m y reparto igual son una aproximación explícita basada en referencias OSM; no son límites administrativos/catastrales ni distribución oficial. Actualizar si la organización comparte polígonos o cantidades por sector.
- Siguiente paso: inspeccionar una partida Reto en el frontend y confirmar visualmente que los marcadores iniciales se muestran en las cuatro zonas; luego seguir la campaña de tres rondas y reporte.

## CAM-093 — Calcular bajo demanda la ruta del habitante seleccionado

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: en el modo Reto, al hacer clic en un habitante no se mostraba su ruta recomendada.
- Causa confirmada: los snapshots del simulador entregan `rutasPrevistas` en fase `decisiones`, pero no en el resto de fases; la ficha dependía exclusivamente de esa lista.
- Decisión: el snapshot general vuelve a conservar la proyección ligera y rutas compartidas solo durante `decisiones`. Para un habitante activo seleccionado fuera de esa fase, el cliente pide una sola ruta versionada a `GET /panel/ruta/{sobreviviente_id}`. La UI reutiliza el trayecto mientras permanece en el mismo turno y descarta respuestas de otra partida/turno/persona. El juego humano sigue usando la ruta visible solo durante decisiones.
- Especificación/requisitos: PRD-04, TRD-07, SPEC-003 CA-003-06, P4-01 y T-45; la intención original se registra en CAM-092. ADR-036 documenta el contrato de consulta individual.
- Archivos: caso de uso y ruta/schema backend, pruebas de panel; parser/cliente/puerto, App y ficha frontend, pruebas; contrato API, flujo espectador, módulos, SPEC-003, T-45, contexto, estado, plan, trazabilidad, índice ADR e historial.
- Verificación: backend completo `python3 -m unittest discover -s tests -p 'test_*.py'` 221/221 en 76,671 s; panel focalizado 17/17. Frontend `npm test -- --run` 94/94 y `npm run build` correcto (permanece advertencia conocida de chunk `mapArea` 1,065.62 kB); `compileall`, `check_docs.py` (120 Markdown/122 archivos), `check_sdd.py` (9 SPEC), regresiones SDD 8/8 y `git diff --check` pasan. Smoke integrado inició R1 por Vite, observó 20 sobrevivientes en turno 2/fase `resuelta` con 0 rutas masivas, y `GET /panel/ruta/S-DEMO-001` devolvió HTTP 200 con un trayecto de 17 nodos en turno 5/resuelta. La UI confirmó run activo y conexión del panel; no se automatizó el clic visual porque el mapa seguía mostrando “Cargando mapa de Manta…”.
- Límites: la ruta sigue siendo recomendación observable y no garantiza seguridad; si el habitante ya no está activo, el endpoint devuelve 404. Esta corrección no mide cadencia global ni completa la evaluación oficial.
- Commits: código `5956880`; documentación `57973f7`, separados según la preferencia vigente del usuario.

## CAM-092 — Mantener rutas recomendadas visibles durante Reto

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: al hacer clic en un habitante del modo Reto, la interfaz no mostraba su ruta recomendada.
- Causa: `ConsultarPanel` solo agregaba `rutasPrevistas` en fase `decisiones`; el simulador automático entrega snapshots también en `preparacion`, `zombies_movidos` y `resuelta`, por lo que la ficha quedaba sin ruta la mayor parte del ciclo.
- Resultado histórico: una primera implementación proyectó ruta para toda la población activa durante todas las fases. El smoke la confirmó, pero el cálculo repetido de la cohorte sobre el grafo Manta produjo uso elevado de CPU y tiempos de espera. CAM-093 sustituye este enfoque por una consulta individual bajo demanda; se conserva el snapshot liviano fuera de `decisiones`.
- Archivos: `backend/src/navira/application/consultar_panel.py`, `backend/tests/test_panel.py`, contrato API, flujo espectador, módulo backend/frontend, T-45, contexto, estado e historial.
- Validación: `tests.test_panel` 16/16; la prueba nueva confirma rutas para todos los sobrevivientes activos en fase `resuelta`, y otra confirma que juego humano no publica rutas fuera de `decisiones`. Frontend 90/90, build correcto con advertencia existente del chunk de mapa >500 kB, compileall, `check_docs.py`, `check_sdd.py`, pruebas del validador SDD 8/8 y `git diff --check` pasan. Smoke del endpoint por Vite: R1 respondió 200 y el panel entregó 20 rutas para 20 sobrevivientes en fases `resuelta` en turnos 0 y 1.
- Commit de código: `5aeedf4`; documentación en commit separado posterior.

## CAM-091 — Mostrar un único contador acumulado de mordidos

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: eliminar el contador duplicado visualmente y conservar una cifra fija para los mordidos.
- Resultado: el panel conserva «Mordidos acumulados» y quita la tarjeta «Mordidos última resolución». El total siempre representa sobrevivientes terminales mordidos durante toda la partida; el dato de última resolución sigue en la respuesta técnica y no cambia la API ni el motor.
- Archivos: `frontend/src/app/App.tsx`, contexto, módulo frontend, criterio T-42, estado e historial.
- Validación: frontend `npm test -- --run` 90/90; `npm run build` correcto con advertencia existente del chunk `mapArea` >500 kB; `check_docs.py`, `check_sdd.py` y `git diff --check` pasan. Revisión estática confirma que `App` ya no renderiza la tarjeta por resolución.
- Commits: código `ec4fcf1`; documentación en commit separado posterior.

## CAM-090 — Enrutar el endpoint de Reto desde Vite

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: corregir `POST http://localhost:5173/reto/iniciar` que respondía 404 desde el modo Reto.
- Causa: el proxy de desarrollo no incluía el prefijo `/reto`; Vite contestaba el 404 sin enviar la petición a la API, aunque el backend tuviera la ruta.
- Resultado: Vite reenvía `/reto` al mismo backend configurado para `/demo`; se conserva `Origin` para la validación local.
- Archivos: `frontend/vite.config.ts`, `frontend/README.md`, módulo frontend, estado e historial.
- Validación: `GET /salud` a través de Vite responde 200. `POST /reto/iniciar` a través de `localhost:5173` respondió 200 y configuró la ronda 1 con 20 sobrevivientes. El run de smoke se limpió reiniciando el backend; una ronda R1 volvió a aparecer en estado activo durante la comprobación final (turno observado 46). Frontend 90/90, build correcto con advertencia del chunk de mapa >500 kB, `check_docs.py`, `check_sdd.py`, 8 pruebas del validador SDD y `git diff --check` pasan.
- Commits: código `0b70ac0`; documentación en commit separado posterior.

## CAM-089 — Priorizar Reto al abrir Navira

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: ordenar los modos de la pantalla inicial como Reto, Simulador y Jugar.
- Resultado: Reto ocupa la primera posición visual y de navegación por teclado y queda seleccionado al cargar la aplicación. Los indicadores pasan a A/B/C en ese orden. No cambia el motor ni las configuraciones de los modos.
- Archivos: `frontend/src/app/App.tsx`, `frontend/src/features/mode/ModeCard.tsx`; contexto, módulo frontend, estado e historial.
- Validación: frontend `npm test -- --run` (90/90), `npm run build` correcto con advertencia de chunk >500 kB; validadores `check_docs.py`, `check_sdd.py` y `git diff --check` correctos. No se modificó backend.
- Commits: código `8d2f806`; documentación en commit separado posterior.

## CAM-088 — Separar el flujo de reto de la demo libre

- Fecha: 2026-10-27, Ecuador continental.
- Solicitud de origen: agregar una experiencia específica para cumplir la prueba de fuego del hackathon y conservar el simulador como demo libre. El usuario seleccionó densidad media provisional y eventos reproducibles.
- Especificación/requisitos: PRD-06/07, TRD-02/10/11, SPEC-009 CA-009-01..05, P4-05, T-47 parcial; trazado también a P5-01/P5-03. No verifica T-11 ni la campaña de quince minutos.
- Decisión: ADR-035 conserva solo dos modos de dominio. «Reto» es un flujo de interfaz con presets automáticos. Densidad media, mezcla proporcional de R2 y turnos 50/100 son supuestos; P-09/P-15 quedan abiertos.
- Resultado: UI agrega selector Simulador/Reto/Jugar y una vista con presets R1/R2/R3. API local protegida `POST /reto/iniciar` crea la ronda elegida; R1 usa 20 caminantes, R2 80 sin dormidos y un puente, R3 200 con los cuatro tipos y dos calles. Semilla opcional controla la repetición; el frontend deja el sorteo aleatorio. El reloj del reto usa 1× sin alterar la velocidad persistente de la demo libre. Los eventos de demo no se modifican.
- Archivos: `frontend/src/app/App.tsx`, `features/mode/ModeCard.tsx`, `domain/simulator.ts`, `infrastructure/http/simulator.ts`, `styles.css`; `backend/src/navira/api/{routes,schemas}.py`, `application/control_simulador_demo.py`, `demo.py`, `simulation/escenarios.py`; pruebas frontend/backend; SPEC-009, ADR-035 y sus índices; PRD/contexto/modos, contrato API, módulos, plan, pendientes, pruebas, trazabilidad, estado e historial.
- Validación ejecutada: suite backend completa 218/218; frontend `npm test -- --run` 90/90 y `npm run build` correcto; `python3 backend/scripts/check_docs.py`, `python3 backend/scripts/check_sdd.py`, `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'` y `git diff --check` pasan. Smoke HTTP `/salud` respondió 200 y `/demo/simulador` indicó control habilitado sin partida activa; la UI Reto se revisó en navegador. El build reporta chunk `mapArea` de 1,065.62 kB (>500 kB).
- Límites: el selector inicia rondas individuales; no encadena 3×5 min, no sostiene el reloj después de la terminación de la población ni exporta reportes persistidos. Eventos programados pueden no aplicarse si la partida termina antes del turno objetivo. Es un control local en memoria, no una ejecución oficial/AWS. Los parámetros indefinidos no se presentan como oficiales.
- Siguiente acción: construir el ejecutor de campaña oficial con secuencia y cronómetro de tres rondas de cinco minutos, espera terminal y reporte por ronda; primero confirmar los criterios que siguen abiertos en P-09/P-15. La implementación actual solo inicia rondas individuales.
- Commits: implementación `ebb4f81`; documentación en un commit separado posterior.

## CAM-087 — Conservar la duración solicitada de la evaluación local

- Fecha: 2026-10-27, Ecuador continental.
- Origen: brecha principal identificada al revisar la duración de rondas; el evaluador pedía 150 turnos, pero detenía la medición cuando la partida sintética terminaba a los 12/15/13 turnos.
- Especificación/requisitos: PRD-06/07/08, TRD-02/06/08/10/11, SPEC-005, P5-01 y T-11. Evidencia parcial; no declara T-11 completa.
- Resultado: el evaluador local completa la ventana `turnos × periodo` aunque la partida termine antes. Slots posteriores al estado terminal se registran explícitamente como ociosos y no envían solicitudes ni fabrican movimientos/rondas. El JSON separa slots solicitados, turnos efectivamente ejecutados, slots ociosos y cumplimiento de duración objetivo.
- Archivos: `backend/src/navira/evaluacion_local.py`, `backend/tests/test_evaluacion_local.py`, `backend/README.md`, módulo backend, pruebas, SPEC-005, trazabilidad, plan, estado, índice e [informe CAM-087](../calidad/resultados/duracion-ronda-cam087.md).
- Verificación: suite focalizada `test_evaluacion_local.py` — 6/6; suite backend completa — 215/215 en 64,291 s; prueba terminal cubre 3 slots ociosos, cero solicitudes y ventana completa. `check_docs.py` correcto (117 Markdown/119 archivos), `check_sdd.py` correcto (8 SPEC), regresiones del validador 8/8, `compileall` y `git diff --check` correctos.
- Límites: completar el reloj no genera carga HTTP ni rondas activas tras el fin de partida. Faltan rondas con actividad suficiente, escenarios oficiales, repeticiones y entorno AWS/evaluación; no se atribuye mejora de latencia, mordidas ni supervivencia.
- Siguiente paso: suite backend completa, validadores docs/SDD, revisar el diff y crear commits separados de implementación y documentación. Después, definir una evaluación que mantenga mundo activo sin alterar reglas terminales y ejecutar T-11 con escenarios/repeticiones oficiales.

## CAM-086 — Reducir trabajo redundante del pronóstico y suavizar turnos

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario de hacer más fluido el ciclo de simulación y reducir la espera entre turnos.
- Especificación/requisitos: PRD-03/10, TRD-05/14, SPEC-002, P3-02/P3-03; la cadencia objetivo de 500 ms sigue pendiente, no se declara cumplida.
- Resultado: agrega distribuciones de caminantes y corredores de igual estado antes de propagar su pronóstico, reutiliza el índice de sobrevivientes por nodo dentro de cada ejecución y cachea el índice inverso del grafo. La equivalencia de exposición de nodos/cruces tiene regresión. No cambia el reloj, orden de turnos ni reglas de resolución.
- Archivos: `backend/src/navira/routing/prediccion.py`, `backend/tests/test_prediccion_rutas.py`; algoritmos, SPEC-002, trazabilidad, pruebas, índice, estado e [informe CAM-086](../calidad/resultados/fluidez-pronostico-cam086.md).
- Verificación: pronóstico (7), planificador (15) y suite backend completa (214) correctos; suite tomó 90,870 s. `python3 backend/scripts/check_docs.py` (116 Markdown/118 archivos), `check_sdd.py` (8 SPEC), sus ocho regresiones, `compileall` y `git diff --check` pasan. Tres rondas en fixture mediano midieron 1,266/1,388/1,443 s bajo contención del backend local; CAM-079 no es comparable.
- Límites: no se afirma que el turno completo sea más rápido ni que alcance 500 ms. No se reinició Uvicorn porque contiene una partida activa en memoria; el backend servido aún no carga esta optimización. Equivalencia funcional no sustituye medición de latencia controlada.
- Siguiente paso: registrar resultados de suite y validadores, revisar diff y separar commits de implementación/documentación. En un reinicio posterior, comparar ronda/etapas con mapa, escenario, población y semilla iguales.

## CAM-085 — Mostrar la ficha del habitante en el panel izquierdo

- Fecha: 2026-10-27, Ecuador continental.
- Origen: aclaración del usuario: la información que desea mover al lado izquierdo es la del habitante seleccionado.
- Especificación/requisitos: PRD-04, TRD-07, SPEC-003 CA-003-06, P4-01 y T-45; continuidad funcional de CAM-083.
- Resultado: `SurvivorRoutePanel` deja de cubrir el mapa y se renderiza debajo de controles/estado de partida en la columna izquierda. Conserva el detalle derivado del snapshot actual, la ruta resaltada, la lista accesible y la selección local; la selección no envía órdenes ni altera el estado del servidor. El estilo adapta las cuatro propiedades a dos columnas en el panel estrecho.
- Archivos: `frontend/src/app/App.tsx`, `frontend/src/features/map/SurvivorRoutePanel.tsx`, `frontend/src/styles.css`; SPEC-003/007, módulo frontend, plan, trazabilidad, índice, estado, reporte e historial.
- Verificación: `cd frontend && npm test -- --run` — 89/89; `npm run build` — correcto, con advertencia existente de bundle cartográfico mayor a 500 kB. `curl` local devolvió 200 para Vite `:5173` y `/salud` en API `:8001`; `:8000` no está escuchando. En una pestaña nueva del navegador se observó el run vivo (turno 242), se seleccionó `S-DEMO-001` desde la lista y el detalle/ruta apareció en la columna izquierda, encima del mapa en viewport de 557 px. Pruebas docs/SDD y `git diff --check` correctas.
- Límites: el panel se ofrece cuando la partida está activa y hay sobrevivientes activos, como antes; los terminales no se seleccionan desde este panel. No se inspeccionó visualmente el breakpoint de escritorio.
- Siguiente paso: inspección visual opcional del layout en escritorio; funcionalmente CAM-085 queda comprobada con selección real del habitante en el panel local.
- Commit individual de implementación: `7c60df1 feat: move resident route details to left panel`. Documentación en commit individual separado.

## CAM-084 — Conservar rutas y replantear ante amenaza cercana

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario para corregir habitantes que dan vueltas sin amenazas cercanas y permitir cambios de ruta cuando un zombie está próximo.
- Especificación/requisitos: PRD-03/10, TRD-14, SPEC-002 CA-002-13, P3-03 y T-46; ADR-034. T-46 queda pendiente de ejecución.
- Motivo: la asignación coordinada se recalculaba en cada snapshot y podía variar por el orden/congestión del grupo, aunque el trayecto seguía legal y no hubiese peligro cercano.
- Resultado: `SnapshotMundo` conserva compromisos de rutas automáticas; el coordinador persiste solo el sufijo que coincide con un movimiento confirmado. El planificador mantiene el trayecto entre snapshots y lo reemplaza cuando encuentra amenaza visible en un radio topológico configurable (inicialmente tres saltos), un cierre que invalida cualquier tramo restante, peligro en el siguiente tramo o desviación. La ocupación/congestión de otros habitantes ya no provoca por sí sola un desvío; rutas con ciclos se descartan. El radio inicial es una decisión de demo, no distancia calibrada ni regla oficial.
- Archivos: modelo de snapshot, planificador, coordinadores automático y humano-NPC, resolución CAS y evaluadores locales/rutas; PRD, TRD, ODDD, reglas, datos, algoritmos, SPEC-002, trazabilidad, ADR-018/019/020/034, pruebas, módulos, plan, índices, estado e historial.
- Verificación: `python3 backend/scripts/check_docs.py` correcto (114 Markdown/116 archivos); `python3 backend/scripts/check_sdd.py` correcto (ocho SPEC estructuralmente válidas); `python3 -m compileall -q backend/src/navira` y `git diff --check` correctos. Smoke manual posterior: se detectó que Uvicorn en puerto 8000 había arrancado antes de CAM-084 y seguía ejecutando código anterior; se levantó el código actualizado en 8001, se conectó Vite a ese backend y se inició un run Manta nuevo. En 14 snapshots consecutivos (20 personas, turnos 8–21 observados) no apareció ningún patrón ABAB en los últimos cuatro nodos; en la muestra las posiciones avanzaban. `/salud` y el estado del simulador respondieron 200/activa. El proceso obsoleto de 8000 fue detenido. No se ejecutaron pruebas de comportamiento T-46 ni se midió mejora de mordidas.
- Límites: la distancia de amenaza se mide en saltos no dirigidos sobre el grafo, no metros; el umbral 3 requiere calibración. Un zombie remoto no causa desvío por sí mismo, aunque un cierre confirmado que afecte cualquier tramo sí invalida de inmediato el compromiso. Persistencia es la del snapshot/repositorio local existente, no persistencia durable entre reinicios.
- Siguiente paso: observar más turnos con una semilla fija y reproducible, ejecutar las pruebas conductuales T-46 (amenaza dentro/fuera del radio, cierres, desviación y ciclos), y evaluar mordidos/evacuados antes de declarar el comportamiento verificado.
- Commit de implementación: `437a84e` (`fix: keep evacuation routes stable between turns`).
- La documentación quedó en un commit individual separado en `master`.

## CAM-083 — Seleccionar habitantes desde el mapa

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario de reemplazar el selector «Ruta observada» por clic sobre el habitante y mostrar sus datos y ruta actual.
- Especificación/requisitos: PRD-04, TRD-07, SPEC-003 CA-003-06, P4-01 y T-45.
- Resultado: los marcadores activos seleccionan un habitante y resaltan su ruta calculada; una ficha superpuesta muestra estado, control, nodo, siguiente paso y destino desde el snapshot actual. El trayecto completo puede expandirse. Una lista expandible conserva selección accesible para marcadores superpuestos. La interacción solo cambia la vista local y no envía órdenes.
- Archivos: `App.tsx`, `CityMap.tsx`, `mapFeatures.ts`, `SurvivorRoutePanel.tsx`, `survivorRoute.ts`, pruebas frontend, estilos; PRD/TRD/contexto, SPEC-003, módulos frontend, T-45, plan, trazabilidad, estado y este historial.
- Verificación: `cd frontend && npm test -- --run` — 89/89 pruebas; `npm run build` — correcto, con la advertencia conocida de bundle cartográfico >500 kB; validadores docs (113 Markdown/115 archivos), SDD (8 SPEC + regresiones 8/8) y `git diff --check` correctos. Smoke browser: clic en marcador seleccionó `S-DEMO-020`; la ficha mostró nodo actual, siguiente paso, refugio R-02 y ruta de 39 pasos; panel en vivo turno 266.
- Límites: la ruta es una recomendación del snapshot y puede cambiar en la siguiente actualización; el mapa puede tener marcadores superpuestos, por lo que permanece una lista alternativa. No modifica la partida ni representa movimiento confirmado.
- Siguiente paso: continuar con el punto de reanudación CAM-066 descrito en `estado-actual.md`.
- Commit de implementación: `81de954` (`feat: select survivors from map`).

## CAM-082 — Cierres aleatorios con alerta cartográfica y rutas actualizadas

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario de sortear 1–10 incidentes al iniciar, alertar en el mapa con un punto amarillo parpadeante, bloquear la zona y redirigir las recomendaciones.
- Especificación/requisitos: PRD-02/03/04, TRD-05/07, SPEC-001 CA-001-11, SPEC-003 CA-003-05, SPEC-007 CA-007-08; P1-05/P4-01/P4-03; T-44; ADR-033.
- Motivo: antes, la demo generaba 1/2/3 cierres según intensidad y el panel solo mostraba metadatos sin ubicación; el backend ya cerraba antes de decisiones, pero el usuario no veía una alerta/punto nuevo.
- Resultado: cada partida con incidentes habilitados sortea uniformemente entre 1 y 10 segmentos físicos disponibles (acotado si el mapa contiene menos), independientemente de intensidad zombie, y los agenda cada tres turnos desde el turno 2. El coordinador conserva orden de aplicación anterior a movimiento zombie/decisiones; el plan vigente del snapshot evita los segmentos cerrados. La proyección expone ubicación WGS84 de un evento solo tras aplicar el cierre. MapLibre añade marcador amarillo con “!” pulsante y un aviso accesible de ocho segundos; movimiento reducido deja el punto estático. No se revela el calendario futuro.
- Archivos: generador de escenarios, proyección y esquema HTTP del panel, pruebas backend/frontend y `CityMap`/GeoJSON/estilos; PRD/TRD/contexto, reglas, flujo, contratos, módulos, SPEC-001/003/007, T-44, ADR-033, plan, trazabilidad, índices, reporte y estado.
- Verificación: backend enfocado (34/34), frontend (87/87), build, `compileall`, comprobadores docs (113 Markdown/115 archivos) y SDD (8 SPEC + regresiones 8/8), y `git diff --check` correctos. Smoke navegador/API local: 20 iniciales, turno 13, cuatro cierres aplicados con ubicación, 19 rutas previstas, alerta accesible del turno 11; snapshot 19 activos/1 evacuado/0 mordidos. Evidencia y límites: [resultado CAM-082](../calidad/resultados/alerta-incidentes-cam082.md).
- Límites: es un cierre vial sintético, no un choque real ni una amenaza natural. El marcador usa el punto medio del segmento OSM, no localización oficial de accidente. Mapas con menos de diez segmentos tienen un máximo menor. No se mide impacto causal agregado en mordidas/evacuados ni rendimiento prolongado.
- Siguiente paso: registrar el commit individual en `master` y dejar el servidor local con la partida de smoke activa para revisión.
- Commit individual en `master`: `beddc56 feat: alert on randomized road incidents`.
- Publicación: `git push origin master` no pudo autenticar; este entorno no dispone de credenciales interactivas. Ambos commits CAM-082 siguen locales.

## CAM-081 — Incidentes viales siempre activos en la demo

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario de ocultar la opción de accidentes viales aleatorios y mantenerla activada siempre.
- Especificación/requisitos: PRD-06, TRD-06/07, SPEC-007 CA-007-05/07, SPEC-001 CA-001-11, P4-03, T-43 y ADR-032.
- Motivo: el menú y API local permitían desactivar cierres viales, contrario al comportamiento solicitado.
- Resultado: se elimina el selector y `eventosCiudad` de `SimulatorSetup`; los inicios/reinicios del control local fuerzan `eventos_ciudad=True`. El esquema HTTP acepta el campo legado marcado obsoleto, pero las rutas lo ignoran, de forma que un cliente que mande `false` tampoco puede apagar incidentes. `crear_contexto_demo` y evaluaciones directas conservan su configuración explícita. La respuesta del control mantiene `eventosCiudad=true` como estado de la demo.
- Archivos: `frontend/src/app/App.tsx`, `application/useSimulator.ts`, `domain/simulator.ts`, pruebas HTTP frontend; `backend/src/navira/application/control_simulador_demo.py`, `api/routes.py`, `api/schemas.py`, `tests/test_control_simulador_demo.py`; ADR-032, ADR-017/021, contrato API, flujos de operador/simulador, SPEC-001/007, T-43, plan, trazabilidad, índices, estado y reporte de evidencia.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_control_simulador_demo -v` — 8 correctas; `cd frontend && npm test -- --run` — 85 correctas; `npm run build` correcto con advertencia de chunk cartográfico >500 kB; `python3 backend/scripts/check_docs.py` (111 Markdown/113 archivos), `check_sdd.py` (8 SPEC), regresiones SDD 8/8, compileall y `git diff --check` correctos. Inspección del navegador confirmó que no hay selector y que el run finalizado registró cierres en turnos 2 y 5.
- Límites: el backend ya arrancado conserva el código anterior mientras mantiene el run finalizado en memoria; la interfaz se actualizó por HMR. El reinicio del backend para cargar la garantía frente a clientes legados queda pendiente para preservar ese resultado local.
- Siguiente paso: recargar el backend en la próxima sesión nueva de simulación.
- Commit individual local: `cf0e742 feat: keep demo road incidents always enabled` en `master`. `git push origin master` no pudo autenticar porque el entorno no dispone de credenciales interactivas; no está publicado.
- Commit: pendiente.

## CAM-080 — Conteo confirmado de mordidos

- Fecha: 2026-10-27, Ecuador continental.
- Origen: reporte del usuario de que el total de mordidos no se reflejaba correctamente y necesitaba un resultado preciso.
- Especificación/trazabilidad: PRD-03/09/10, TRD-14, SPEC-001 CA-001-03/13, T-05/T-06/T-42. No verifica la SPEC completa ni demuestra menor mortalidad.
- Diagnóstico: el total existente del panel ya se derivaba de sobrevivientes en estado `mordido`. La corrida local observada en turno 945 mostró 5 activos, 15 evacuados y 0 mordidos; los estados coinciden con el contador y suman los 20 iniciales. Sin embargo, el contrato no mostraba el número de mordidas de la última resolución, por lo que no permitía distinguir «ninguna mordida nueva» de «total acumulado».
- Cambio: cada snapshot resuelto conserva los IDs mordidos en esa resolución con unicidad validada. El panel publica tanto `mordidos` acumulado desde los estados como `mordidosUltimoTurno`; la UI les da etiquetas distintas. No se cambian las reglas de mordida ni el planificador.
- Archivos: `backend/src/navira/domain/snapshot.py`, `simulation/coordinador.py`, `application/consultar_panel.py`, `api/schemas.py`, pruebas de panel, `frontend/src/domain/panel.ts`, `frontend/src/app/App.tsx`, contrato API, datos, SPEC-001, T-42, trazabilidad y estado.
- Verificación: prueba de integración fuerza dos hordas sobre un sobreviviente, confirma que se muerde una sola vez y contrasta el resultado del resolutor, los estados persistidos y ambas métricas. Backend completo 213/213; `test_panel.py` 14/14; frontend 85/85; `npm run build` correcto con advertencia conocida de bundle cartográfico >500 kB; `check_docs.py` (109 Markdown/111 archivos), `check_sdd.py` (ocho SPEC), regresiones SDD 8/8, `compileall` y `git diff --check` correctos. El parser trata como desconocido (—) el campo por turno cuando conecta con una API previa, sin falsear el valor.
- Límites: la corrida activa observada no tuvo mordidas en su estado actual, por lo que cero es el conteo correcto para esa ejecución. No se reinició el backend para conservar el snapshot volátil activo; por eso el campo nuevo por turno no aparece hasta el próximo reinicio controlado del servidor. La persistencia solo vive en memoria y no conserva resultados al reiniciar.
- Siguiente paso: mantener la partida local actual; reiniciar la API cuando se pueda descartar su estado volátil y verificar que el panel reciba el campo por turno.
- Commit individual local de CAM-080 en `master`. `git push origin master` no pudo autenticar porque el proceso no dispone de credenciales interactivas; no está publicado.

## CAM-079 — Fluidez de turnos y movimientos confirmados

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario de hacer más fluida la partida por turnos y los movimientos, conservando las acciones que corresponden a cada pieza.
- Especificación/trazabilidad: PRD-04/06, TRD-06/07, SPEC-003 CA-003-02, SPEC-007 CA-007-03/06, P4-03/P4-04 y T-41.
- Motivo: la demo local iniciaba en 1× y el frontend cancelaba animaciones activas al recibir snapshots de fase sin movimientos. Además, la ronda medida en el grafo completo tardó más que el intervalo objetivo 4×.
- Resultado: el control local inicia en 4× y conserva 1×/2×/4×; el reloj sigue procesando turnos completos secuenciales sin omisiones. El mapa conserva una trayectoria confirmada entre snapshots y adapta la duración al mayor valor entre periodo nominal y cadencia local observada (ignora huecos mayores a 5 s). Selección de otro run, desaparición/terminalidad de actores y movimiento reducido limpian o evitan interpolación. No cambia reloj oficial ni reglas.
- Archivos: `backend/src/navira/application/control_simulador_demo.py`, `backend/src/navira/application/reloj_simulador.py`, `backend/tests/test_velocidad_simulador.py`, `frontend/src/app/App.tsx`, `frontend/src/features/map/CityMap.tsx`, `mapFeatures.ts` y pruebas; SPEC-003/007, T-41, flujo del simulador/operador, módulo frontend, plan, trazabilidad, índice, reporte y estado.
- Verificación: `cd frontend && npm test -- --run` (83 pruebas); `npm run build` correcto con advertencia de chunk cartográfico >500 kB; suite backend completa 212/212 con `/tmp/navira-env`; test de velocidad 5/5; `check_docs.py` (109 Markdown/111 archivos), `check_sdd.py` (ocho SPEC), regresiones SDD 8/8 y `git diff --check` correctos. El smoke same-origin cambió la partida local activa a 4× y navegador mostró 4×, run activo y mapa cargado. Tres lecturas del control estimaron intervalos de 1,361 y 1,172 s entre turnos, por lo que 4× nominal no fue sostenido bajo esa carga local; la animación se adapta a la cadencia real.
- Límites: muestra breve y hardware local; no mide fotogramas ni valida rendimiento sostenido. Cálculo lento todavía retrasa turnos, nunca los salta. No es una evaluación oficial ni una garantía de cadencia.
- Siguiente paso: inspeccionar visualmente transiciones de varios tipos de actor en el navegador activo y, por separado, optimizar/medir el coste de la ronda si se necesita sostener 4× real.
- Commit: `3cf3a66 perf: smooth local simulation turn playback` en `master`; commit individual de CAM-079.

## CAM-078 — Perímetro de una cuadra alrededor de refugios Manta

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario de impedir que los zombies se acerquen a las zonas seguras dentro de aproximadamente una cuadra por lado.
- Especificación/requisitos: PRD-11, TRD-16, SPEC-001 CA-001-12, ADR-031 y prueba T-40.
- Motivo: antes de este cambio la población inicial podía aparecer junto a los refugios y los caminantes/corredores podían llegar a esos nodos.
- Resultado: partidas Manta calculan el conjunto protegido como nodo del refugio más intersecciones directamente conectadas por calles entrantes o salientes. El generador no coloca zombies en él; el resolutor filtra los destinos de caminantes y corredores y evita que una ruta del corredor atraviese el perímetro. Los cierres temporales no modifican su alcance. Fixtures sintéticos permanecen intactos; una entidad preexistente en el búfer puede quedarse o salir.
- Archivos: `backend/src/navira/domain/mapa.py`, `backend/src/navira/simulation/resolver.py`, `backend/src/navira/demo.py`; `backend/tests/test_resolver.py`, `test_demo.py`, `test_evaluacion_local.py`, `test_simulacion_mapa_manta.py`; PRD/TRD, contexto, reglas, dataset, SPEC-001, trazabilidad, pruebas, módulos, ADR-031, P-17, plan, índice, reporte y estado.
- Decisión: la cuadra se aproxima con un salto topológico porque no hay radio métrico validado por refugio. Una arista OSM no representa siempre la misma distancia. Ver ADR-031.
- Verificación: pruebas focalizadas de resolución/demo (27/27) y suite backend completa (212/212) pasaron. Se alinearon dos expectativas de integración que comparaban la versión recortada jugable con la versión del fixture fuente. `check_docs.py` (108 Markdown/110 archivos), `check_sdd.py` (ocho SPEC estructuralmente válidas), regresiones SDD (8/8) y `git diff --check` pasaron. Smoke local: `/salud`, `/panel/mapa` y `/panel/estado` devolvieron 200; en el turno 5 había 159 zombies visibles y ninguno en los 17 nodos protegidos.
- Límites y pendientes: P-17 queda abierto para calibración geográfica. El perímetro es una regla del juego, no certificación de seguridad real ni sísmica. No cambia la regla de mordida ni garantiza que un sobreviviente quede protegido fuera del modelo.
- Estado: implementación y smoke local verificados; la app quedó activa con una nueva partida. El reinicio del backend perdió la partida efímera anterior.
- Siguiente acción: continuar P1-03; calibrar la equivalencia métrica de una cuadra si se obtiene referencia por refugio. No se solicitó publicación.

## CAM-077 — Ventana urbana como límite jugable

- Fecha: 2026-10-27, Ecuador continental.
- Origen: el usuario pidió que fuera del límite establecido ya no se pudiera jugar. Confirmó que el selector de refugios también debía limitarse al recorte.
- Especificación/trazabilidad: PRD-01, TRD-15, SPEC-008 CA-008-07/09/10, ADR-030, P4-04 y T-39.
- Motivo: CAM-076 restringía cámara y máscara, pero las partidas seguían usando el grafo OSM amplio y el selector admitía nodos exteriores.
- Resultado: el dominio crea una proyección Manta con nodos internos y calles cuyos dos extremos son internos; inicio, zombies, rutas y movimientos usan solo ese subgrafo. Los refugios personalizados exteriores se rechazan antes de iniciar (HTTP 422). `GET /demo/simulador/candidatos` informa los límites y el frontend encuadra, dibuja y permite elegir únicamente dentro de ellos. El fixture fuente OSM no se modifica.
- Alcance medido: fuente 44.590 nodos/94.146 sentidos; proyección 35.518 nodos/75.548 sentidos. La caja `[-80.807, -1.082]`–`[-80.621, -0.897]` es aproximada y no constituye un límite municipal certificado.
- Archivos: dominio `mapa.py`, ensamblaje `demo.py`, API de candidatos, tests de mapa/demo/control, dominio HTTP del frontend y `RefugePicker`; PRD/TRD, mapa, datos, SPEC-008, ADR-030, T-39, módulos, plan, estado y este registro.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest tests.test_mapa_manta tests.test_demo tests.test_control_simulador_demo -v` (25 pruebas correctas); `cd frontend && npm test -- --run` (80 pruebas en siete archivos); `cd frontend && npm run build`; `python3 backend/scripts/check_docs.py` (106 Markdown/108 archivos); `python3 backend/scripts/check_sdd.py` (ocho SPEC); regresiones SDD (8/8) y `git diff --check` correctos. La primera suite frontend detectó un fixture HTTP sin `limitesJugables`; se actualizó y la repetición pasó.
- Prueba local: el selector abrió visualmente encuadrado en el recorte. La API se reinició para cargar la regla, perdiéndose la ronda volátil anterior del turno 147; luego se inició una nueva partida. `GET /panel/mapa` devolvió 35.518 nodos; snapshot observado con 20 sobrevivientes/159 zombies y cero actores referidos fuera del mapa. Run activo en turno 13 al actualizar estado.
- Pendientes: probar un clic real para colocar refugio dentro/fuera; medir payload/cadencia objetivo; auditar calles/cobertura OSM y el fallback del proveedor/WebGL.
- Estado real: implementación, pruebas automatizadas, validadores y mapa en partida local verificados; colocación interactiva puntual pendiente. Evidencia: [reporte CAM-077](../calidad/resultados/limite-jugable-cam077.md).
- Siguiente paso: continuar P4-04 con prueba controlada del fallback WebGL/proveedor y medición del payload en entorno objetivo.
- Commit individual en `master`: `5790135 feat: confine Manta gameplay to urban bounds`; no se publicó a remoto.

## CAM-076 — Enfocar el mapa principal a la ventana urbana de referencia

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario de limitar el mapa al tamaño del recorte de la imagen adjunta.
- Especificación/trazabilidad: PRD-04, SPEC-008 CA-008-06/07/09, P4-04 y T-27/T-38. Sigue vigente el grafo jugable ampliado de CAM-073; el cambio limita cámara/máscara, no contenido del mundo.
- Decisión de encuadre: la captura no trae coordenadas. Se estimó el recorte `[-80.807, -1.082]`–`[-80.621, -0.897]` mediante las posiciones de R-01..R-04 visibles en ella; aproximadamente 20,7 × 20,6 km. No se afirma que sea frontera administrativa.
- Resultado: `CityMap` inicia y limita su navegación/zoom-out y máscara a `MANTA_CITY_VIEW`; «Todo Manta» pasa a «Vista urbana». «Ver partida» acota el foco al viewport. El grafo OSM y el selector de refugios conservan cobertura amplia; personajes fuera del viewport continúan simulándose aunque no aparezcan en el mapa principal.
- Archivos: `frontend/src/features/map/CityMap.tsx`, `mapArea.ts`, `mapArea.test.ts`; SPEC-008, mapa Manta, frontend, T-27, plan, trazabilidad, índice y [evidencia CAM-076](../calidad/resultados/ventana-urbana-cam076.md).
- Verificación: prueba focalizada 8/8; suite frontend 79/79; `npm run build`; `check_docs.py` (104 Markdown/106 archivos); `check_sdd.py` (ocho SPEC); regresiones SDD (8/8) y `git diff --check` correctos. No se verificó visualmente CityMap: no había snapshot/partida activa disponible en el tablero local.
- Límites: límites de la ventana aproximados; los actores fuera de ella no son visibles en el mapa principal. No cambia datos, reglas o posiciones de simulación. No es mapa de evacuación real.
- Siguiente paso: habilitar una partida local con snapshot activo y confirmar en navegador que el recorte y el mar coinciden con la captura; retocar coordenadas solo si la comparación visual lo requiere.
- Commit individual creado localmente en `master`; el intento de `git push origin master` falló por falta de credenciales HTTPS interactivas de GitHub.

## CAM-075 — Mostrar el mar dentro del margen cartográfico

- Fecha: 2026-10-27, Ecuador continental.
- Origen: el usuario reportó que el mapa aparecía igual y que el mar no se reflejaba en el lado derecho.
- Especificación/trazabilidad: PRD-04, SPEC-008 CA-008-07/09, P4-04 y T-27/T-38. Mejora de presentación cartográfica; el mapa y zona jugable completas de CAM-073 no cambian.
- Diagnóstico: el estilo oscuro de OpenFreeMap pintaba agua en `rgb(27,27,29)`, casi indistinguible del fondo; la máscara exterior se calculaba con la caja jugable aunque el límite de navegación ya permitía 5 km por lado, cubriendo los tiles del margen.
- Resultado: las capas `water`/`waterway` y nombres de agua reciben un tono visible. La máscara ahora se construye con el mismo `paddedBounds` del límite de navegación. La función pura `outsideBoundsMask` se prueba junto a `mapArea.ts`; no modifica calles, actores, refugios, rutas ni apariciones.
- Archivos: `frontend/src/features/map/CityMap.tsx`, `mapArea.ts`, `mapArea.test.ts`; SPEC-008, mapa Manta, módulos frontend, T-27/T-38, plan, estado, README de docs y [resultado CAM-075](../calidad/resultados/mar-visible-cam075.md).
- Verificación: `npm test` (77/77), `npm run build`, `check_docs.py` (103 Markdown/105 archivos), `check_sdd.py` (ocho SPEC), regresiones SDD (8/8) y `git diff --check` correctos; se inspeccionó la definición remota del estilo OpenFreeMap. Se levantó la demo Manta usando `/tmp/navira-env`, se comprobó visualmente la costa y el mar azul en el encuadre «Todo Manta» y se dejó la simulación pausada en turno 22.
- Límites: el mar se ve al oeste, donde está la costa de Manta; el este es terreno continental, por lo que no se fabrica una masa de agua en ese lado. El proveedor requiere internet y su geometría/color siguen siendo externos. No se altera el fixture o el espacio jugable.
- Siguiente paso: revisar la app con la corrección; cualquier nuevo ajuste de encuadre puede continuar sobre esta base.
- Commit individual local en `master`. `git push origin master` no se pudo autenticar porque GitHub solicitó credenciales HTTPS interactivas que no están disponibles en este entorno.

## CAM-074 — Limitar la navegación del mapa a 5 km por lado

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario de enfocar más el mapa dejando una extensión de 5 km por lado.
- Especificación/trazabilidad: PRD-04, SPEC-008 CA-008-07, P4-04 y T-38. Es un ajuste visual; no cambia PRD-01 ni la cobertura jugable.
- Resultado: `paddedBounds` convierte 5 km a grados de latitud y longitud según la latitud media de la caja. MapLibre y el selector de refugios comparten ese margen. La caja de 44.590 nodos y 94.146 calles dirigidas, los refugios y los lugares de aparición no se recortan.
- Archivos: `frontend/src/features/map/mapArea.ts`, `mapArea.test.ts`; documentación propietaria del mapa, criterio SPEC-008, T-38, estado e índice; evidencia [CAM-074](../calidad/resultados/margen-navegacion-5km-cam074.md).
- Verificación: prueba focalizada 5/5; suite frontend 76/76; build correcto con el aviso conocido de chunk MapLibre; `check_docs.py` 102 Markdown/104 archivos; `check_sdd.py` ocho SPEC; regresiones SDD 8/8; `git diff --check` correcto. En el navegador local cargaron el fixture y snapshots en vivo, sin errores de consola. No se arrastró manualmente al borde en la inspección visual. Evidencia: [CAM-074](../calidad/resultados/margen-navegacion-5km-cam074.md).
- Límites: los 5 km son una conversión local aproximada sobre una caja rectangular OSM, no una distancia exacta siguiendo el terreno ni una frontera municipal. No se modifican tiles o geometría de juego.
- Siguiente paso: conservar margen de 5 km al modificar futuros encuadres; el mapa jugable continúa incluyendo toda la envolvente CAM-073.

## CAM-073 — Mapa y zona jugable ampliados a la envolvente de Manta

- Fecha: 2026-10-27, Ecuador continental.
- Origen: solicitud del usuario de ampliar a Manta completa también la zona jugable, incluyendo parroquias rurales.
- Especificación/trazabilidad: [PRD-01/04](../producto/PRD.md), [SPEC-001](../metodo/especificaciones/SPEC-001-mundo-simulacion.md), [SPEC-008](../metodo/especificaciones/SPEC-008-mapa-cartografico-3d.md), P1-01/P4-04, T-27/T-38. Decisión [ADR-029](../arquitectura/decisiones/0029-cobertura-y-rutas-mapa-ampliado.md).
- Resultado: extracción Overpass en caja con margen de la relación OSM 112895: 44.590 nodos y 94.146 sentidos dirigidos; 581 nodos desconectados de los refugios excluidos. Artefacto `manta-osm-df97a2f3a878`, hash de respuesta documentado. Mantiene geometría OSM por vértice y sentidos únicos. La caja no es límite municipal certificado.
- Simulación: campo inverso Dijkstra temporal compartido para cohortes con el mismo snapshot/objetivo/cierres/amenazas. Reutiliza búsquedas de rutas, mantiene filtros de peligros visibles, desempate y el escape desde nodo de origen bloqueado. Pronóstico reutiliza objetivo de corredor durante el mismo horizonte; grafo memoiza listas de entradas por cierre y evita construir tuplas completas para nodos sin filtros.
- Frontend: encuadre derivado del grafo más área mínima documentada, controles «Todo Manta»/«Ver partida», máscara y límites de navegación ampliados, selector de refugios compartido, memoización de índice de coordenadas/capas. Nota de producto aclara fuente OSM y uso exclusivo de simulación.
- Pruebas: suite backend completa anterior a GZip: 206 correcta (219,1 s); tras el middleware GZip, 7 pruebas HTTP focalizadas correctas; cobertura del fixture 3, exportador 2 y campo inverso 10 pruebas focalizadas correctas; frontend 75 pruebas en siete archivos; build correcto con advertencia de chunk de mapa de 1,065 kB (289 kB gzip); `check_docs.py` 101 Markdown/103 archivos, `check_sdd.py` ocho SPEC y `git diff --check` correctos. Estos validadores no miden rendimiento.
- Prueba local visual: partida nueva en el frontend recibió `manta-osm-df97a2f3a878`, mostró cuatro refugios, 20 sobrevivientes y controles de encuadre; backend `/panel/mapa` devolvió 20.082.198 bytes por loopback. Simulador pausado después de inspección. La compresión y latencia del payload no se midieron; pendiente prueba de tamaño/cadencia objetivo y proveedor/WebGL.
- Limitaciones: datos/calles de OSM no exhaustivos, muestra de sectores no es auditoría, paths sólo para red pública etiquetada; no se verifica estado real, rutas vigentes, seguridad sísmica ni frontera municipal. Tiles externos requieren internet. No equivale a despliegue.
- Archivos principales: exportador y fixture/sidecar en `backend/`; planificador, pronóstico y adyacencia en `backend/src/navira/`; `frontend/src/features/map/` y `frontend/src/app/App.tsx`; PRD/contexto, docs del mapa, SPEC-001/008, T-38, ADR-029, estado y evidencia.
- Siguiente paso: medir transferencia comprimida, memoria y cadencia del mapa ampliado; evaluar la falla del proveedor y auditar cobertura vial/peatonal. Ver [estado actual](estado-actual.md).

## CAM-072 — Lote 4: F4 (`useGameSession` y reglas puras de juego) y F5 (`mapFeatures.ts`)

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación de la migración de [la guía](../arquitectura/guia-clean-architecture.md) (ADR-025).
- Especificación/tareas: sin SPEC nueva; pasos F4 y F5 de la guía.
- Resultado F4: `domain/game.ts` incorpora funciones puras (`activeGameState`, `findPlayer`, `legalMoves`, `radioSuggestion`, `buildGameOrder`, `remainingMs`, `createActionId`, `classifyGameError`) y errores de dominio (`GameSessionMissingError`, `GameSessionExpiredError`, `GameOrderRejectedError`). `infrastructure/http/game.ts` traduce el status con `httpError`. `application/ports.ts` añade `GamePort`; `application/useGameSession.ts` contiene red, sesión, recuperación y temporizador. `GameControls.tsx` queda como presentación. `App.tsx` compone el hook con `gamePort` (constante de módulo) y `onJoined` estable. Corrección tras revisión: se limpian `pendingOrder` y `activity` al salir de la partida; la sesión se descarta si cambia `runId` o llega 403. Pruebas nuevas de infraestructura (`sendGameOrder`, `restoreGameSession`).
- Resultado F5: `features/map/mapFeatures.ts` (tipos `Position`, `FeatureCollection`, `AnimatedMovement`; `createSimulationFeatures`, `createActorFeatures`, `createMovementAnimations`, `positionAlongPath`, `emptyCollection`) con 9 pruebas en `mapFeatures.test.ts`. Decisión: vive en `features/map` y no en `domain/` por ser proyección a GeoJSON.
- Limpieza: se quitó el código muerto `refreshCount === 0` de `usePanel.ts`; el `Intl.DateTimeFormat` de `App.tsx` es constante de módulo.
- Revisión (datos del orquestador): F4, arquitectura aprobada con observaciones y comportamiento sin hallazgos críticos ni importantes; F5, fidelidad sin cambio visual en el código. Observación aceptada: `GameControls` importa el tipo `GameSessionView` desde `application` (`import type`). Declarado: el hook vive en `App` (la sesión sobrevive al cambio de modo) y el temporizador de 100 ms re-renderiza `App` en modo juego; revisado sin riesgo real.
- Verificación (datos del orquestador): `npm test` 59 pruebas correctas (6 archivos); `npm run build` correcto.
- Validación no ejecutada: revisión visual en navegador de F3, F4 y F5 (no realizada; la debe hacer el usuario); CI remota; los hooks no tienen pruebas unitarias.
- Deuda: `isRecord` duplicado; `import type GameSessionView` en `GameControls`.
- Archivos: `frontend/src/{domain/game.ts,infrastructure/http/game.ts,application/{ports.ts,useGameSession.ts,usePanel.ts},features/game/GameControls.tsx,features/map/{CityMap.tsx,mapFeatures.ts,mapFeatures.test.ts},app/App.tsx}`, guía de Clean Architecture, `docs/arquitectura/modulos/frontend.md`, `docs/calidad/pruebas.md`, estado actual.
- Siguiente acción: ver [estado actual](estado-actual.md).

## CAM-071 — Lote 3: B4 (seguridad e inyección en `api/`), B5 (escenarios) y B6 (visibilidad y puertos de paso)

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación de la migración de [la guía](../arquitectura/guia-clean-architecture.md) (ADR-025). Decisión duradera: [ADR-028](../arquitectura/decisiones/0028-configuracion-de-seguridad-inyectada.md).
- Especificación/tareas: sin SPEC nueva; pasos B4, B5 y B6 de la guía. Sin cambio de códigos HTTP ni del contrato de `POST /paso`.
- Resultado B4a: `api/seguridad.py` (cookie de sesión, comprobación de Origin unificada para `Request` y WebSocket, loopback separado), `api/dependencias.py` (proveedores tipados de `app.state`) y helpers `_error` y `_sesion_expirada` en `api/routes.py`.
- Resultado B4b: `main.py` (`_crear_app_configurada`) lee el entorno una sola vez y pasa `ConfiguracionSeguridad` (frozen, `api_key` con `repr=False`). `crear_app(seguridad=...)` asigna `app.state.seguridad`; sin valor, configuración más cerrada (sin clave, 503 en `/paso`; cookie Secure; control de demo local apagado). `api/` y `evaluacion_local.py` ya no leen `os.environ`; `evaluacion_local.py` pasa su clave explícita (se eliminó `_clave_temporal`). Las pruebas de api_http, planner, demo y control_simulador usan `seguridad=...`. Prueba nueva: 401 antes que 422 en `/paso` sin clave.
- Resultado B5: los escenarios salen de `navira/demo.py` a `navira/simulation/escenarios.py` (`IntensidadEscenario`, `FRACCION_NODOS_POR_INTENSIDAD`, `ESCENARIOS`, `crear_zombies`, `crear_eventos_ciudad`; privadas `_repartir_composicion`, `_seleccionar_nodos_estratificados`). `demo.py` reexporta `IntensidadDemo` y `ESCENARIOS_DEMO`. Hash de `repr(zombies)` y del snapshot idénticos antes y después con la semilla 20261026.
- Resultado B6: `domain/visibilidad.py` (`peligros_visibles`, `nodos_horda_visibles`) y `application/puertos_paso.py` (`PartidaNoDisponible`, `PasoIncompatible`, `EntidadNoEncontrada`, `ProveedorSnapshotsActivos`, `ProveedorMapas`). `application/decidir_paso.py` baja de 574 a 503 líneas y reexporta esos nombres con `noqa F401` (mismos objetos).
- Limpieza: import `os` sin uso fuera de `evaluacion_local.py`; docstring de `main.py` corregido; helper `_leer_parametros_demo`; pruebas nuevas del cableado de `control_demo_local` y del repr; orden de imports en `test_demo.py` y `evaluacion_rutas.py`.
- Revisión (datos del orquestador): B4a arquitectura aprobada, seguridad sin hallazgos medios o altos, calidad sin hallazgos reales. B4b igual (bajo: repr de la clave, corregido; limitación operativa: rotar la clave exige reiniciar). B5 arquitectura aprobada, fidelidad sin hallazgos reales. B6 arquitectura aprobada con observaciones, fidelidad sin hallazgos reales.
- Verificación (datos del orquestador): suite backend 181 pruebas correctas (sin `-v`).
- Validación no ejecutada: CI remota.
- Deuda: los importadores siguen usando la fachada `decidir_paso`; migrarlos y retirar los `noqa` queda pendiente. `ESCENARIOS` es mutable; dos pruebas importan aún desde `simulation.coordinador`; `intensidad: str` en el puerto sin límite de tipo.
- Archivos: `backend/src/navira/{api/{seguridad,dependencias,routes}.py,main.py,demo.py,evaluacion_local.py,evaluacion_rutas.py,simulation/escenarios.py,domain/visibilidad.py,application/{puertos_paso,decidir_paso}.py}`, pruebas de backend correspondientes, ADR-028, `docs/arquitectura/{contratos/api.md,modulos/backend.md,guia-clean-architecture.md}`, `docs/calidad/pruebas.md`, índices, estado actual.
- Siguiente acción: ver [estado actual](estado-actual.md).

## CAM-070 — Lote 2: B3 (sesiones a `adapters/`) y F3 (hooks `usePanel` y `useSimulator`)

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación de la migración de [la guía](../arquitectura/guia-clean-architecture.md) (ADR-025), tras los diagnósticos de `arquitecto-backend` y `arquitecto-frontend`.
- Especificación/tareas: sin SPEC nueva; pasos B3 y F3 de la guía.
- Resultado B3: `RepositorioSesionesMemoria` pasa a `backend/src/navira/adapters/sesiones_memoria.py` sin cambiar su firma. `application/juego.py` ya no contiene la clase ni `_huella`; `UnirseAJuego` tiene el campo final `generar_id_jugador` (`uuid4` por defecto). `secrets.token_urlsafe` y `random.Random()` no se inyectan por decisión (credencial de sesión y rehidratación del RNG del snapshot). `main.py` pasa `reloj_monotonico=time.monotonic`.
- Resultado F3: `frontend/src/application/{ports.ts,usePanel.ts,useSimulator.ts}`. `App.tsx` pasa de unas 300 a 168 líneas y compone los hooks con puertos (constantes de módulo). `SimulatorUnavailableError` traduce el 404. Helpers puros en `domain/panel.ts` (`PanelLog`, `nextPanelLog`, `classifyCursor`, `pickMap`).
- Revisión (datos del orquestador): B3, arquitectura aprobada, calidad sin hallazgos, seguridad sin hallazgos medios o altos (dos bajos: `_expiradas` y `_propietario_por_run` crecen sin límite; `activar_pendiente` no renueva actividad). F3, arquitectura aprobada con observaciones; calidad sin regresiones (menores: `refreshCount === 0` es código muerto heredado, `Intl.DateTimeFormat` por render, `loadMap` sin `signal`).
- Verificación (datos del orquestador): `npm test` 27 pruebas correctas; `npm run build` correcto. Backend: la suite del conjunto completo (con la reversión de [CAM-069](#cam-069--reversión-del-aplanado-de-backendsrc-adr-027)) dio 178 pruebas correctas.
- Validación no ejecutada: revisión manual del tablero en navegador; CI remota; los hooks no tienen pruebas unitarias (decisión: sin testing-library ni jsdom).
- Deuda: los dos hallazgos bajos de seguridad de B3 y las observaciones menores de F3 anteriores.
- Archivos: `backend/src/navira/adapters/sesiones_memoria.py` (nuevo), `backend/src/navira/application/juego.py`, `backend/src/navira/main.py`, `frontend/src/application/`, `frontend/src/domain/panel.ts`, `frontend/src/app/App.tsx`, guía de Clean Architecture, `docs/arquitectura/modulos/{backend,frontend}.md`, estado actual.
- Siguiente acción: B4a en implementación; diagnóstico en curso de F4, F5 y B5; después B4b y B6.

## CAM-069 — Reversión del aplanado de `backend/src` (ADR-027)

- Fecha: 2026-10-26, Ecuador continental.
- Origen: decisión del usuario de volver a la estructura `backend/src/navira/` tras el aplanado de [CAM-067](#cam-067--backend-b1-b2-y-aplanado-de-backendsrc-adr-026).
- Especificación/tareas: sin SPEC nueva. Decisión [ADR-027](../arquitectura/decisiones/0027-reversion-del-aplanado-de-backend.md), que sustituye a [ADR-026](../arquitectura/decisiones/0026-aplanado-backend-y-setuptools.md).
- Resultado: `backend/src/` vuelve a contener solo `navira/` con todo el paquete dentro. El build vuelve a `hatchling` (`packages = ["src/navira"]`), igual que en HEAD. `parents[1]` vuelve a `parents[2]` en `navira/demo.py` (líneas 38-39), `navira/evaluacion_rutas.py` (28) y `navira/evaluacion_local.py` (45). Se conservan los cambios de B1, B2, B3, F1, F2, F3 y F6. CAM-067 queda revertido solo en su parte estructural (aplanado y setuptools).
- Arranque vigente: `cd backend && env NAVIRA_API_KEY=... NAVIRA_DEMO=1 NAVIRA_LOCAL_DEMO_CONTROL=1 .venv/bin/uvicorn navira.main:app --app-dir src` (forma original de HEAD; sin `--app-dir` también funciona).
- Verificación (datos del orquestador): los mapas resuelven con `parents[2]`; suite backend `python -m unittest discover -s tests -p 'test_*.py'` con 178 pruebas correctas (sin `-v`); búsquedas de dependencias de la guía con 0 coincidencias.
- Validación no ejecutada: CI de GitHub con el empaquetado revertido.
- Límites: `backend/navira.egg-info/` es obsoleto y no está versionado; no se tocó. Pendiente de decisión del usuario: ubicación de `main.py` (hoy dentro de `navira/`; confirmar si lo quiere en `src/`).
- Archivos: `backend/src/navira/` (restaurado), `backend/pyproject.toml`, `navira/{demo,evaluacion_rutas,evaluacion_local}.py`, ADR-027 y ADR-026 (estado), índices de `docs/`, guía de Clean Architecture, `docs/arquitectura/modulos/backend.md`, `docs/calidad/pruebas.md`, estado actual.
- Siguiente acción: ver [estado actual](estado-actual.md).

## CAM-068 — Frontend: migración a capas (F1, F2) y pruebas con vitest (F6)

- Fecha: 2026-10-26, Ecuador continental.
- Origen: lote 1 de la migración de [la guía](../arquitectura/guia-clean-architecture.md) (ADR-025), tras el diagnóstico de `arquitecto-frontend`.
- Especificación/tareas: sin SPEC nueva; pasos F1, F2 y F6 de la guía.
- Resultado F1: `fetch('/salud')` sale de `App.tsx` a `frontend/src/infrastructure/http/health.ts` (`checkHealth`).
- Resultado F2: tipos y parsers de `shared/api` y `shared/realtime` pasan a `frontend/src/domain/{panel,game,simulator}.ts`; el `fetch` a `infrastructure/http/{panel,game,simulator}.ts` con errores `GameApiError` y `SimulatorApiError` que conservan el status; el WebSocket a `infrastructure/realtime/panel.ts`. Se borraron `shared/api` y `shared/realtime`; `shared/` solo conserva `ui/BrandMark.tsx`.
- Resultado F6: vitest 5.0.5 (versión exacta) en `frontend/package.json`, script `"test": "vitest run"`, pruebas en `frontend/src/domain/{panel,game,simulator}.test.ts`.
- Verificación (datos del orquestador): `npm test` 19 pruebas correctas; `npm run build` correcto; búsquedas de dependencias (domain sin infrastructure/shared; `fetch` y `WebSocket` solo en `infrastructure/`) con 0 coincidencias indebidas.
- Validación no ejecutada: revisión manual del tablero en navegador tras la migración; lint (no se añadió); CI remota.
- Deuda: `isRecord` está copiado en 6 sitios (aceptado en revisión). Pendientes F3 (`usePanel` y `useSimulator`; diagnóstico en curso), F4 y F5.
- Archivos: `frontend/src/{domain,infrastructure}/`, `frontend/src/app/App.tsx`, `frontend/package.json` y su lockfile, guía de Clean Architecture, `docs/arquitectura/modulos/frontend.md`, `docs/calidad/pruebas.md`.
- Siguiente acción: F3, cuando termine el diagnóstico.

## CAM-067 — Backend: B1, B2 y aplanado de `backend/src` (ADR-026)

- Fecha: 2026-10-26, Ecuador continental.
- Origen: lote 1 de la migración de [la guía](../arquitectura/guia-clean-architecture.md) (ADR-025). El aplanado surgió porque la instalación editable con hatchling copiaba archivos a `site-packages`.
- Especificación/tareas: sin SPEC nueva; pasos B1 y B2. Decisión [ADR-026](../arquitectura/decisiones/0026-aplanado-backend-y-setuptools.md), que sustituye parcialmente a ADR-024.
- Resultado B1: `ControlSimuladorDemoLocal` (`backend/src/application/control_simulador_demo.py`) ya no importa `navira.demo`; recibe una fábrica inyectada (`Protocol` `ContextoSimulacion` y `FabricaContextoSimulacion`, en `application`). `main.py` define `crear_control_simulador_demo(ruta_mapa)` con `functools.partial(crear_contexto_demo, ruta_mapa)`. `test_control_simulador_demo.py` usa esa función.
- Resultado B2: `SnapshotMundo`, `EventoCierre`, `MovimientoZombie` y `EstadoAleatorio` viven en `backend/src/domain/snapshot.py`. `simulation/coordinador.py` los reexporta con `noqa F401`; `simulation/resolver.py` importa `MovimientoZombie` desde `domain`; `application` y `adapters` importan `SnapshotMundo` desde `domain.snapshot`.
- Resultado aplanado: el paquete pasó de `backend/src/navira/` a `backend/src/`; build con `setuptools>=68` y `package-dir = {"navira" = "src"}`; rutas desde `__file__` ajustadas (`parents[2]` a `parents[1]` en `demo.py`, `evaluacion_rutas.py`, `evaluacion_local.py`); se quitaron `--app-dir src` y `PYTHONPATH=src` de los comandos.
- Verificación (datos del orquestador): suite backend `python -m unittest discover -s tests -p 'test_*.py'` con 178 pruebas correctas; arranque `uvicorn navira.main:app` sin `--app-dir`: `/salud` 200 con `{"estado":"activo","servicio":"navira"}` y `POST /paso` sin clave 401; búsquedas de la guía sin coincidencias nuevas.
- Validación no ejecutada: CI de GitHub; no hay mypy en el repositorio.
- Deuda: el puerto declara `intensidad: str` y `crear_contexto_demo` la valida lanzando `ValueError` (límite conocido de B1). Los tests `tests/test_decidir_paso.py:28` y `tests/test_api_planner_integration.py:15` aún importan desde `simulation.coordinador`; quitar el reexport cuando migren. Pendiente B3 (diagnóstico listo, implementación pendiente), B4–B6.
- Hecho: el directorio sobrante `backend/src/navira/` (solo contenía un entorno huérfano, `backend/src/navira/.venv`) se borró con aprobación del usuario. El entorno real `backend/.venv` sigue funcionando: `import navira` resuelve a `backend/src/__init__.py` (dato del orquestador).
- Archivos: `backend/src/` (movido), `backend/src/domain/snapshot.py` (nuevo), `backend/src/application/control_simulador_demo.py`, `backend/src/main.py`, `backend/pyproject.toml`, pruebas, ADR-026 y documentos de arquitectura/calidad/estado.
- Siguiente acción: B3.

## CAM-066 — Subagentes de proyecto y guía de Clean Architecture

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario pidió subagentes de proyecto basados en la documentación para desarrollar más rápido, y una guía para armar backend y frontend en Clean Architecture. Pidió hacerlo primero en `.claude/` y no tocar código.
- Especificación/tareas: sin SPEC nueva; procedimiento SDD. Decisión [ADR-025](../arquitectura/decisiones/0025-agentes-de-proyecto-y-clean-architecture.md), que completa [ADR-023](../arquitectura/decisiones/0023-configuracion-de-agentes.md).
- Resultado: cuatro subagentes en `.claude/agents/` (`arquitecto-backend` y `arquitecto-frontend` en Opus, solo lectura; `revisor-arquitectura` y `documentador-sdd` en Sonnet); guía canónica en `docs/arquitectura/guia-clean-architecture.md` con regla de dependencia, capas objetivo, línea base de violaciones y pasos de migración B1–B6 y F1–F6; skill `navira-clean-architecture`.
- Línea base registrada (2026-10-26): backend, `application/control_simulador_demo.py:11` importa `navira.demo` (violación dura); frontend, `App.tsx:143` hace `fetch('/salud')` desde un componente (violación dura). Violaciones menores en la guía.
- Archivos: `.claude/agents/` (4 nuevos), `.claude/skills/navira-clean-architecture/SKILL.md`, `docs/arquitectura/guia-clean-architecture.md`, ADR-025, índices de `docs/`, enlace en `docs/metodo/SDD.md`, enlaces en `.claude/rules/backend-capas.md`, `.claude/rules/frontend-panel.md`, `.agents/` y `CLAUDE.md`.
- Verificación: `python3 backend/scripts/check_docs.py` correcto (96 Markdown en `docs/`, 98 archivos comprobados); `python3 backend/scripts/check_sdd.py` correcto (8 especificaciones); `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'` correcto; comprobación de enlaces relativos de todos los Markdown del repositorio: 0 rotos (122 archivos); frontmatter de los cuatro agentes y de la skill revisado con `sed`.
- Validación no ejecutada: los subagentes no se han invocado en una sesión nueva; el código no cambió, así que las pruebas del backend y el build del frontend no se repiten.
- Límites: los agentes de `.claude/agents/` se cargan al iniciar sesión y su carga real no está comprobada aquí. La guía describe un destino; el código actual no cumple todavía la regla de dependencia. Cambios sin commit.
- Siguiente acción: abrir una sesión nueva, comprobar que aparecen los cuatro agentes y que `revisor-arquitectura` reproduce la línea base. Después, decidir el primer paso de migración (B1 o F1) con `arquitecto-backend` o `arquitecto-frontend`.

## CAM-065 — Separar backend y frontend en carpetas propias

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario pidió centralizar el backend (`src/`, `data/`, `scripts/`, `tests/`, `pyproject.toml`, `.env.example` y `.venv/`) en una carpeta, separarlo del frontend y dejar en la raíz solo el README general y `.gitignore`. Pidió también un README por área con su arranque y especificaciones, sin perder el contexto del README anterior.
- Especificación/tareas: sin SPEC nueva; ADR-004 y ADR-022 (documentación) y procedimiento SDD. Decisión [ADR-024](../arquitectura/decisiones/0024-backend-y-frontend-por-carpeta.md).
- Resultado: `backend/` contiene `src/`, `data/`, `scripts/`, `tests/`, `pyproject.toml`, `.env.example`, `README.md` y un entorno `.venv/` recreado dentro. La raíz conserva `README.md` general, `.gitignore`, `docs/`, `.agents/`, `.claude/`, `.github/`, `AGENTS.md` y `CLAUDE.md`. `frontend/README.md` reúne arranque, proxy, estructura y especificaciones del tablero. El README raíz pasó a ser índice general.
- Resultado (ajustes): los validadores calculan la raíz del repositorio con `parents[2]`; la CI del backend usa `working-directory: backend` y `cache-dependency-path: backend/pyproject.toml`; los comandos de la configuración y de la documentación vigente se actualizaron a `backend/`; el `readme` de `pyproject.toml` apunta al `backend/README.md`.
- Archivos: `backend/` (movido), `README.md`, `frontend/README.md`, `.github/workflows/ci.yml`, `backend/scripts/check_docs.py`, `backend/scripts/check_sdd.py`, `.agents/`, `.claude/`, `CLAUDE.md`, `AGENTS.md`, `docs/` (enlaces y comandos vigentes), ADR-024 y este registro.
- Verificación: `python3 backend/scripts/check_docs.py` correcto (93 Markdown en `docs/`); `python3 backend/scripts/check_sdd.py` correcto (8 especificaciones); `cd backend && python -m unittest discover -s tests -p 'test_*.py'` con 178 pruebas correctas; `cd frontend && npm run build` correcto (solo el aviso conocido de tamaño de bundle); `backend/.venv` importa `navira`, `uvicorn` y `httpx2`; backend levantado desde `backend/` y `/salud` responde `activo`, con el proxy de Vite llegando a él. Comprobación de enlaces de todos los Markdown del repositorio: 0 rotos.
- Validación no ejecutada: la CI en GitHub Actions (solo se han ejecutado sus comandos en local); la carga del tablero en una sesión de navegador nueva.
- Límites: cambios sin commit. `.venv` antiguo de la raíz eliminado tras comprobar el nuevo. Los archivos `__pycache__` versionados en git (`scripts/` y `tests/`) cambian de ubicación al moverse. `.env.example` quedó dentro de `backend/`; no se comprobó que el backend lo lea automáticamente. Las rutas antiguas se conservan en el texto histórico de CAM, ADR y resultados.
- Siguiente acción: decidir el commit; comprobar la CI en GitHub tras subir los cambios.

## CAM-064 — Reorganizar docs/ por temas y configurar agentes

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario pidió ordenar `docs/` en carpetas con todo su contenido y especificaciones, con `docs/README.md` como índice general que indique dónde está cada documento. Después pidió que las guías por carpeta de código (`src/navira/`, `frontend/`, `tests/`, `scripts/`) estuvieran en una carpeta general `.agents/` en la raíz, y no dentro de cada carpeta.
- Especificación/tareas: sin SPEC nueva; ADR-004 (documentación canónica) y procedimiento SDD. Decisiones [ADR-022](../arquitectura/decisiones/0022-organizacion-documental-por-temas.md) y [ADR-023](../arquitectura/decisiones/0023-configuracion-de-agentes.md).
- Resultado: 87 documentos de `docs/` se movieron a `producto/`, `dominio/`, `arquitectura/`, `metodo/`, `seguimiento/`, `calidad/`, `operacion/` y `referencias/`. `docs/README.md` es el índice general con una sección por carpeta. Los IDs y el contenido de los documentos no cambian.
- Resultado (configuración): `CLAUDE.md` en la raíz importa `AGENTS.md`; `.agents/` contiene las guías de backend, frontend, pruebas y scripts, con su índice; `.claude/` contiene cinco reglas con `paths:`, tres skills y tres comandos. Se eliminaron los `AGENTS.md` y `CLAUDE.md` de las subcarpetas de código.
- Archivos: `docs/` (todo), `scripts/check_docs.py`, `scripts/check_sdd.py`, `tests/test_check_sdd.py` (rutas nuevas), `AGENTS.md` (ruta de inventario y enlace a `.agents/`), `README.md`, `frontend/README.md` (enlaces), `CLAUDE.md`, `.agents/`, `.claude/`, ADR-022 y ADR-023.
- Verificación: `python3 scripts/check_docs.py` correcto (91 Markdown en `docs/`, 93 archivos comprobados); `python3 scripts/check_sdd.py` correcto (8 especificaciones con trazabilidad válida); `python -m unittest discover -s tests -p 'test_check_sdd.py'` correcto (8 pruebas). Comprobación propia de enlaces relativos en los `.md` de la configuración: 0 rotos. Durante la migración aparecieron 9 enlaces rotos, corregidos antes de la verificación final.
- Validación no ejecutada: suite backend completa y `npm run build` (no afectados por este cambio de documentación); no se abrió el tablero en el navegador.
- Límites: cambios sin commit. `docs/` está sin seguimiento en git y `doc/` aparece como borrado. Ejecutar los validadores modificó `scripts/__pycache__/` y `tests/__pycache__/`, que git tiene versionados; no se restauraron. Las guías de `.agents/` no se cargan solas en Claude Code y la configuración no se ha probado en una sesión nueva. Las rutas antiguas se conservan en texto histórico cuando no son enlaces.
- Siguiente acción: decidir el commit y comprobar la carga de la configuración en una sesión nueva.

## CAM-063 — Iniciar la demo en intensidad media

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario indicó que el total evacuado seguía muy bajo. La UI iniciaba en alta, es decir 25 % de nodos elegibles con amenazas, y mantenía incidentes aleatorios activos.
- Especificación/tareas: PRD-06, SPEC-007 CA-007-05, P4-03/T-37; ADR-021. Mantiene escenarios, controles y reglas existentes.
- Resultado: frontend, esquema de inicio y control local omiten el valor alto y comienzan en intensidad media (14 %); eventos siguen activos por defecto y todos los selectores explícitos permanecen disponibles.
- Archivos: `frontend/src/app/App.tsx`, `src/navira/api/schemas.py`, `src/navira/application/control_simulador_demo.py`, `tests/test_control_simulador_demo.py`; ADR-021, SPEC-007, pruebas, plan, estado, índices y [reporte](../calidad/resultados/default-media-cam063.md).
- Verificación: comparación emparejada local en mixto, 20 habitantes, eventos, semillas 101/202/303 y hasta 30 turnos: media 29 evacuados/27 mordidos/4 activos; alta 13/45/2. La diferencia favorece media en los tres pares, pero la muestra de un escenario no predice otras semillas/densidades. T-37 pasa en siete pruebas focalizadas; suite backend completa (178 pruebas), `frontend/npm run build`, validadores docs/SDD, ocho regresiones SDD, `compileall` y `git diff --check` pasan. El build conserva el aviso conocido de bundle MapLibre >500 kB.
- Límites: no cambia la densidad generada ni reglas; métricas son sintéticas y no orientan una evacuación real. El cambio afecta partidas nuevas; se debe iniciar una nueva simulación para aplicar sus defaults. No acredita una mejora universal.
- Commit individual local en `master`: `fix: start demo at balanced threat intensity`.

## CAM-062 — Limitar la exposición sumada al horizonte pronosticado

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario reportó que el total evacuado seguía bajo y pidió continuar mejorando la ruta de evacuación.
- Especificación/tareas: PRD-03/10, TRD-14, SPEC-002 CA-002-12; P3-03/T-36 parcial. No completa T-22, T-11 ni SPEC-002.
- Problema: la coordinación repetía el último valor del pronóstico en cada nodo posterior al horizonte y podía penalizar rutas largas con un riesgo que no había sido modelado.
- Resultado: la política acumula solo exposición explícita por turno pronosticado. Los turnos posteriores quedan sin puntaje de exposición y el costo de ruta determina el desempate disponible; no se consideran seguros por ello.
- Archivos: `src/navira/application/decidir_paso.py`, `tests/test_decidir_paso.py`; SPEC-002, algoritmos, pruebas, trazabilidad, plan, estado y [reporte](../calidad/resultados/horizonte-riesgo-cam062.md).
- Verificación: 13 pruebas focalizadas y suite backend completa (177 pruebas) correctas; `python3 scripts/check_docs.py` (89 Markdown/91 archivos), `python3 scripts/check_sdd.py` (ocho SPEC), ocho regresiones SDD, `compileall` y `git diff --check` correctos. Evaluación local exploratoria con seis pares (semillas 101/202/303, mixto/horda, 20 habitantes, intensidad alta, eventos, hasta 30 turnos): temporal 24 evacuados/74 mordidos/22 activos, Dijkstra 20/77/23. Temporal tuvo mejor prioridad de producto en cuatro pares y peor en dos. La muestra no aísla el cambio causal ni garantiza mejora por semilla; evidencia, comando y límites en [reporte](../calidad/resultados/horizonte-riesgo-cam062.md).
- Límites: el pronóstico sigue siendo aproximado y sintético; no se mide HTTP/p95 ni se valida el futuro sin pronóstico. P3-03 y SPEC-002 permanecen parciales.
- Siguiente paso: CAM-063 baja el valor inicial de la demo a media y conserva los controles manuales de dificultad.
- Commit individual local en `master`: `fix: bound route exposure to forecast horizon`.

## CAM-061 — Coordinar las rutas del grupo por snapshot

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario para implementar una detección de mejores rutas con prioridad en reducir sobrevivientes mordidos.
- Especificación/tareas: PRD-03/10, TRD-14, SPEC-002 CA-002-11; P3-03/T-35 parcial. No completa T-11, T-22 ni SPEC-002.
- Motivo: decisiones aisladas podían dirigir simultáneamente a varios sobrevivientes hacia una misma salida, sin evaluar la congestión de grupo.
- Resultado: `DecidirPaso` cachea una asignación de rutas por `(runId, snapshot, mapa)` y la comparte entre `/paso`, runner y panel. Prioriza exposición visible acumulada; el uso de un destino ya asignado desempata suavemente rutas de riesgo igual. La exposición tiene prioridad sobre congestión y costo; el resolutor sigue decidiendo mordidas/colisiones con sus reglas vigentes. Un superviviente aislado conserva búsqueda temporal completa; para cohortes se usa pronóstico observable con continuación estática en candidatos para acotar fan-out.
- Archivos: `src/navira/application/decidir_paso.py`, `tests/test_decidir_paso.py`; ADR-020, SPEC-002, algoritmos, pruebas, trazabilidad, plan, estado, índices y [reporte](../calidad/resultados/coordinacion-rutas-cam061.md).
- Verificación: 12 pruebas enfocadas `test_decidir_paso.py` pasan, incluido embudo compartido y prioridad de exposición ante congestión. Suite backend completa: 176 pruebas OK. Validadores docs/SDD, ocho regresiones SDD, `compileall` y `git diff --check` correctos. Evaluación fría local sobre Manta/mixto/alta/eventos (semilla 20261026), 20/80/200 tardó 28,73/34,36/92,52 ms de planificación interna. En tres pares de seis turnos (semillas 101/202/303, 20, alta/eventos), coordinación registró 26 mordidos/4 evacuados/30 activos frente a Dijkstra 39/6/15: menos mordidos en los tres pares, pero menos evacuados al turno seis; ver [reporte](../calidad/resultados/coordinacion-rutas-cam061.md). Es muestra exploratoria, no p95 HTTP, ciclo ni efecto causal de la coordinación aislada.
- Límites: el caso de prueba solo acredita descongestión en un embudo; la comparación emparejada reporta la política completa frente a Dijkstra, pero no aísla el aporte causal de coordinación frente a temporal individual. No se modelan capacidades de calles/refugios ni colisiones entre sobrevivientes. La composición es sintética y la predicción aproximada.
- Siguiente acción: ampliar evaluación con más semillas, poblaciones 20/80/200 y horizonte mayor; aislar coordinación frente a política temporal individual y medir HTTP/ronda.
- Commit individual local en `master` con mensaje `feat: coordinate evacuation routes per snapshot`. El push a `origin/master` falló porque Git no pudo solicitar usuario para HTTPS.

## CAM-059 — Alinear la ruta mostrada, la acción y el escape de peligro inmediato

- Fecha: 2026-10-26, Ecuador continental.
- Origen: reporte del usuario: 20 de 20 sobrevivientes mordidos y el indicador de ruta fallando.
- Especificación/tareas: PRD-03/10, TRD-12/14, SPEC-002 CA-002-07..09; P3-03/T-31/T-32/T-33. No completa T-11, T-22 ni SPEC-002.
- Problema observado: el run local `navira-demo-aa0bd0cdb27f41b791e44f07c42983b4` terminó al turno 12 con 20 mordidos, 0 evacuados, 0 activos y 67 zombies visibles. El pronóstico ignoraba cruces futuros del resolutor; ante ausencia de ruta completa, fallback podía dejar quieto a un sobreviviente cuyo nodo ya estaba ocupado; panel y simulador creaban instancias diferentes del planificador.
- Resultado: predicción de exposición a cruces opuestos por arista dirigida; cruce confirmado se limita al paso actual y no se convierte en cierre persistente. El caso sin ruta completa ahora selecciona un vecino legal despejado por riesgo observable próximo y continuidad topológica. El panel y runner comparten una sola instancia de planificador y caché por snapshot/actor, con locks separados por sobreviviente. El evaluador reutiliza el caso de uso de producción y permite configurar intensidad/eventos para reproducir el caso.
- Archivos de código: `src/navira/routing/temporal.py`, `src/navira/routing/prediccion.py`, `src/navira/application/decidir_paso.py`, `src/navira/application/simulacion_automatica.py`, `src/navira/application/control_simulador_demo.py`, `src/navira/evaluacion_rutas.py` y pruebas de rutas, predicción, runner, control y evaluación.
- Documentación: ADR-019, SPEC-002, algoritmos, API, pruebas, trazabilidad, plan, módulos backend, índices, estado actual y [reporte CAM-059](../calidad/resultados/ruta-cruces-cam059.md).
- Evaluación emparejada exploratoria: mixto, 20, intensidad alta, cierres activos, 12 turnos, semillas 101/202/303. Temporal produjo 42 mordidos, 8 evacuados, 10 activos; Dijkstra 48 mordidos, 5 evacuados, 7 activos. Diferencia agregada: −6 mordidos; temporal quedó igual o mejor por mordidos en los 3 pares. No prueba mejora universal. p95 local por recomendación temporal 90,986/90,105/106,752 ms; no es HTTP ni ciclo de 2 s. Métricas de fallback/preparación específicas ahora se informan no disponibles para el evaluador refactorizado.
- Verificación: 43 pruebas enfocadas de ruta/predicción/planificación/runner/control/evaluación y suite backend completa (174 OK tras CAM-060); `cd frontend && npm run build` correcto con aviso conocido de chunk MapLibre >500 kB; `python3 scripts/check_docs.py` (86 Markdown/88 archivos), `python3 scripts/check_sdd.py` (ocho SPEC), ocho regresiones de `test_check_sdd.py`, `compileall` y `git diff --check` correctos. La corrida inicial encontró una expectativa demasiado restrictiva sobre la ruta completa; se ajustó para comprobar el primer movimiento legal y luego pasó la suite completa. El smoke de ruta/mapa está en [reporte CAM-059](../calidad/resultados/ruta-cruces-cam059.md); el defecto de estado terminal descubierto se corrigió en CAM-060.
- Límites: la comparación tiene tres semillas, regla de zombies provisional y fixture parcial. El run inicial del usuario no se puede deshacer; hay que iniciar otra partida para comprobar el código actualizado. No usar como guía real de evacuación.
- Siguiente paso: ampliar la comparación de semillas/duración con configuración alta y eventos, contra Dijkstra.
- Commit individual en `master`: `b6dd754` (`fix: align evacuation route preview and action`).

## CAM-060 — Mantener terminal el estado de evacuación

- Fecha: 2026-10-26, Ecuador continental.
- Origen: prueba manual de CAM-059 con la prioridad explícita del usuario de reducir mordidas; el panel mostró que el contador de evacuados bajaba en rondas posteriores.
- Especificación/tareas: SPEC-002 CA-002-10, P3-03/T-34; corrige implementación de R-11 en `docs/dominio/reglas-juego.md`. No verifica toda la SPEC ni prueba mejora universal.
- Diagnóstico: `_resolver_mordidas()` comparaba movimientos de todos los sobrevivientes con posiciones zombie, aunque la regla vigente dice que evacuados y mordidos dejan de participar. Una horda podía convertir un evacuado en mordido y el estado/estadística retrocedía.
- Cambio: el resolutor limita mordidas a quienes estaban activos al inicio de la fase de decisiones; llegada al refugio permanece resuelta después de las mordidas del mismo turno.
- Código/prueba: `src/navira/simulation/resolver.py`, `tests/test_resolver.py`; regresión verifica que un evacuado en el nodo de una horda siga evacuado en el turno posterior.
- Documentación: reglas, SPEC-002, pruebas, trazabilidad, flujo del simulador, módulo backend, plan, estado e índice de especificaciones.
- Verificación: 12 pruebas de `test_resolver.py`; suite completa 174 OK; build frontend correcto con aviso conocido de chunk MapLibre >500 kB; `python3 scripts/check_docs.py` (86 Markdown/88 archivos), `python3 scripts/check_sdd.py` (ocho SPEC), ocho regresiones del checker, `compileall` y `git diff --check` correctos. Smoke local con semilla 202: el mapa 3D cargó, el panel publicó 20 rutas al inicio y la partida concluyó en turno 18 con 15 mordidos, 5 evacuados y 0 activos. El contador de evacuados no retrocedió durante la observación.
- Límites: no cambia la prioridad del planificador ni prueba por sí solo que se reduzcan las mordidas antes de evacuar. La partida demo observada bajo el resolutor anterior no se puede revertir; iniciar una nueva con el backend actualizado.
- Límites de verificación: una semilla y un smoke local no prueban reducción general de mordidas, T-22 ampliada, latencia HTTP ni operación externa.
- Siguiente paso: ampliar semillas antes de afirmar mejora general; mantener backend y frontend locales activos.
- Commit individual en `master`: creado para CAM-060 (`fix: keep evacuated survivors safe from later bites`).

## CAM-056 — Reducir el encuadre cartográfico a 15 km por lado

- Fecha: 2026-10-26, Ecuador continental.
- Origen: solicitud del usuario para reducir la extensión del mapa a 15 km.
- Especificación/tarea: SPEC-008 CA-008-07, P4-04/T-27; continuidad visual de CAM-055 y ADR-016.
- Motivo: la vista de aproximadamente 50 km por lado dejaba el área central de Manta demasiado pequeña.
- Archivos: `frontend/src/features/map/CityMap.tsx`; mapa Manta, frontend, SPEC-008, ADR-016, plan, pruebas, trazabilidad, índices, estado, resultado e historial.
- Resultado: se configura una ventana aproximadamente 15 km fuera de cada borde del rectángulo OSM de extracción. Límites WGS84: oeste `-80.890`, sur `-1.103`, este `-80.540`, norte `-0.799`. Cámara, máscara y restricciones de pan/zoom siguen usando el mismo rectángulo.
- Límites: el cambio solo modifica el encuadre del basemap; no amplía los 300 nodos/599 aristas del fixture. No es un límite administrativo ni muestra simulación fuera del fixture.
- Verificación: `npm run build` correcto con aviso conocido de chunk MapLibre >500 kB; `python3 scripts/check_docs.py` (80 Markdown/82 archivos), `python3 scripts/check_sdd.py` (ocho SPEC), ocho regresiones del checker y `git diff --check` correctos. El navegador local cargó cartografía/atribución, mostró escala 5 km y mantuvo el zoom-out limitado a la vista general. Evidencia: [reporte CAM-056](../calidad/resultados/reduccion-15km-mapa-cam056.md).
- Siguiente paso: continuar con la prueba controlada del error del proveedor/WebGL (P4-04/T-27).
- Commit: individual en `master` tras validación; revisar historial Git local para el hash.

## CAM-055 — Ampliar el encuadre cartográfico 50 km por lado

- Fecha: 2026-10-26, Ecuador continental.
- Origen: solicitud del usuario para ampliar el mapa unos 50 km por lado.
- Especificación/tarea: SPEC-008 CA-008-07, P4-04/T-27; misma decisión de renderer y recorte visual de ADR-016.
- Motivo: la ventana anterior todavía ofrecía cobertura visual reducida alrededor del fixture vial.
- Archivos: `frontend/src/features/map/CityMap.tsx`; mapa Manta, frontend, SPEC-008, ADR-016, plan, pruebas, trazabilidad, índices, estado, resultado e historial.
- Resultado: el viewport y su máscara abarcan aproximadamente 50 km adicionales en cada dirección cardinal respecto a la ventana previa. Límites WGS84: oeste `-81.219`, sur `-1.434`, este `-80.211`, norte `-0.468`. Se conservan el límite de navegación, el zoom mínimo y la cámara ajustada al área.
- Límites: esto amplía el mapa base, no el grafo Navira; los 300 nodos/599 aristas del fixture quedan en el área central. El rectángulo no es un límite administrativo y la simulación fuera del fixture no está representada.
- Verificación: `npm run build` correcto con aviso conocido de chunk MapLibre >500 kB; `python3 scripts/check_docs.py` (79 Markdown/81 archivos), `python3 scripts/check_sdd.py` (ocho SPEC), ocho regresiones del checker y `git diff --check` correctos. En `http://localhost:5173/` cargaron tiles y atribución, la escala reportó 20 km y el zoom-out quedó deshabilitado en el encuadre general. Evidencia: [reporte CAM-055](../calidad/resultados/ampliacion-50km-mapa-cam055.md).
- Siguiente paso: continuar con la falla controlada del proveedor/WebGL (P4-04/T-27).
- Commit: individual en `master`; la revisión final se identifica en el historial Git local. La publicación remota se comprobará por separado.

## CAM-054 — Ampliar la ventana visual de Manta

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario reportó que la zona del mapa no cargaba correctamente y pidió ampliarla un poco más.
- Especificación/tarea: SPEC-008 CA-008-07, P4-04/T-27; relacionado con ADR-016.
- Motivo: la ventana visual del CAM-053 dejaba poco contexto cartográfico visible en la pantalla estrecha; la máscara ocultaba las áreas exteriores al rectángulo ajustado al fixture.
- Archivos: `frontend/src/features/map/CityMap.tsx`; mapa Manta, frontend, SPEC-008, ADR-016, plan, pruebas, trazabilidad, índices, estado, resultado e historial.
- Resultado: se amplió el rectángulo visual en 0,015° por lado (aprox. 1,7 km), a latitud `[-0.982, -0.920]` y longitud `[-80.770, -80.660]`. Sigue restringido el pan/zoom y la máscara cubre el exterior. No se añadieron calles al fixture ni se afirma el límite administrativo.
- Verificación: navegador local cargó cartografía y mostró los cuatro refugios en la ventana ampliada; `cd frontend && npm run build`, `python3 scripts/check_docs.py` (78 Markdown/80 archivos), `python3 scripts/check_sdd.py` (ocho SPEC), regresiones de `test_check_sdd.py` (8) y `git diff --check` correctos. Evidencia: [reporte CAM-054](../calidad/resultados/ampliacion-mapa-cam054.md).
- Límites: la cobertura del grafo continúa parcial; no prueba cobertura municipal completa, exactitud de calles, seguridad de refugios ni uso de emergencia.
- Siguiente paso: terminar pruebas y commit individual en `master`; luego continuar con la falla controlada del proveedor/WebGL (P4-04/T-27).
- Commit: commit individual de CAM-054 en `master` tras las validaciones; no implica publicación remota.

## CAM-053 — Limitar el mapa al recorte de Manta

- Fecha: 2026-10-26, Ecuador continental.
- Origen: solicitud del usuario para abarcar solo Manta y evitar navegar o mostrar cartografía exterior.
- Especificación/tarea: SPEC-008 CA-008-07, P4-04/T-27; relacionado con ADR-016.
- Motivo: el mapa vectorial podía mostrar áreas exteriores al recorrer la cámara; el encuadre anterior dependía solo de los nodos centrales del fixture y no enmascaraba el basemap.
- Archivos: `frontend/src/features/map/CityMap.tsx`; SPEC-008, ADR-016, mapa Manta, módulo frontend, plan, pruebas, trazabilidad, README, estado, resultado CAM-053 e historial.
- Resultado: se utiliza como límite el rectángulo de extracción OSM del fixture, se ajusta el encuadre completo, se restringe el pan con `maxBounds`, se deshabilita alejar más allá de la vista general, se desactivan copias del mundo y se enmascara el exterior con fondo oscuro. Esto no afirma que el rectángulo sea el límite administrativo oficial ni que el grafo cubra toda Manta.
- Verificación: `cd frontend && npm run build`; recorrido en el navegador local observó mapa y atribución, máscara exterior, arrastre limitado y vistas 3D/2D; demo sintética local de 20 sobrevivientes avanzó hasta el turno 9. `python3 scripts/check_docs.py` (77 Markdown/79 archivos), `python3 scripts/check_sdd.py` (ocho SPEC), regresiones de `test_check_sdd.py` (8) y `git diff --check` correctos. Evidencia: [reporte CAM-053](../calidad/resultados/limites-mapa-cam053.md).
- Límites: fixture parcial, tiles externos requieren conexión y el proveedor no ofrece SLA. La máscara no afecta el mundo ni el grafo. No se verifica límite administrativo, seguridad de refugios, precisión vial ni uso de emergencia.
- Siguiente paso: probar la falla controlada de tiles/WebGL de P4-04; después continuar el recorrido integral del modo humano T-19.
- Commit: commit individual de CAM-053 en `master` tras las validaciones; no implica publicación remota.

## CAM-052 — Movimiento visible de actores y sincronización de nuevos runs

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario reportó que el simulador iniciaba, pero las piezas no se movían visiblemente en el mapa; pidió que el movimiento se entendiera como fichas de un tablero.
- Especificación/tarea: SPEC-008 CA-008-05/06, SPEC-003 CA-003-02; P4-04/T-27.
- Causa encontrada: el WebSocket retenía el proveedor del panel que existía al abrir la conexión. El control local cambia de contexto al iniciar/reiniciar; el socket seguía enviando heartbeats de la partida anterior y el mapa se quedaba obsoleto hasta una lectura HTTP.
- Archivos: `src/navira/api/routes.py`, `tests/test_panel.py`, `frontend/src/features/map/CityMap.tsx`; SPEC-003/008, contrato de eventos, módulos backend/frontend, pruebas, plan, trazabilidad, índice documental, estado, resultado y este registro.
- Resultado: el WebSocket vuelve a resolver el proveedor vigente en cada sondeo. El mapa encuadra el fixture, separa actores en una fuente dinámica y anima entre posiciones de snapshots confirmados durante 1,6 s; fichas azules `S` identifican sobrevivientes y rojas `Z` zombies. Hordas usan ficha propia. La preferencia de movimiento reducido desactiva interpolación y conserva el destino confirmado. El servidor sigue siendo autoridad; no cambian reglas ni contratos de movimiento.
- Verificación: 12 pruebas de `tests.test_panel`; build TypeScript/Vite; recorrido manual en navegador con 80 sobrevivientes que avanzó hasta el turno 11 y mostró fichas sin recargar ni pulsar actualización. `git diff --check` correcto. Evidencia: [reporte CAM-052](../calidad/resultados/movimiento-mapa-cam052.md).
- Límites: entorno local con tiles disponibles; prueba de falla de proveedor/WebGL y cobertura amplia de Manta siguen pendientes. El bundle diferido de MapLibre conserva advertencia >500 kB; la simulación sigue siendo demo sintética y no guía de evacuación.
- Siguiente paso: completar la prueba controlada de error de cartografía de P4-04; después retomar el recorrido humano accesible pendiente T-19.
- Commit: commit individual de fase en `master` tras las validaciones; no implica publicación remota.

## CAM-051 — Cartografía real de Manta con vista inclinada 3D

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario indicó que el mapa actual no le convence y pidió usar cartografía real, de ser posible en 3D; la imagen adjunta se usó como referencia visual, no como especificación técnica.
- Especificación/tarea: SPEC-008, P4-04 parcial; CA-008-01..03 verificados en navegador/build; CA-008-04 implementado, pero la falla controlada aún no se probó. T-27.
- Decisión: [ADR-016](../arquitectura/decisiones/0016-mapa-maplibre-openfreemap.md): MapLibre GL JS + tiles vectoriales públicos OpenFreeMap/OSM; extruir edificios solo si la fuente incluye altura.
- Motivo: el SVG anterior solo unía intersecciones y no mostraba calles circundantes, nombres ni edificios, por lo que la representación parecía abstracta.
- Archivos: `frontend/src/features/map/CityMap.tsx`, `frontend/src/styles.css`, `frontend/src/app/App.tsx` (incluida carga HTTP del snapshot al iniciar), manifiesto/lock npm; documentación de mapa, arquitectura, seguridad, costos, frontend, plan, pruebas, SPEC, trazabilidad, README e índice; reporte CAM-051.
- Resultado: el frontend carga mapa vectorial oscuro de Manta, escala/rotación, vista 2D/3D y volumen de edificios con altura disponible. Las capas de Navira usan snapshots existentes y se renderizan en el cliente; el motor, grafo y contratos no cambian. La carga de MapLibre es diferida.
- Verificación: `cd frontend && npm run build` correcto; navegador local mostró basemap, atribución, edificios elevados y alternancia 2D/3D. El bundle `CityMap` queda en 1.070,25 kB / 290,78 kB gzip y Vite muestra advertencia de chunk >500 kB. Evidencia: [reporte CAM-051](../calidad/resultados/mapa-cartografico-3d-cam051.md).
- Límites: OpenFreeMap público no ofrece SLA y requiere internet; cobertura/alturas de Manta no se auditaron exhaustivamente; las rutas del grafo conectan nodos con segmentos rectos; la falla de tiles/WebGL está implementada pero no fue inyectada en navegador. No es guía de emergencia ni modelo de edificios de alta precisión.
- Siguiente paso: probar un error del proveedor/WebGL y, si se necesita correspondencia exacta ruta-calle, añadir geometría completa OSM al grafo en una fase independiente.
- Commit: `01797e2 feat: render real Manta map in 3D`, commit individual de fase en `master`; no implica publicación remota.

## CAM-050 — Tablero visual y control local del simulador

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario reportó que no podía iniciar el simulador desde el frontend y pidió acercar el diseño a la referencia de control cartográfico.
- Especificación/tarea: SPEC-007, P4-03; CA-007-01..04/T-26; PRD-06, TRD-06/TRD-07.
- Decisión: [ADR-015](../arquitectura/decisiones/0015-control-local-de-demo.md). El control de operador de esta fase es local, opt-in y same-origin; no se crea control de administración público.
- Motivo: el selector anterior solo cambiaba una vista previa y la app base arrancaba sin partida activa. El caso de uso automático no tenía reloj local conectado a controles del panel.
- Archivos: nuevo `ControlSimuladorDemoLocal`, `RelojSimuladorLocal`, rutas `/demo/simulador/*`, esquema de configuración, UI de tablero y cliente frontend, proxy Vite, prueba `test_control_simulador_demo.py`; SPEC-007, frontend/backend, API, arquitectura, seguridad, flujo de operador, plan, pruebas, trazabilidad, README, estado, resultado e índice.
- Resultado: panel de mapa central, controles de escenario/población, iniciar/pausar/continuar/reiniciar, métricas solo del snapshot, refugios representados y feed de snapshots. Una semilla omitida inicia un mundo nuevo. El backend mantiene la autoridad del turno y el panel consulta el mismo `runId`. Sin `NAVIRA_LOCAL_DEMO_CONTROL=1`, el frontend explica cómo habilitar la demo y el API no expone los controles.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_control_simulador_demo.py'` (5); suite Python completa (159); `frontend/npm run build`; `python3 scripts/check_docs.py`; `python3 scripts/check_sdd.py`; suite de `test_check_sdd.py`; recorrido manual en `http://localhost:5173/` inició la partida en Manta y confirmó pausa estable durante 2,5 s. Evidencia detallada: [reporte CAM-050](../calidad/resultados/panel-operador-local-cam050.md). Verificación local, no demuestra despliegue.
- Límites: estado y reloj en memoria de un proceso; las demos son sintéticas y no guía de emergencia. Cadencia sostenida, persistencia, AWS, seguridad de operador público y T-19 integral quedan fuera.
- Siguiente paso: completar el recorrido integral de órdenes y resultado del modo juego (T-19); después continuar medición sostenida P5-01 según sus criterios.
- Commit: un commit individual de fase en `master` tras cerrar validaciones; sin publicación remota.

## CAM-049 — Cobertura HTTP para expiración en las tres rutas

- Fecha: 2026-10-26, Ecuador continental.
- Origen: seguimiento autorizado de CAM-046; verificar el contrato de cookie expirada también al recuperar y enviar órdenes.
- Especificación/tarea: SPEC-004, CA-004-07/T-25.
- Motivo: CAM-046 probó la expiración a nivel de servicio y la ruta de unión; recuperación/acción usan sus propios handlers HTTP y deben conservar el mismo 410 y eliminación de cookie.
- Archivos: `tests/test_juego_sesion.py`, sección de evidencia en `docs/calidad/pruebas.md`, `docs/seguimiento/estado-actual.md` y este historial.
- Resultado: regresiones ASGI con reloj controlado verifican HTTP 410 y `Set-Cookie` de borrado para `GET /juego/mi-personaje` y `POST /juego/accion`; el test de unión también verifica que otra cookie recibe 409 en la partida ocupada.
- Verificación: suite completa (`unittest discover -s tests -p 'test_*.py'`: 154 pruebas OK); `python3 scripts/check_docs.py` (69 Markdown en `docs/`, 71 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho regresiones del checker, `compileall` y `git diff --check` correctos. La suite enfocada de `test_juego_sesion.py` pasó 12 pruebas.
- Límites: adaptador local de un proceso; no valida persistencia/revocación durable ni una cookie en distintos procesos.
- Siguiente paso: terminar el recorrido end-to-end de accesibilidad con una sesión humana en una partida que siga activa.
- Commit: commit individual local en `master` después de las verificaciones.

## CAM-048 — Sincronizar resumen raíz con el estado del juego

- Fecha: 2026-10-26, Ecuador continental.
- Origen: revisión de coherencia documental al continuar P4B-03 después de CAM-046/047.
- Especificación/tarea: SPEC-004 y documentación de incorporación.
- Motivo: el resumen visible al comenzar desde README todavía afirmaba que el juego carecía de radio y expiración local, y el índice de SPEC-004 no registraba CAM-046/047.
- Archivos: `../README.md`, `docs/metodo/especificaciones/README.md` y este historial.
- Resultado: README distingue expiración local de la política productiva pendiente; índice SPEC-004 incorpora evidencia reciente y sus límites.
- Verificación: `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py`, ocho regresiones del checker y `git diff --check`.
- Límites: corrección documental; no cambia ni prueba comportamiento de la app.
- Siguiente paso: completar recorrido end-to-end de teclado/lector de pantalla dentro de una partida activa.
- Commit: commit documental individual local en `master` tras las comprobaciones.

## CAM-047 — Recorrido manual de teclado parcial

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario y siguiente acción de P4B-03/T-19 indicada en CAM-046.
- Especificación/tarea: SPEC-004, P4B-03 parcial; CA-004-06/T-19 parcial.
- Motivo: verificar con entrada de teclado que la navegación inicial y la selección de modo no dependen del mouse.
- Archivos: solo documentación de estado, pruebas, módulos frontend, SPEC y este historial.
- Resultado observado en navegador local: `Tab` enfoca «Saltar al contenido», `Enter` lleva el foco a `main-content`; la navegación secuencial alcanza Simulador/Jugar y `Space` selecciona Jugar, anunciando la experiencia humana. Se comprobó además el enlace de salto en una segunda ejecución local.
- Verificación: recorrido manual mediante navegador local con árbol de accesibilidad; `python3 scripts/check_docs.py` y `python3 scripts/check_sdd.py` se ejecutan para cerrar este registro.
- Límite: el backend en el puerto estándar servía una partida simulador; un backend de juego local llegó al estado terminal antes de completar el flujo. No se probó movimiento humano con teclado, lector de pantalla, WCAG integral, responsive ni estado de expiración. T-19 permanece parcial.
- Siguiente paso: ejecutar recorrido end-to-end con una partida de juego que permanezca activa y validar teclado/lector de pantalla, incluido orden, acuse, llegada y fin.
- Commit: commit documental individual local en `master` tras las comprobaciones.

## CAM-046 — Expiración local de sesión humana

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para avanzar P4B-01/P5-04 y cerrar el vencimiento de sesión pendiente P-12.
- Especificación/tarea: SPEC-004, P4B-01/P5-04; CA-004-07 y T-25.
- Motivo: limitar sesiones abandonadas sin permitir que otra cookie controle o duplique el personaje ya asignado.
- Decisión: [ADR-014](../arquitectura/decisiones/0014-expiracion-local-de-sesion-humana.md), TTL deslizante local de 30 min por defecto, configurable, con HTTP 410 y reserva tombstone no transferible.
- Archivos: `src/navira/application/juego.py`, `src/navira/application/ordenes.py`, `src/navira/api/routes.py`, `src/navira/main.py`, `frontend/src/features/game/GameControls.tsx`, `tests/test_juego_sesion.py`; documentos propietarios de sesión, seguridad, API, frontend, SPEC, plan, trazabilidad, estado e índice.
- Resultado: reloj monotónico inyectable; lecturas/acciones válidas renuevan plazo. Unión/recuperación/acción rechazan la cookie expirada con HTTP 410 y la borran del navegador para permitir entrar en partidas futuras. El tombstone retiene la reserva del `runId` hasta limpieza local explícita; la UI muestra el estado vencido y no ofrece reentrada en la partida actual.
- Verificación: suite backend completa (`unittest discover -s tests -p 'test_*.py'`: 152 pruebas OK); `python3 scripts/check_docs.py` (69 Markdown en `docs/`, 71 archivos), `python3 scripts/check_sdd.py` (6 SPEC), regresiones del checker (8 OK), `compileall`, `git diff --check` y `cd frontend && npm run build` correctos. La primera corrida integral detectó que `HTTPException` descartaba el borrado de cookie del `Response`; se corrigió propagando el header `Set-Cookie` y se repitió el caso enfocado (10 pruebas OK) antes de repetir la suite.
- Límites: adaptador y tombstones son volátiles, sin revocación administrativa, reinicio durable o coordinación multiproceso. No habilita despliegue público ni completa SPEC-004/T-14/T-15/T-19.
- Siguiente paso: recorrido manual T-19 con teclado/tecnologías de asistencia; después diseño e implementación de persistencia durable y recuperación ante reinicio.
- Commit: commit individual local en `master` después de las verificaciones.

## CAM-045 — Accesibilidad de navegación y tiempo de juego

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada de P4B-03/P5-04; revisión de navegación por teclado, foco y estados del juego.
- Especificación/tarea: SPEC-004, P4B-03 parcial; CA-004-06/T-19 parcial.
- Motivo: dar acceso directo al contenido y hacer visibles los estados de foco y reloj sin depender de color ni anunciar cada actualización de 100 ms.
- Resultado: enlace inicial «Saltar al contenido» apunta al panel principal; botones, enlaces y selector tienen foco `:focus-visible`; el token `--dim` alcanza 4,61:1 sobre el fondo `#1c3032`; el reloj conserva lectura visual y anuncia por lector de pantalla solo al quedar medio segundo y al terminar. La ruta de radio tiene respuesta hover.
- Archivos: `frontend/src/app/App.tsx`, `frontend/src/features/game/GameControls.tsx`, `frontend/src/styles.css`; pruebas, frontend, SPEC-004, trazabilidad, plan, estado.
- Decisión: conservar elementos HTML nativos y una actualización accesible por umbrales, manteniendo el countdown de 100 ms solo visual.
- Verificación: revisión de las directrices Web Interface Guidelines y del código; build TypeScript/Vite, validadores docs/SDD y regresiones del checker se ejecutan para cerrar esta CAM.
- Límites: contraste calculado para tokens y fondos base, no auditoría WCAG automatizada; falta recorrido manual con teclado/lector de pantalla en una partida real. T-19 no se marca completo.
- Siguiente paso: ejercicio manual de entrada, reintento, orden y resultado con teclado/lector de pantalla y controles responsive.
- Commit: commit local individual en `master` después de las validaciones.

## CAM-044 — Medición P5-01 extendida de loopback

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada de las fases y criterio de medición P5-01/P2-03.
- Especificación/tarea: SPEC-002, P2-03/P5-01 parcial; CA-002-04/T-11.
- Motivo: comprobar ráfagas HTTP de las cohortes 20/80/200 con el reloj objetivo de 2 s y registrar si la aplicación alcanza 150 turnos.
- Resultado: una matriz pidió 150 turnos por cohorte en mapa Manta sintético, semilla 20261026 y concurrencia configurada 200. Las partidas finalizaron a los 12, 15 y 13 turnos; acumuló 2.072 solicitudes sin error HTTP, p95 18,860/58,097/92,060 ms, ciclos máximos 62,461/218,492/480,701 ms. No se extendió artificialmente el mundo finalizado.
- Archivos: reporte [P5-01 CAM-044](../calidad/resultados/evaluacion-p501-cam044.md), índice, SPEC-002, pruebas, trazabilidad, plan, estado y este registro.
- Verificación: comando `navira.evaluacion_local` ejecutado una vez sobre servidor Uvicorn/cliente loopback; `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py`, ocho pruebas del checker SDD y `git diff --check` correctos.
- Límites: solo 12/15/13 de los 150 turnos solicitados, aproximadamente 80,474 s total, un host/semilla, escenario sintético. No equivale a cinco minutos por cohorte, repetición estadística, T-11 ni AWS; P2-03/P5-01 siguen en curso.
- Siguiente paso: conservar el evaluador fiel al fin de partida; medir rondas oficiales de 150 turnos en el entorno objetivo cuando estén disponibles parámetros y despliegue. Continuar con verificaciones locales accesibles y seguridad de sesión.
- Commit: commit local individual en `master` después de validación.

## CAM-043 — Recuperar la sesión humana al reconectar

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada de las fases; cerrar la recuperación de la UI después de CAM-042.
- Especificación/tarea: SPEC-004, P4B-01/P4B-03/P5-04 parcial; CA-004-02/04, T-13/T-15/T-18.
- Motivo: restaurar la identidad propietaria tras una recarga sin volver a crear un personaje ni tomar la sesión ajena.
- Resultado: `GET /juego/mi-personaje` valida únicamente la cookie opaca existente y devuelve la identidad propia, estado y posición actual del personaje desde el snapshot, además de la última orden del repositorio local. El frontend consulta al seleccionar el modo juego y recupera el personaje; 403 significa que no hay sesión y conserva el botón explícito de entrada. El GET no reserva cupo ni cambia el mundo.
- Archivos: caso de uso de recuperación, puerto/adaptador de órdenes, esquema y ruta API, ensamblaje demo, cliente y controles frontend; contrato, flujo, módulo, pruebas, SPEC-004, trazabilidad, plan, estado.
- Decisión: posición y estado del personaje vienen del mundo confirmado y no del dato inicial de sesión; la orden se presenta como recibida, no como movimiento aplicado. El endpoint es de lectura y la cookie mantiene `SameSite=Strict`.
- Verificación: pruebas enfocadas de órdenes/sesión (19 OK); suite completa backend (149 OK); build TypeScript/Vite; `python3 scripts/check_docs.py` (67 Markdown/69 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho regresiones SDD, `compileall` y `git diff --check` correctos.
- Límites: solo memoria de un proceso; recargar restaura la sesión mientras no se reinicie el servidor. No hay expiración, revocación, store durable, coordinación multi-worker ni prueba manual completa de navegación.
- Siguiente paso: continuar P5-01 con medición extendida local de cadencia; recuperación durable y TLS requieren fase de persistencia/infraestructura.
- Commit: commit local individual en `master` al completar validación.

## CAM-042 — Sugerencia de radio en controles humanos

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada de las fases de Navira y alcance P4B-03/P5-04.
- Especificación/tarea: SPEC-004, P4B-03 parcial; CA-004-05/T-17 y CA-004-06/T-19 parcial.
- Motivo: hacer visible y utilizable en el juego humano la recomendación basada en el mismo snapshot observable del panel.
- Resultado: `GameControls` presenta el siguiente nodo de `rutasPrevistas` para el personaje como sugerencia de Radio Navira. Un botón explícito envía esa orden mediante el flujo existente; no mueve al personaje automáticamente. La UI verifica que la sugerencia empiece en la posición confirmada y corresponda a una calle habilitada, y aclara que no garantiza seguridad.
- Archivos: `frontend/src/features/game/GameControls.tsx`, `frontend/src/styles.css`; flujo del jugador, contrato, módulo frontend, pruebas, SPEC-004, trazabilidad, plan, estado.
- Decisión: reutilizar la ruta prevista ya calculada por el servidor con peligros visibles. No se crea un endpoint adicional ni se calculan rutas privadas en el navegador.
- Verificación: build TypeScript/Vite y validadores documentales/SDD más suite backend completa; no existe runner de componentes ni se declara auditoría WCAG.
- Límites: la UI solo muestra sugerencia mientras hay una ruta válida en el snapshot de decisiones; pueden cambiar los peligros antes de resolver. Sin prueba completa de teclado, lector de pantalla, T-14/T-15 ni resultado integral.
- Siguiente paso: verificar recorrido de reconexión/idempotencia en UI y ejecutar evaluación prolongada local de P5-01; el entorno remoto y la persistencia siguen pendientes.
- Commit: commit local individual en `master` después de las validaciones declaradas.

## CAM-041 — Contador visual del deadline

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada para avanzar las fases y cerrar los criterios del juego humano.
- Especificación/tarea: SPEC-004, P5-04 parcial; CA-004-06/T-19 parcial y TRD-03/05/06/09.
- Motivo: mostrar al jugador cuánto tiempo aproximado queda para registrar su orden, manteniendo el deadline autoritativo en el backend.
- Resultado: `GET /panel/estado` y sus snapshots WebSocket agregan `decisionRestanteMs` durante decisiones en modo juego. La UI estima un contador local, desactiva botones cuando llega a cero y permite que el servidor siga rechazando órdenes por su reloj monotónico; no se calcula usando hora del cliente como autoridad.
- Archivos: `application/puerta_decisiones.py`, `application/consultar_panel.py`, esquema API, frontend `panel.ts`, `GameControls.tsx`, estilos; contratos API/eventos, flujo jugador, frontend backend, SPEC-004, pruebas, trazabilidad, plan, estado.
- Decisión: publicar un restante truncado a milisegundos como dato de presentación. No añade un evento incremental por segundo ni cambia la secuencia del snapshot; la UI hace el decremento visual sobre una duración recibida.
- Verificación: `test_coordinador_juego.py` confirma restante inicial y descendente con reloj controlado; suite enfocada coordinador/panel/demo (22 OK); suite backend completa (147 OK); build TypeScript/Vite correcto; validadores de docs/SDD, ocho regresiones SDD, `compileall` y `git diff --check` correctos.
- Límites: contador puede desviarse por latencia o suspensión de pestaña, no se anuncia cada 100 ms a lectores de pantalla y el servidor siempre decide. Sin auditoría WCAG ni prueba manual completa de teclado; SPEC-004 no se verifica.
- Siguiente paso: completar recorrido accesible y resultado, mantener radio pendiente según alcance, luego evaluar recuperación y seguridad de sesión.
- Commit: commit local individual en `master` después de las validaciones declaradas.

## CAM-040 — Reloj y juego demo local

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para implementar las fases pendientes y mantener commits separados.
- Especificación/tarea: SPEC-004, P5-04 parcial; PRD-05/06, TRD-03/04/05/06/09/12; T-12/T-14/T-15/T-16/T-19 parciales. No verifica SPEC-004 ni completa P5-04.
- Motivo: hacer ejecutable localmente el juego humano sobre el coordinador CAM-039, con cierre de turno autoritativo y recuperación del mismo personaje al volver a unirse.
- Resultado: `PuertaDecisiones` comparte lock y deadline monotónico; rechaza órdenes nuevas al vencimiento y conserva los acuses idempotentes. `RelojJuegoLocal` arranca/detiene con lifespan ASGI, abre ventanas de 1,7 s y alinea ciclos nominales de 2 s. `NAVIRA_GAME_DEMO=1` ensambla juego sintético y servicios efímeros. Vite reenvía `/juego` junto a panel/WebSocket.
- Archivos: coordinador/puerta/reloj de aplicación, ensamblaje `main.py`, `demo.py`, tests del coordinador y `test_demo.py`, `frontend/vite.config.ts`, README raíz/frontend; contratos API, módulos, flujos de jugador/simulador, pruebas, SPEC-004, trazabilidad, plan, pendientes y estado.
- Decisión: el game demo es opt-in y usa mapa sintético, un hilo/proceso, snapshots/sesiones/órdenes en memoria. No altera el modo demo del simulador ni el contrato `/paso`. Cualquier despliegue requiere TLS, expiración/revocación de sesión y almacenamiento/coordinación durables.
- Verificación: suite completa (147 pruebas OK); `frontend/npm run build`; `python3 scripts/check_docs.py` (67 Markdown/69 archivos); `python3 scripts/check_sdd.py` (seis SPEC) y regresiones del validador (8 OK); `compileall`, `git diff --check`. Smoke HTTP ASGI con semilla 45 avanzó de turno 0 a 1 y una segunda llamada a unirse devolvió el mismo `jugadorId`; es una sola ejecución local, no métrica sostenida.
- Límites: no hay temporizador visible en UI, radio, sesión con expiración, recuperación tras caída/reinicio, persistencia durable, multi-worker, TLS/despliegue ni prueba sostenida de cadencia. El fixture demo no representa Manta. P5-04 y T-14/T-15/T-19 permanecen parciales.
- Siguiente paso: completar UI de deadline/resultado y la recuperación tras desconexión; revisar seguridad de sesión y luego retomar P5-02 antes de considerar despliegue.
- Commit: se crea commit local individual en `master`.

## CAM-039 — Integración local del ciclo de juego

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario para avanzar las fases restantes y mantener cambios separados en `master`.
- Especificación/tarea: SPEC-004, P5-04 parcial; PRD-05/06, TRD-03/04/05/06/09/12; T-12/T-14/T-16 parciales. No verifica SPEC-004.
- Motivo: conectar sesión/aparición y órdenes humanas con el ciclo versionado y el mismo resolutor utilizado por los personajes automáticos.
- Resultado: `CoordinadorJuego.preparar()` incorpora una aparición pendiente antes de mover zombies, prepara/retoma decisiones con CAS y no repite movimiento al reintentar. `resolver()` consume la última orden humana aceptada o espera si falta; calcula intenciones de NPC por `DecidirPaso` y confirma una resolución conjunta. `RegistrarOrdenHumana` acepta una puerta `RLock` opcional para que el integrador la comparta y serialice el registro frente al cierre/resolución en un proceso.
- Archivos principales: `src/navira/application/coordinador_juego.py`, `src/navira/application/ordenes.py`, `tests/test_coordinador_juego.py`; SPEC-004, flujo jugador, módulos backend, pruebas, plan, trazabilidad, pendientes y estado actual.
- Decisión: integrar mediante aplicación sobre puertos existentes y CAS, sin duplicar reglas ni modificar el resolutor. No se crea reloj/worker hasta definir e implementar el deadline monotónico. El lock compartido no es multiproceso.
- Verificación: pruebas enfocadas de coordinador y órdenes: 12 OK; suite completa (`PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v`): 146 OK; `python3 scripts/check_docs.py` (67 Markdown/69 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho pruebas `test_check_sdd.py`, `compileall` y `git diff --check` correctos.
- Límites: integración aún no ensamblada en `main.py`/demo; no hay ciclo continuo, plazo 1,7 s, recuperación durable/tras reinicio, T-14/T-15/T-19 integral, radio, TLS ni sesión con expiración. Un método `resolver()` no debe llamarse antes del cierre temporal cuando se añada el runner.
- Siguiente paso: P5-04, implementar ventana monotónica compartida, cierre atómico y runner local opt-in; luego validar reconexión/resultado end-to-end.
- Commit: commit local individual en `master` tras ejecutar las validaciones declaradas.

## CAM-038 — Controles humanos en frontend

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases restantes, con un commit individual por fase en `master`.
- Especificación/tarea: SPEC-004, P4B-03 parcial; inicia evidencia T-19 sin completar T-19 ni verificar la SPEC.
- Motivo: convertir la selección «Jugar» en una interfaz que consuma sesión/órdenes y deje claro el momento en que una intención fue recibida frente al movimiento confirmado.
- Resultado: el panel añade controles de unión, posición propia, espera y vecinos dirigidos habilitados; muestra peligro observable por zombies activos, bloqueos de horda, envío, acuse/error y reintento de red con el mismo `accionId`. Los controles se deshabilitan cuando el snapshot no está fresco o no se aceptan decisiones. La identidad se recupera mediante cookie same-origin HttpOnly, sin guardar token en JavaScript. El modo juego informa que la instancia predeterminada no tiene partida habilitada.
- Decisión: reutilizar el mapa/snapshot de `WS /ws/panel` y los contratos CAM-036/037; no hacer movimiento optimista ni crear partidas desde la selección de modo.
- Archivos: `frontend/src/features/game/GameControls.tsx`, `frontend/src/shared/api/game.ts`, `frontend/src/app/App.tsx`, `frontend/src/styles.css`; módulos frontend, flujo de jugador, pruebas, SPEC-004, trazabilidad, plan, estado e historial.
- Verificación: `frontend/npm run build` compila TypeScript y Vite; suite backend completa (144 pruebas OK); `python3 scripts/check_docs.py` (67 Markdown/69 archivos); `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas); ocho pruebas del validador SDD; `compileall` y `git diff --check` correctos. Smoke de navegador local mostró snapshot real del simulador, selector de modo y estado en vivo. No hubo recorrido de los controles de una partida porque el backend demo no ensambla un modo de juego activo.
- Límites: UI inicial, sin radio ni temporizador/cierre autoritativo; el backend aún no arma el ciclo humano y el endpoint puede responder 503 en la app predeterminada. No se acredita recorrido jugable, T-19 WCAG, durable, reconexión de sesión tras reinicio, seguridad real del mapa ni despliegue.
- Siguiente acción: P5-04, ensamblar un ciclo local modo juego que llame aparición antes de zombies, consuma orden humana junto a órdenes automáticas y publique resultados confirmados; definir cierre monotónico/atómico (P-16) antes de T-14 integral.
- Commit: individual local en `master` después de validaciones locales.

## CAM-037 — Órdenes humanas idempotentes

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases restantes, con un commit individual por fase en `master`.
- Especificación/tarea: SPEC-004, P4B-02; aporta evidencia parcial a T-13/T-14, pero no completa sus criterios ni verifica la SPEC.
- Motivo: recibir intención humana sin confiar en posición/identidad del cliente, permitir reintentos de red y reemplazar una orden válida antes de resolver el turno.
- Resultado: `POST /juego/accion` autentica sesión/origen, comprueba run, personaje humano activo, modo/turno/fase y destino dirigido habilitado. Rechaza cierres topológicos y bloqueos de horda; no rechaza un nodo por riesgo de zombie activo. `OrdenHumana` conserva versión de snapshot; `RepositorioOrdenesMemoria` serializa `accionId`, secuencia creciente por partida y última orden por personaje/turno. Repetir la misma acción y cuerpo devuelve su acuse original; variar cuerpo con la misma clave devuelve 409.
- Decisión: se implementa el contrato existente de [orden humana](../arquitectura/contratos/api.md), sin cambiar el movimiento confirmado ni el orden común de resolución. El repositorio volátil se ubica en `adapters/`; `application/ordenes.py` solo define el puerto y el caso de uso.
- Archivos: `src/navira/application/ordenes.py`, `src/navira/adapters/ordenes_memoria.py`, schemas/ruta/ensamblaje API y `tests/test_ordenes_juego.py`; módulos, contrato, datos, ODDD, flujo, seguridad, pruebas, pendientes, SPEC-004, plan, trazabilidad, estado e historial.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_ordenes_juego.py' -v` (10 OK) y suite completa (`144` pruebas OK); `python3 scripts/check_docs.py` (67 Markdown/69 archivos); `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas); `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 OK); `compileall`, `git diff --check` y `frontend/npm run build` correctos. La salida de uso inválido del CLI es el caso negativo esperado en la suite.
- Límites: el adaptador es memoria de un proceso; el coordinador todavía no consume el resultado ni comparte transacción con las órdenes. El cierre solo se contrasta con la fase actual; no hay deadline monotónico ni cierre atómico contra una solicitud concurrente. No se afirma persistencia durable ni T-14 completo (P-16).
- Siguiente acción: P4B-03, controles y estado de personaje en UI usando la cookie same-origin; luego conectar aparición, bandeja de órdenes y cierre de turno al ciclo de juego antes de afirmar recorrido jugable.
- Commit: individual local en `master` después de validaciones locales.

## CAM-036 — Sesión propietaria y aparición humana local

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario para construir las fases restantes, con un commit independiente por fase en `master`.
- Especificación/tarea: SPEC-004, P4B-01; aporta evidencia parcial a T-12/T-13, pero no verifica la SPEC ni completa T-12/T-13.
- Motivo: habilitar la entrada del jugador humano al modo juego sin aceptar posición del navegador, reservar más de un propietario o revelar información privada de zombies dormidos.
- Resultado: caso de uso `UnirseAJuego`, repositorio local de sesiones que conserva solo hash SHA-256 del token y `POST /juego/unirse` con cookie opaca `HttpOnly`, `Secure` por defecto, `SameSite=Strict`, `Path=/juego` y validación de Origin same-host. La aparición usa RNG privado versionado para escoger un nodo elegible no-refugio, no ocupado por sobrevivientes/zombies activos, no bloqueado y con ruta a refugio. Una entrada posterior a PREPARACION queda pendiente para un hook que el coordinador debe llamar antes del movimiento zombie.
- Decisión: [ADR-013](../arquitectura/decisiones/0013-sesion-y-aparicion-humana-local.md). Un solo propietario humano; sesión y snapshot permanecen en adaptadores separados, locales y volátiles.
- Archivos: `src/navira/application/juego.py`, `src/navira/api/routes.py`, `src/navira/api/schemas.py`, `src/navira/main.py`, `tests/test_juego_sesion.py`; API, datos, ODDD, seguridad, flujo de jugador, módulos, pruebas, SPEC-004, plan, trazabilidad e índices.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_juego_sesion.py' -v` (7 pruebas OK); suite completa (`134` pruebas OK); `python3 scripts/check_docs.py` (67 Markdown/69 archivos); `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas); `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 OK); `compileall`, `git diff --check` y `frontend/npm run build` correctos. La salida de uso inválido del CLI dentro de la suite es el caso negativo esperado.
- Límites: el hook todavía no se invoca desde el coordinador, el modo predeterminado no ensambla el servicio, no existen órdenes/autorización de acciones ni UI jugable, y las sesiones no expiran ni sobreviven reinicios. P-11/P-12 siguen abiertas. La aparición CAS y el repositorio de sesiones no forman una transacción durable.
- Siguiente acción: P4B-02, registro de órdenes humanas con propiedad, fase/turno, idempotencia por `accionId`, sustitución atómica y acuse sin mover directamente al personaje.
- Commit: uno local e individual en `master` después de cerrar todas las comprobaciones locales.

## CAM-035 — Comparación emparejada de políticas de ruta

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario de las fases restantes, con un commit individual por fase en `master`.
- Especificación/tarea: SPEC-002, P3-03 y T-22 parcial; usa P3-01/CAM-033 y P3-02/CAM-034. No completa T-11 ni SPEC-002.
- Motivo: comparar Dijkstra y la candidata temporal bajo mundos emparejados, conservando línea base ante límites o falta de evidencia operativa.
- Resultado: CLI reproducible `python -m navira.evaluacion_rutas`; avanza ambos mundos de forma independiente con misma semilla/perfil/población y un snapshot versionado, calcula recomendaciones desde proyección observable, aplica el mismo resolutor y reporta evacuados/mordidos/activos, fallback y tiempos de funciones.
- Decisión: [ADR-012](../arquitectura/decisiones/0012-seleccion-politica-baseline.md). Dijkstra se mantiene activa en `/paso`; el candidato temporal queda solo en el evaluador hasta reglas y medición HTTP concurrente.
- Archivos: `src/navira/evaluacion_rutas.py`, `src/navira/routing/prediccion.py` (búsqueda de objetivo de corredor acotada por alcance), `tests/test_evaluacion_rutas.py`; pruebas, módulo backend, SPEC-002, plan, matriz, reporte, ADR e índices/estado.
- Verificación/evidencia: 27 pares (3 perfiles sintéticos × 3 semillas × poblaciones 20/80/200), 3 turnos por partida, repetidos dos veces con idénticos resultados de mundo; ver [reporte CAM-035](../calidad/resultados/comparacion-rutas-cam035.md). Temporal sumó 15 evacuados, igualó mordidas; fue mejor en 15 pares, igual en 12, peor en ninguno. Suite completa (`127` pruebas OK), `python3 scripts/check_docs.py` (66 Markdown/68 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructurales), pruebas del validador SDD (8 OK), `compileall`, `git diff --check` y `frontend/npm run build` correctos. Suma de observaciones, no inferencia estadística ni supervivencia.
- Límites: los mundos son sintéticos y cortos; el predictor conserva supuestos provisionales; el tiempo reportado es de funciones locales, no HTTP/latencia concurrente. `2.027` recomendaciones recurrieron a Dijkstra por falta de ruta dentro del horizonte/limitación. T-22 es parcial y T-11 pendiente.
- Siguiente acción: completar validación end-to-end de P3-03/T-11 cuando corresponda, sin activar temporal en `/paso` antes de verificar p95 desde cliente y reglas aceptadas. Después priorizar sesión de juego local, manteniendo AWS/publicación como dependencias externas.
- Commit: individual local en `master`, tras cerrar verificaciones.

## CAM-034 — Pronóstico observable de amenazas por escenarios

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases restantes, con un commit por fase en `master`.
- Especificación/tarea: SPEC-002, P3-02 parcial; enlaza con P3-01/CAM-033 y CA-002-05. La comparación de políticas T-22 queda para P3-03.
- Motivo: proveer condiciones futuras para el buscador temporal sin entregarle fase privada, estado completo de partida o RNG.
- Resultado: pronóstico por fases de ocupación de caminantes, corredores y hordas observables, compatible con `CondicionTurno`. El resultado enumera supuestos y produce un puntaje de exposición, nunca probabilidad calibrada.
- Decisión: [ADR-011](../arquitectura/decisiones/0011-pronostico-visible-por-escenarios.md). Caminantes mezclan fases desconocidas y bifurcan uniformemente por salidas; los corredores persiguen con posiciones actuales de sobrevivientes congeladas; las hordas mantienen bloqueo estático provisional. Dormidos son rechazados.
- Archivos: `src/navira/routing/prediccion.py`, `tests/test_prediccion_rutas.py`, algoritmo, módulos, SPEC-002, plan, trazabilidad, pruebas, ADR e índices.
- Verificación: suite completa (`125` pruebas OK; incluye 5 de pronóstico), `python3 scripts/check_docs.py` (64 Markdown/66 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas), `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 OK), `compileall`, `git diff --check` y `frontend/npm run build` correctos. El mensaje CLI de argumentos inválidos es la salida esperada de una prueba negativa.
- Límites: no usa el estado/RNG privados y no se integra en `/paso`; la salida del corredor presupone sobrevivientes quietos, la horda no se mueve y la mezcla uniforme no valida distribuciones oficiales. No demuestra T-22, supervivencia ni latencia. P3-02 queda parcial hasta cerrar sus dependencias de reglas/evaluación.
- Siguiente acción: P3-03 compara Dijkstra con búsqueda temporal/pronóstico en escenarios y semillas declarados; mantener Dijkstra salvo mejora replicable y dentro del presupuesto.
- Commit: individual local en `master`, al completar verificaciones.

## CAM-033 — Núcleo de búsqueda temporal acotada

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases restantes, con un commit por fase en `master`.
- Especificación/requisitos/tareas: SPEC-002, P3-01, CA-002-05 parcial. P3-02/P3-03, T-11/T-22 y la verificación integral de SPEC-002 siguen pendientes.
- Motivo: explorar planificación por turnos con espera y riesgos observables, con presupuesto explícito, antes de sustituir Dijkstra.
- Resultado: módulo puro de búsqueda temporal `(nodo, turnos)`, acciones de espera/movimiento, cierres y exposición futura inyectados. Costo lexicográfico de exposición, turnos, metros ponderados y desempate estable. Límite de horizonte, expansiones y tiempo; ante agotamiento o falta de refugio en horizonte no se retorna una ruta parcial.
- Decisión: [ADR-010](../arquitectura/decisiones/0010-busqueda-temporal-acotada.md). El módulo no se integra en `/paso`, no genera pronósticos, no consume RNG ni conoce dormidos; Dijkstra permanece como política activa.
- Archivos: `src/navira/routing/temporal.py`, `tests/test_ruta_temporal.py`; algoritmo, módulo backend, plan, SPEC-002, matriz de trazabilidad, pruebas, ADR, reporte e índices/estado.
- Evidencia: [reporte CAM-033](../calidad/resultados/busqueda-temporal-cam033.md), una única medición serial sobre fixture parcial de Manta con escenario sintético `mixto`, semilla `20261026`, horizonte 6 y presupuesto 25 ms. Cohortes 20/80/200: p95 de función 1,331/1,514/1,291 ms; no es HTTP, T-11, T-22, medición de ronda ni evidencia de supervivencia.
- Verificación de cierre: suite completa (`120` pruebas OK; incluye 8 de ruta temporal), `python3 scripts/check_docs.py` (63 Markdown/65 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas), `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 OK), `compileall`, `git diff --check` y `frontend/npm run build` correctos. El mensaje CLI de `argparse` dentro de la suite es una salida esperada de una prueba que verifica argumentos inválidos; la suite termina OK.
- Límites: condiciones futuras son entradas de prueba/puerto, no una predicción implementada; reglas P-02/P-03/P-07/P-09 siguen abiertas. Un horizonte sin ruta no demuestra que el destino sea inalcanzable. P3-01 no termina T-22 ni SPEC-002.
- Siguiente acción: P3-02, construir pronóstico observable sin revelar dormidos ni estado privado, revisando reglas y pendientes; preservar Dijkstra hasta comparar.
- Commit: individual local en `master`, se completa al cerrar verificaciones.

## CAM-032 — WebSocket de snapshots completos y recuperación del panel

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases restantes; un commit separado por fase en `master`.
- Especificación/requisitos/tareas: SPEC-003, P4-02, CA-003-02 y T-15 local. No cierra la SPEC integral ni cubre sesión de juego.
- Motivo: que el panel reciba turnos confirmados y se recupere de desconexiones sin aplicar deltas faltantes o mezclar partidas.
- Resultado: `WS /ws/panel` entrega snapshot observable inmediato y snapshot completo ante cambio de `(runId, snapshotVersion)`, heartbeat cada 2 s y rechazo de handshake con otro/missing origin. Poll de clave cada 250 ms; cada conexión reconectada comienza desde la versión vigente. La UI valida los sobres, aplica secuencia, cambia de run sin conservar el snapshot anterior, presenta conexión/desactualización y usa backoff exponencial. Predicción Dijkstra no se calcula fuera de la fase de decisiones.
- Decisión: [ADR-009](../arquitectura/decisiones/0009-panel-ws-snapshots-completos.md), snapshot completo en vez de delta/buffer porque el almacenamiento actual es en memoria, no outbox durable.
- Archivos principales: `src/navira/api/routes.py`, `application/consultar_panel.py`, `tests/test_panel.py`, cliente React `frontend/src/shared/realtime/panel.ts`, API de mapa, `App.tsx` y proxy; contrato de eventos/API, seguridad, arquitectura, módulos, flujo de espectador, SPEC-003, plan, pruebas, trazabilidad, índice, ADR, README y estado.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py'` (112 pruebas OK); `python3 scripts/check_docs.py` (61 Markdown en `docs/`, 63 archivos); `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas); `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 OK); `compileall`, `git diff --check` y `frontend/npm run build` correctos. Las 12 pruebas enfocadas de `test_panel.py` comprueban snapshot inicial, cambio de versión/fase/run, heartbeat, origen cross-origin y reconexión a secuencia posterior. Smoke visual local a través de Vite/Uvicorn confirmó `EN VIVO`.
- Límites: almacenamiento volátil y único proceso; la conexión requiere mismo host y un Origin browser; no hay outbox, historial de deltas, límites por conexión, multi-worker, sesión/órdenes de juego ni despliegue. No se verificó desconexión real del navegador; el smoke solo comprobó conexión viva. El mapa Manta sigue parcial y no es una guía de emergencia.
- Siguiente acción: P3-01, búsqueda temporal acotada sobre el snapshot/política Dijkstra, manteniendo P2-03 como referencia/evaluación parcial y sin afirmar que la evaluación oficial ya está completa.
- Commit: se crea commit local individual de P4-02 en `master`, después de cerrar suite/validadores.

## CAM-031 — Proyección inicial de mapa y estado para el panel

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de las fases pendientes, con commits individuales en `master`.
- Especificación/requisitos/tareas: SPEC-003 sigue lista; PRD-04/06 y TRD-05/07/09; P4-01 verificado para mapa/capas/ruta/métricas con consulta manual. P4-02/CA-003-02 continúa pendiente. T-04 y primer tramo de ruta tienen regresiones.
- Motivo: alimentar el panel con un snapshot confirmado y una versión de mapa coherente, evitando exponer dormidos o estado privado.
- Resultado: `GET /panel/estado` devuelve sin partida o proyección activa; `GET /panel/mapa` entrega el grafo de la versión activa. Ambas lecturas no requieren API key maestra ni mutan el mundo. La proyección incluye rutas dirigidas completas por sobreviviente activo con la política Dijkstra/peligros visibles compartida con `/paso`. La UI valida formato y versión, permite elegir personaje para dibujar su ruta, presenta modo real del servidor y deja el selector de modo como vista previa.
- Archivos principales: `src/navira/application/consultar_panel.py`, schemas/rutas/API y ensamblaje; `tests/test_panel.py`; `frontend/src/shared/api/panel.ts`, `features/map/CityMap.tsx`, `app/App.tsx`, estilos y proxy Vite. Documentos propietarios: contratos, datos, módulos, espectador, seguridad, pruebas, SPEC-003, trazabilidad, plan, índice, README y estado.
- Decisión/ADR: se sigue la ruta de lectura limitada ya prevista en `docs/arquitectura/contratos/api.md` y el flujo de espectador; no altera `/paso` o el contrato del reto, por lo que no requiere ADR nueva.
- Verificación: suite completa (106 pruebas OK), `python3 scripts/check_docs.py` (60 Markdown en `docs/`, 62 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas) y `python3 -m unittest discover -s tests -p 'test_check_sdd.py'` (8 pruebas OK); `compileall`, `git diff --check`, `npm ci` (24 paquetes, cero vulnerabilidades reportadas) y `npm run build` correctos. Smoke navegador local con Uvicorn/Vite y fixture Manta: muestra versión `manta-osm-d76772f9d9e9`, 300 nodos y 4 refugios. Una medición local única de `consultar_estado()` observó 12,12/42,68/101,47 ms para cohortes 20/80/200; no son percentiles ni medición del endpoint remoto.
- Límites: la fixture tiene cobertura parcial, no certifica seguridad sísmica ni es guía de emergencia. Las rutas se limitan al snapshot y no predicen futuro o garantizan seguridad. No hay consulta automática/WebSocket/reconexión ni endpoint de panel desplegado. El CI remoto no se ejecutó.
- Siguiente acción: P4-02 implementa transporte de eventos/frescura/reconexión; los criterios de actualización en vivo quedan pendientes.
- Commit: commit individual de P4-01 en `master`, registrado tras cerrar sus verificaciones.

## CAM-030 — Base compilable del frontend y CI

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario para avanzar las fases restantes, creando un commit separado por fase.
- Especificación/requisitos/tareas: SPEC-003 lista; PRD-04/PRD-06, TRD-05/07/09; P0-04 verificada por sus criterios locales. CA-003-01..04 permanecen pendientes porque no hay panel conectado.
- Motivo: habilitar una base frontend ejecutable y automatizar verificaciones antes de construir el panel real.
- Resultado: scaffold React + TypeScript + Vite, vista inicial responsiva Navira, selector local de los modos simulador/juego y estado explícito sin partida. La imagen costera es ilustrativa, no cartografía de navegación. Workflow Actions ejecuta suite backend/validadores y build frontend para push a `master` o pull request.
- Archivos: `frontend/` (fuentes, lockfile y guía local), `.github/workflows/ci.yml`, `.gitignore`, README raíz, módulos frontend, pruebas, SPEC índice, plan, estado e historial.
- Decisión: sin ADR; no se cambia arquitectura documentada ni contrato, y se conserva React/TypeScript/Vite previsto. Leaflet continúa pendiente para mapa interactivo.
- Validación: `npm ci` y `npm run build` (correctos; 24 paquetes, cero vulnerabilidades reportadas); suite completa backend (100 pruebas); `python3 scripts/check_docs.py` y `python3 scripts/check_sdd.py` correctos; revisión del árbol de accesibilidad y captura local en viewport móvil. `git diff --check` se ejecutará al cierre.
- Validación no ejecutada: workflow remoto porque el cambio aún no está publicado; no se afirma CI de GitHub exitoso.
- Límites: selector solo cambia copy; no inicia partidas ni consume `/panel/estado`, `/panel/mapa` o WebSocket. No se implementa mapa vivo, controles, sesión o comportamiento offline.
- Siguiente acción: diseñar P4-01 contra snapshot/proyección observable y contratos reales existentes, preservando ocultamiento de dormidos; seguir con un commit independiente por fase.
- Commit: se registra después de cerrar y verificar la fase.

## CAM-029 — Evaluador HTTP con cadencia configurable

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario; siguiente paso de CAM-028 para medir el evaluador con el período de dos segundos que requiere T-11.
- Especificación/requisitos/tareas: SPEC-002, CA-002-04 parcial, P2-03 y P5-01 en curso; T-11 parcial. No verifica la SPEC.
- Base Git: `master`, commit `4f943d8`; conserva el commit CAM-028 separado.
- Resultado: `evaluacion_local.py` programa inicios con reloj monotónico, admite `periodo_segundos`/`--periodo-segundos` (2 s por defecto), y reporta intervalos, retrasos y duración/cumplimiento del período por turno. Las solicitudes siguen leyendo una sola versión por turno y se resuelven después de la tanda HTTP.
- Archivos: `src/navira/evaluacion_local.py`, `tests/test_evaluacion_local.py`; documentos propietarios del módulo, pruebas, plan, SPEC-002, trazabilidad, índice, estado y [reporte CAM-029](../calidad/resultados/evaluacion-cadencia-cam029.md).
- Evidencia local: tres turnos por cohorte 20/80/200 con mapa `manta-osm-d76772f9d9e9`, escenario sintético `mixto`, semilla `20261026`, concurrencia máxima 200 y cadencia 2 s. 877 solicitudes, cero fallos HTTP, p95 18,017/54,593/103,734 ms, ciclos máximos 59,078/207,267/479,105 ms y retraso máximo de inicio 0,176/0,072/0,074 ms. Los datos completos y límites están en el reporte.
- Límites: corrida local única y corta; no son 150 turnos, no dura cinco minutos por ronda, no usa poblaciones oficiales de zombies ni cliente remoto/AWS. No verifica T-11 ni latencia sostenida, supervivencia general, persistencia durable, cartografía para uso real o seguridad sísmica. P-07 y P-09 siguen abiertos.
- Verificación: prueba enfocada `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_evaluacion_local.py' -v` (5 pruebas correctas); suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (100 pruebas correctas); `python3 scripts/check_docs.py` (60 Markdown en docs/, 62 archivos comprobados); `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas); `PYTHONPATH=src /tmp/navira-env/bin/python -m compileall -q src tests` y `git diff --check` correctos. Corrida CLI guardada temporalmente en `/tmp/navira-evaluacion-local-cam029.json`; el resumen versionado está en el reporte. El cambio quedó en un commit individual local. `git push origin master` no pudo leer credenciales HTTPS; la conexión GitHub también rechazó crear el árbol remoto con HTTP 403 `Resource not accessible by integration`. `git ls-remote` confirmó que `origin/master` permaneció en `fa7ebd8`; no se afirma publicado.
- Siguiente paso: cerrar P-09/parámetros de escenario antes de identificar poblaciones oficiales; luego ejecutar 150 turnos por ronda y medir en el entorno de evaluación. Mientras tanto el evaluador admite `--turnos 150 --periodo-segundos 2`, pero una corrida local no cierra la evaluación oficial.

## CAM-028 — Evaluación HTTP multi-turno en Manta

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario; siguiente acción de CAM-025/estado actual para medir `/paso` mientras el mundo avanza.
- Especificación/tareas: SPEC-002, P2-03 y T-11 parciales; CA-002-04 parcial. No se verifica T-11 ni toda la SPEC.
- Base Git: el usuario confirmó publicación y `git ls-remote` verificó que `origin/master` coincidía con `fa7ebd8` antes de esta tarea. El trabajo se realiza directamente en `master`, como pidió el usuario.
- Resultado: nuevo CLI local crea contexto sobre el fixture Manta, sirve FastAPI con Uvicorn en loopback, consulta por HTTP a cada sobreviviente activo de cada turno y resuelve usando los destinos recibidos. Cada turno comparte snapshot; las fallas se contabilizan y se convierten en espera para completar la transición. La API no adquiere rutas nuevas. Se usa una clave aleatoria temporal que no se imprime.
- Archivos: `src/navira/evaluacion_local.py`, `src/navira/carga_http.py`, `tests/test_evaluacion_local.py`; documentos propietarios de pruebas, módulos, plan, SPEC-002, índice, estado y reporte en [resultados](../calidad/resultados/evaluacion-multi-turno-cam028.md).
- Evidencia: una matriz de cinco turnos por cohorte con semilla `20261026`, perfil sintético `mixto` y hasta 200 workers produjo 91/374/911 solicitudes para 20/80/200 personas, todas HTTP 200 y 0 fallidas. p95 local: 20,712/52,781/109,847 ms. Duración total por cohorte: 0,320/0,809/1,841 s.
- Límites: Uvicorn y cliente comparten host; no se espera el período de 2 s ni se ejecutan cinco minutos/rondas oficiales. No acredita p95 desplegado, T-11, supervivencia general, distribución oficial, exactitud cartográfica ni seguridad ante tsunami/sismo. T-11 y P2-03 siguen en curso.
- Verificación: `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (98 pruebas OK); incluye integración HTTP real, avance de versión y replay de resultados del mundo con la misma semilla. `python3 scripts/check_docs.py` (59 Markdown en docs/, 61 archivos), `python3 scripts/check_sdd.py` (seis SPEC), `compileall` y `git diff --check` correctos. La matriz CLI produjo el reporte resumido versionado; JSON íntegro temporal en `/tmp/navira-evaluacion-local-cam028.json`. El commit local se creó, pero `git push origin master` falló porque Git no pudo leer credenciales HTTPS; el remoto sigue en `fa7ebd8`.
- Siguiente paso: publicar el commit local CAM-028 cuando se restablezca autenticación de escritura; después medir con reloj real y duración requerida al confirmar parámetros P-09 y repetir desde el entorno remoto antes de afirmar objetivos de rendimiento.

## CAM-027 — Continuar en `master` y preservar commits por cambio

- Fecha: 2026-10-26, Ecuador continental.
- Origen: ante la falta de autenticación para publicar `main`, el usuario elige `master` y pide mantener un commit separado por cada cosa implementada.
- Resultado: `master` local avanzó en fast-forward hasta el historial completo. Se eliminaron las ramas locales `feat/navira-*` y `main` después de confirmar que sus commits son ancestros de `master`. El remoto no se ha modificado.
- Granularidad: se conservaron los commits ya existentes, uno por fase/cambio; no se hizo squash ni se reescribió el historial. `git log --reverse origin/master..HEAD` mostró los 21 commits locales previos a esta entrada; CAM-027 agrega un commit documental aparte.
- Verificación: estado limpio antes de documentar, avance fast-forward y revisión del historial con `git log --oneline --reverse origin/master..HEAD`. El push de prueba sigue limitado por la falta de credenciales registrada en CAM-026.
- Pendiente: publicar `master` cuando GitHub esté autenticado con permiso de escritura. El remoto aún está en `6e3e9c02e21e64c25b185b14ac5544bdf69dab99`.

## CAM-026 — Consolidación local en `main` y publicación pendiente

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario pide eliminar ramas de fase, trabajar directamente en `main` y subir los cambios.
- Motivo: centralizar en `main` el historial de implementación ya integrado y ajustar el flujo de trabajo según la instrucción actual.
- Resultado local: se creó `main` desde `e5e9e749adb93af73dbcdd095fe8cb2d8d23042b`; incluye los 20 commits posteriores a `master`. No se creó un commit de merge porque la rama de trabajo ya descendía directamente de `master`.
- Verificación remota: el remoto solo tiene `master` en `6e3e9c02e21e64c25b185b14ac5544bdf69dab99`. `git push --set-upstream origin main` falló porque Git no pudo solicitar credenciales HTTPS en esta sesión. La integración GitHub conectada rechazó crear `main` con HTTP 403 y el navegador no tiene sesión iniciada.
- Límite: `main` aún no está en GitHub ni es rama predeterminada; no se eliminó `origin/master`. La eliminación de ramas locales se completa después de registrar este cambio y verificar que todas estén contenidas en `main`.
- Siguiente paso: habilitar una sesión GitHub con escritura, publicar `main`, cambiar y comprobar la rama predeterminada, y luego borrar las referencias obsoletas según [estado actual](estado-actual.md).

## CAM-001 — Análisis y plan inicial

- Fecha: 2026-10-26.
- Origen: el usuario solicita analizar el reto y preparar un plan de implementación.
- Motivo: convertir requisitos, rúbrica y plazo en una solución construible.
- Resultado: propuesta de núcleo de rutas, simulador, stack AWS y fases; archivo original preparado en `docs/PLAN_IMPLEMENTACION.md`, ahora conservado como [referencia histórica](../referencias/plan-previo.md).
- Decisiones relacionadas: ADR-001 y ADR-003, formalizadas después.
- Verificación: lectura del reto y creación del documento. Ninguna aplicación, prueba de carga o infraestructura ejecutada.
- Pendiente: construir la base y comprobar accesos, reglas ambiguas y costos reales.

## CAM-002 — Incorporación de juego humano

- Fecha: 2026-10-26.
- Origen: el usuario pide entrar al simulador como personaje aleatorio y mantener ambos modos.
- Motivo: añadir una experiencia interactiva distintiva sobre el mismo motor.
- Resultado: se amplía el plan con control humano, aparición, sesión, órdenes por turno, radio y métricas separadas.
- Decisión relacionada: ADR-002; un jugador por partida es el límite inicial de diseño, no una implementación multijugador.
- Verificación: revisión y actualización documental; sin código de juego.
- Pendiente: implementar control y probar que no cambia las reglas de simulación.

## CAM-003 — Documentación modular y entrada para agentes

- Fecha: 2026-10-26; concluido después de la instrucción «continúa» que retomó la misma tarea.
- Origen: el usuario pide `../producto/contexto.md`, arquitectura, flujos por rol, documentación modular de todo el proyecto y un `AGENTS.md` que ordene revisar los Markdown de `docs/`.
- Motivo: conservar intención, responsabilidades y contexto de cada cambio aunque se cambie de agente o se interrumpa una sesión.
- Archivos: `../README.md`, `AGENTS.md`, documentos indexados en [docs/README.md](../README.md), enlace compatible `docs/PLAN_IMPLEMENTACION.md` y `scripts/check_docs.py`.
- Resultado: contexto/estado separados, reglas y flujos, módulos, API/eventos/datos, algoritmos, infraestructura, seguridad, costos, pruebas, plan vigente, pendientes, ADR, plantillas e historial. Se preservan fuente del reto y plan anterior sin convertirlos en contratos vigentes.
- Decisión relacionada: ADR-004. La documentación canónica usa `docs/`, en singular.
- Verificación: comprobador local de enlaces e inventario y comparación de la copia del reto con el adjunto; resultados finales en [estado actual](estado-actual.md). No se ejecutaron pruebas de aplicación porque no existe implementación.
- Limitaciones: Budget, recursos, URLs, código, rendimiento y remoto Git siguen sin verificar. Los flujos y tecnologías describen diseño, no servicios existentes.
- Siguiente acción: P0-01 y P0-02 del [plan](plan-implementacion.md); configurar Budget cuando haya acceso autorizado.

## CAM-004 — Incorporación PRD, TRD, ODDD y SDD

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario solicita implementar las cuatro prácticas y confirma ODDD como OO + DDD.
- Especificación: SPEC-006; requisito TRD-13; tareas M0-01 a M0-04. No se implementan funcionalidades del juego en esta intervención.
- Motivo: enlazar necesidades, restricciones, dominio, criterios, tareas, pruebas y evidencia sin duplicar arquitectura/roadmap/bitácora.
- Archivos: PRD/TRD/ODDD/SDD, seis SPEC con índice y matriz, dos plantillas, ADR-005, referencia de propuesta, validación `scripts/check_sdd.py` y sus regresiones. Se actualizan AGENTS, índice, contexto, continuidad, plan, pruebas y enlaces de modelo/arquitectura.
- Decisiones: conservar stack, `docs/`, roles y ambos modos; flujo reducido para cambios pequeños y autorización persistente sin aprobaciones rutinarias repetidas. No instalar skills/hooks/frameworks ni crear agentes por seguir una plantilla.
- Verificación: validadores documentales correctos, seis SPEC con trazabilidad válida, ocho regresiones correctas y copia exacta de la propuesta SDD. Revisión de criterios y comandos en [evidencia de SPEC-006](../calidad/resultados/verificacion-sdd.md).
- Discrepancia encontrada: la ruta antigua `docs/PLAN_IMPLEMENTACION.md` ya no existe; se corrigen afirmaciones vigentes del índice/AGENTS sin recrear una carpeta paralela. El plan histórico se conserva y no se reescriben entradas anteriores para ocultar la diferencia.
- Límites: comprobar estructura no verifica app, latencia, seguridad desplegada ni factura. Funcionalidades SPEC-001 a SPEC-005 permanecen sin implementar.
- Siguiente paso: iniciar P0-01/P0-02 con SPEC-002 y el modelo ODDD cuando se solicite construir; las tareas de aplicación siguen pendientes.

## CAM-005 — Nombre oficial Navira

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario indica «el nombre de la app sera Navira».
- Flujo SDD reducido: cambio de identidad documental, sin nuevos requisitos o comportamiento; PRD vigente y ADR-006. Se conservan SPEC, criterios y tareas existentes.
- Resultado: **Navira** como nombre oficial e identificador técnico previsto `navira`, con paquete futuro `src/navira/`.
- Archivos: README, AGENTS, contexto, PRD/TRD, ODDD, módulos backend, plan, índice ADR y estado actual; nueva decisión ADR-006.
- Historia: el plan anterior y demás referencias históricas conservan su contenido. No se renombra el directorio `SPOOKYTHON` ni se migra código de app inexistente.
- Verificación: validadores documentales y SDD; resultado del cierre en [estado actual](estado-actual.md). No se requieren nuevas pruebas funcionales porque solo cambia documentación e identidad prevista.
- Siguiente paso: P0-01/P0-02 con el nombre Navira cuando se inicie la construcción.

## CAM-006 — Base local de backend y contrato inicial

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario autoriza comenzar la construcción por fases, con una rama `feat/...` y un commit por fase.
- Especificación/tareas: SPEC-002, P0-01 y P0-02; requisitos PRD-03, TRD-01, TRD-06 y TRD-09. Criterio cubierto parcialmente: contrato y autenticación iniciales; no se declara verificada la SPEC.
- Rama: `feat/navira-backend-base`.
- Motivo: crear un punto de arranque local para el backend y fijar el contrato de transporte antes de construir grafo y simulación.
- Archivos: `pyproject.toml`, `.env.example`, `src/navira/`, fixtures de contrato/mapa mínimo, README, documentos de API/backend, plan y estado.
- Resultado: aplicación FastAPI con `GET /salud`, `POST /paso`, esquema estricto, API key configurable y caso de uso temporal de espera determinista. La espera es válida por el contrato, pero no calcula rutas ni garantiza seguridad. No se exponen rutas auxiliares ni estado inexistente.
- Verificación: instalación editable de `pyproject.toml` correcta en entorno aislado `/tmp/navira-env`; `python3 scripts/check_docs.py` y `python3 scripts/check_sdd.py` correctos; parseo AST de módulos Python, lectura de fixtures JSON/`pyproject.toml` y `git diff --check` correctos. No se ejecutó la API ni pruebas HTTP; el arranque aún queda pendiente.
- Límites: no existe mapa de Manta, simulador, persistencia, Dijkstra, latencia medida ni despliegue. P0-01/P0-02 permanecen en curso hasta verificar instalación/arranque y pruebas de contrato.
- Siguiente paso: arrancar y verificar el endpoint HTTP; después construir grafo/mundo en P1.

## CAM-007 — Modelo y validación de grafo

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario pide continuar la construcción por fases, con rama y commit propios para cada fase.
- Especificación/tarea: SPEC-001, P1-01; requisitos PRD-01, TRD-09 y TRD-12; CA-001-01 parcial y T-07 parcial.
- Rama: `feat/navira-map-graph`.
- Motivo: validar el formato de la red vial antes de cargar datos geográficos de la ciudad.
- Archivos: `src/navira/domain/mapa.py`, fixture sintético, `tests/test_mapa.py`, documentos de datos, pruebas, pendientes, módulos, SPEC-001, plan, README y estado.
- Resultado: nodos WGS84, calles dirigidas con segmento físico estable, refugios, índice de adyacencia, parser JSON y validaciones de IDs/referencias/unidades/categorías. Los cierres pueden apuntar a un sentido o al segmento completo; calles paralelas permanecen independientes.
- Verificación: `python -m unittest discover -s tests -p 'test_mapa.py' -v`: diez pruebas correctas. El fixture sintético de cuatro nodos supera el validador con umbral cuatro. `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py` y `git diff --check` correctos.
- Límites: no hay extracción OpenStreetMap, polígono de Manta, mapa real de unas 300 intersecciones ni refugios reales. P1-01 permanece en curso; P1-02 a P1-05 no implementadas. P0-01/P0-02 aún requieren ejecución HTTP.
- Siguiente paso: preparar el dataset real de Manta y cerrar P1-01; luego continuar con entidades e intenciones.

## CAM-008 — Entidades e intenciones compartidas

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario para implementar Navira fase por fase.
- Especificación/tarea: SPEC-001, P1-02; requisitos PRD-02, PRD-06 y TRD-09; CA-001-06 parcial y T-17 parcial.
- Rama: `feat/navira-world-model`.
- Motivo: fijar el modelo del mundo y el contrato temporal antes de implementar las reglas de movimiento.
- Archivos: `src/navira/domain/modelo.py`, `tests/test_modelo.py`, documentos ODDD, modos, datos, módulos backend, pruebas, SPEC-001, plan y estado.
- Resultado: modelos inmutables para partida, sobreviviente, zombie e intención; el modo queda fijo y cada intención se valida contra run, turno, fase y personaje. Ambos modos usan la misma forma de intención.
- Verificación: siete regresiones de dominio correctas con `python -m unittest discover -s tests -p 'test_modelo.py' -v`. Se verifican estados y vínculo temporal, no la aplicación de movimientos.
- Límites: no hay transición de turnos, política zombie, resolución de mordidas, datos reales de Manta ni persistencia. P1-02 queda en curso; SPEC-001 no está verificada.
- Siguiente paso: implementar un único resolutor de intención/movimiento para NPC y humano en P1-03.

## CAM-009 — Resolución de turno y reglas zombie

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario para construir Navira por fases, con rama y commit individuales.
- Especificación/tarea: SPEC-001, P1-03; CA-001-02/03/04/06 parciales; T-01 a T-06, T-09 y T-17 parciales. Los criterios de visibilidad y snapshot no se consideran cubiertos.
- Rama: `feat/navira-zombie-resolution`.
- Motivo: implementar un único resolutor en memoria que aplique fases zombie, valide intenciones y determine mordidas/llegadas igual en simulador y juego humano.
- Archivos: `src/navira/domain/modelo.py`, `src/navira/simulation/resolver.py`, `tests/test_resolver.py` y documentos propietarios de reglas, algoritmo, flujo, backend, plan, pendientes y pruebas.
- Resultado: caminantes alternan movimiento, corredores persiguen hasta dos tramos, hordas estáticas bloquean el nodo y sus vecinos, dormidos despiertan por radio topológico configurable, sobrevivientes resuelven intenciones a la vez y cruces opuestos comparan cada tramo por segmento. Mordida precede evacuación. Semilla RNG inyectada permite repetición.
- Supuestos: comportamiento del dormido, objetivo/desempate del corredor, inmovilidad de horda y orden mordida/llegada siguen provisionales, configurables o pendientes según P-02 a P-04/P-07. No se expone aún una proyección segura que oculte dormidos.
- Verificación: conjunto completo local: 36 pruebas correctas (8 de SDD, 10 de mapa, 7 de modelo y 11 de resolutor). Validadores documentales y `git diff --check` se ejecutan al cierre; cualquier resultado final se registra antes del commit.
- Límites: un único turno en memoria; no reloj continuo, avance a siguiente turno, eventos persistidos, snapshots/versionado, carga de escenario ni mapa real de Manta. P1-03 queda parcial y SPEC-001 no está verificada.
- Siguiente paso: P1-04 en rama separada, coordinando ciclo de turnos y publicación atómica/versionada del estado.

## CAM-010 — Coordinación de fases, eventos y snapshots locales

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para construir por fases en ramas/commits separados.
- Especificación/tarea: SPEC-001, P1-04; CA-001-03/05 y T-07/T-10/T-18 parciales. Persistencia, recuperación y publicación no están cubiertas.
- Rama: `feat/navira-turn-snapshots`.
- Motivo: separar movimiento zombie de órdenes humanas y dar identidad/versiones explícitas al estado de decisión y resultado.
- Archivos: `src/navira/simulation/coordinador.py`, `src/navira/simulation/reloj.py`, `src/navira/simulation/resolver.py`, `tests/test_coordinador.py` y documentos propietarios de ODDD, datos, flujo, módulos, pruebas, plan, SPEC-001 y estado.
- Resultado: aplicación versionada de cierres en turno objetivo; snapshots completos de decisiones y resolución; preparación separada para juego humano; ruta de avance automático; estado aleatorio privado preservado en los snapshots; apertura del siguiente turno solo desde resultado resuelto; cálculo de deadline absoluto con reloj monotónico.
- Verificación: 43 pruebas de todas las suites correctas, incluidas siete regresiones del coordinador/reloj. Los validadores `check_docs.py`, `check_sdd.py` y `git diff --check` pasan al cierre.
- Límites: el coordinador puro rechaza una versión local obsoleta, pero no evita carreras entre procesos. No existe DynamoDB/adaptador durable, compare-and-swap real, reloj continuo, WebSocket, interrupción/recuperación ni ocultamiento de dormidos. P1-04 permanece parcial y SPEC-001 no se verifica.
- Siguiente paso: persistir snapshots mediante puerto/adaptador con condición de versión y probar fallos/recuperación; luego integrar reloj de ejecución y publicación.

## CAM-011 — Puerto de snapshots y CAS local

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario para implementar Navira por fases y dejar cada cambio en su rama/commit.
- Especificación/tarea: SPEC-001, P1-04; CA-001-05 y T-18 parciales; persistencia durable y recuperación no cubiertas.
- Rama: `feat/navira-snapshot-cas`.
- Motivo: definir el límite de aplicación para guardar estado completo por versión y evitar que dos transiciones locales desde el mismo snapshot se confirmen ambas.
- Archivos: `src/navira/application/snapshots.py`, `src/navira/adapters/snapshots_memoria.py`, `tests/test_snapshots_persistidos.py` y módulos/datos/arquitectura/pruebas/SPEC/estado.
- Resultado: puerto `RepositorioSnapshots`, casos de uso de preparación, resolución y apertura del turno con CAS; el adaptador local inserta una partida una vez y reemplaza snapshot solo cuando versión esperada coincide, bajo un lock por proceso.
- Verificación: tres regresiones nuevas para ciclo completo, duplicado e intento concurrente desde la misma versión. Suites totales, validadores documentales y SDD se registran al cierre.
- Límites: lock local no coordina varios procesos/hosts, no persiste ante reinicio y no sustituye DynamoDB. P1-04 sigue parcial; SPEC-001 no está verificada.
- Siguiente paso: implementar el adaptador durable con escritura condicional y recuperación, sin llevar reglas o SDK al dominio.

## CAM-012 — Verificación HTTP del contrato base

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario; validar la base de backend antes de conectar planificación y estado.
- Especificación/tareas: SPEC-002, P0-01 verificada y P0-02 parcialmente verificada; CA-002-01 parcial y T-08 parcial. No cubre decisión de ruta.
- Rama: `feat/navira-api-contract-tests`.
- Motivo: comprobar instalación, arranque HTTP, autenticación y contrato de éxito/error de la API existente.
- Archivos: `pyproject.toml`, `tests/test_api_http.py`, README, SPEC-002, pruebas y estado.
- Resultado: dependencia opcional `.[test]` con `httpx2` para evitar la API de prueba obsoleta; regresiones para `/salud`, clave sin configurar/inválida/válida, respuesta exacta, campos extra y turno negativo.
- Verificación: instalación editable con extra de pruebas correcta; cinco pruebas ASGI correctas; smoke con Uvicorn/curl: `/salud` 200, `/paso` autenticado 200 con `siguienteNodo` igual al nodo actual, y sin credencial 401. No se mide p95.
- Límites: `/paso` aún devuelve espera determinista, no consulta mapa ni planificador. P0-02 queda parcial; SPEC-002 no está verificada. Sin despliegue.
- Siguiente paso: conectar el caso de uso al mapa/estado y definir respuestas 404/409 con T-08/T-10, manteniendo el cuerpo obligatorio del reto.

## CAM-013 — Núcleo Dijkstra dirigido

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para avanzar Navira por fases y ramas separadas.
- Especificación/tarea: SPEC-002, P2-01 parcial; CA-002-02 parcial; T-07/T-08 parciales. No valida mapa real ni endpoint.
- Rama: `feat/navira-dijkstra`.
- Motivo: construir una política base de rutas sobre el grafo independiente de HTTP y estado de partida.
- Archivos: `src/navira/routing/`, `tests/test_dijkstra.py`, documentos de algoritmos, módulo backend, pendientes, pruebas, plan, SPEC-002, README y estado.
- Resultado: Dijkstra dirigido con costo de distancia y factor positivo configurable por tipo, cierres de aristas/segmentos y filtro de nodos de peligro visibles; selección de refugio objetivo o de menor costo; desempate estable por ID de calle/refugio.
- Supuesto: costo base son metros ponderados; factores neutros 1.0. Velocidad, eficiencia oficial y penalizaciones de juego no se mezclan hasta aclarar P-01.
- Verificación: siete pruebas de grafo sintético cubren ruta más barata, factor por tipo, cierres, peligro visible, no-ruta, desempates y validación. El resultado final del conjunto y validadores queda registrado al cierre.
- Límites: P2-01 continúa parcial; no carga Manta real ni integra el planificador en `/paso`. No estima zombies futuros, mordidas o seguridad garantizada. SPEC-002 no está verificada.
- Siguiente paso: integrar rutas con snapshot vigente y definir proyección de riesgos permitidos, sin exponer dormidos.

## CAM-014 — Integración de rutas con `/paso`

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para seguir construyendo Navira por fases.
- Especificación/tarea: SPEC-002, P2-02 parcial; CA-002-01/02 parciales; T-03/T-04/T-05/T-07/T-08 parciales. No hay ronda operacional.
- Rama: `feat/navira-step-planner`.
- Motivo: hacer que el caso de uso consulte estado vigente y utilice Dijkstra sin introducir runId o estado privado en el contrato externo.
- Archivos: `src/navira/application/decidir_paso.py`, `src/navira/api/routes.py`, `src/navira/main.py`, catálogo de mapas, consulta de partida activa en adaptador de memoria, pruebas de decisión/API e índices propietarios.
- Resultado: valida partida activa, mapa, turno, fase, personaje y posición; selecciona ruta/refugio evitando nodos ocupados por zombies activos, vecindad de horda, cierres y aristas de cruce opuesto conocidas. Ignora dormidos en la recomendación. HTTP conserva el esquema y mapea entidad ausente/estado incompatible/no disponible a 404/409/503. Se puede ensamblar con `crear_app(servicio_decision)`.
- Verificación: suite completa `python -m unittest discover -s tests -p 'test_*.py' -v` (67 pruebas OK); `python3 scripts/check_docs.py` y `python3 scripts/check_sdd.py` OK; `git diff --check` OK. Los validadores comprueban estructura documental, no comportamiento.
- Límites: el app predeterminado no carga mapa/partida y mantiene espera determinista. Almacenamiento es memoria, no hay inicio de partida/configuración de escenario ni idempotencia durable. Dijkstra trata riesgos visibles actuales, no futuro y no garantiza supervivencia. P2-02 parcial; SPEC-002 no verificada.
- Siguiente paso: añadir inicializador de partida de demostración con mapa de desarrollo explícito y preparar la integración persistente, sin presentar ese mapa sintético como Manta.

## CAM-015 — Bootstrap local explícito de partida demo

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de la construcción por fases; siguiente acción concreta de CAM-014/estado actual.
- Especificación/tareas: SPEC-001, P1-04 parcial; P2-02 continúa en curso. No se declara ronda completa ni SPEC verificada.
- Rama: `feat/navira-demo-bootstrap`.
- Motivo: arrancar el planificador con un mundo explícito y verificable sin presentar datos sintéticos como mapa de Manta.
- Archivos: `src/navira/demo.py`, `src/navira/main.py`, `data/maps/demo-sintetico.json`, `tests/test_demo.py`, README y documentos propietarios de datos, backend, pruebas, plan, SPEC y estado.
- Resultado: `NAVIRA_DEMO=1` carga mapa sintético, crea un snapshot inicial en memoria, avanza al primer estado de decisiones con el coordinador y ensambla `DecidirPaso`. La ruta `S-DEMO-001` desde `D-001` propone `D-002`. Sin opt-in, el proceso mantiene espera determinista.
- Límites: un sobreviviente, sin zombies, un refugio, repositorios volátiles, semilla controlable y sin reloj continuo. No es mapa de evaluación ni una ronda de simulación completa; reiniciar el proceso reinicia el estado.
- Verificación: suite completa `PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v` (70 pruebas OK); smoke con proceso Uvicorn: `GET /salud` 200 y `POST /paso` autenticado 200 con `{"siguienteNodo":"D-002"}`. Se ejecutaron `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py` y `git diff --check` al cierre. El smoke es local y no mide carga.
- Siguiente paso: avanzar escenarios reproducibles con ciclo de turno; mantener pendiente persistencia durable, mapa real y reglas/visibilidad.

## CAM-016 — Orquestación de ronda automática versionada

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada por el usuario de la implementación por fases y siguiente trabajo del plan tras el bootstrap demo CAM-015.
- Especificación/tareas: SPEC-001, P1-04 parcial; criterios de fase/snapshot T-06 y T-18 parciales. No se declara SPEC verificada.
- Rama: `feat/navira-automatic-round`.
- Motivo: conectar coordinador, snapshots CAS y Dijkstra para resolver una ronda del modo simulador sin duplicar reglas.
- Archivos: `src/navira/application/simulacion_automatica.py`, `tests/test_simulacion_automatica.py`, documentos propietarios de flujo, datos, backend, pruebas, plan, SPEC y estado.
- Resultado: `EjecutarRondaAutomatica` confirma preparación, genera intenciones automáticas desde Dijkstra y confirma la resolución. Una llamada siguiente abre el turno siguiente; un reintento desde decisiones persistidas no vuelve a mover zombies. Rechaza modo juego y versiones obsoletas.
- Verificación: seis pruebas dedicadas; suite completa `PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v` (76 pruebas OK); `python3 scripts/check_docs.py`, `python3 scripts/check_sdd.py`, `compileall` y `git diff --check` correctos. Son verificaciones locales; no miden reloj ni durabilidad.
- Límites: CAS y escenario solo en memoria; no hay reloj continuo, llamada HTTP/CLI, publicación, mapa real ni evaluación oficial. Estado final del juego y métricas de ronda permanecen pendientes.
- Siguiente paso: proporcionar un ejecutor local documentado sobre el contexto demo y crear escenarios/semillas reproducibles con zombies.

## CAM-017 — Ejecutor local de rondas demo

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario para construir Navira por fases; siguiente acción registrada en CAM-016.
- Especificación/tareas: SPEC-001, P1-04 parcial; P1-05 continúa pendiente. No se completa la aceptación de la SPEC.
- Rama: `feat/navira-auto-demo-cli`.
- Motivo: hacer ejecutable y reproducible desde terminal el caso de uso de ronda automática, sin introducir reloj continuo ni persistencia nueva.
- Archivos: `src/navira/demo.py`, `src/navira/simulador_demo.py`, `tests/test_simulador_demo.py`, README y documentos propietarios del flujo, módulo, pruebas, plan, SPEC-001 y estado.
- Resultado: `python -m navira.simulador_demo --turnos N --semilla S [--mapa RUTA]` crea contexto efímero, completa rondas por CAS, emite JSON por línea y se detiene al no quedar sobrevivientes activos o alcanzar N turnos. El fixture predeterminado evacúa al único personaje en cuatro rondas.
- Verificación: cuatro regresiones de `test_simulador_demo.py`; suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (80 pruebas OK); `python3 scripts/check_docs.py` (53 Markdown en `docs/`, 55 archivos comprobados), `python3 scripts/check_sdd.py`, ocho regresiones de `test_check_sdd.py`, `compileall` y `git diff --check` correctos. Smoke `PYTHONPATH=src python -m navira.simulador_demo --turnos 10 --semilla 41` produjo cuatro líneas JSON, movimientos D-001→D-002→D-003→D-004→D-005 y evacuación en el turno 3. Validación local, no mide reloj ni persistencia.
- Límites: fixture sintético sin zombies; la semilla se incluye en el reporte y alimenta el generador inicial, pero no cambia el recorrido actual. No duerme entre turnos, mide tiempo, persiste al reiniciar, publica eventos ni evalúa el escenario oficial.
- Siguiente paso: diseñar escenarios reproducibles con zombies para P1-05, después medir las tres rondas según SPEC-005.

## CAM-018 — Perfiles sintéticos de escenarios con zombies

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario; siguiente paso P1-05 documentado por CAM-017.
- Especificación/tareas: SPEC-001, CA-001-07 y P1-05 parcial; T-10. No se considera completo P1-05 ni verificada SPEC-001.
- Rama: `feat/navira-zombie-scenarios`.
- Motivo: ejercitar el mismo ejecutor con zombies y reproducir decisiones usando escenario y semilla como entradas explícitas.
- Archivos: `src/navira/demo.py`, `src/navira/simulador_demo.py`, `tests/test_simulador_demo.py`, README y documentos propietarios de SPEC-001, flujo, módulo, pruebas, plan, pendientes y estado.
- Resultado: perfiles sintéticos `libre`, `caminantes`, `mixto` y `horda`; la partida conserva su perfil, el CLI lo acepta con `--escenario`, y el JSONL reporta movimientos visibles. Zombies que siguen dormidos se omiten. Igual perfil y semilla reproducen reportes; la semilla puede variar el movimiento de caminantes.
- Verificación: seis pruebas de `test_simulador_demo.py`; suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (82 pruebas OK); `python3 scripts/check_docs.py` (53 Markdown en `docs/`, 55 archivos comprobados), `python3 scripts/check_sdd.py`, ocho regresiones de `test_check_sdd.py`, `compileall`, `git diff --check` y smoke del perfil `horda` correctos. Las pruebas muestran reproducción exacta del mismo escenario/semilla, variación posible entre semillas y ausencia de dormidos en JSONL. No se midió duración del turno ni carga oficial.
- Límites: mapa lineal sintético, un sobreviviente, ubicaciones fijas de inicio y cuatro perfiles reducidos; no son las rondas oficiales (20/80/200 sobrevivientes) ni fijan la distribución de zombies del reto. P-09 continúa abierto para tamaño/balance oficial. Sin reloj de 2 segundos, persistencia durable ni medición oficial.
- Siguiente paso: completar poblaciones/condiciones de P1-05 cuando se confirme densidad zombie y contar con mapa de evaluación; después integrar tres rondas según SPEC-005.

## CAM-019 — Cohortes sintéticas para el ejecutor

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario; extensión incremental de P1-05 después de CAM-018.
- Especificación/tareas: SPEC-001, CA-001-08 y P1-05 parcial; T-10. T-11 no se ejecuta con este cambio.
- Rama: `feat/navira-evaluation-populations`.
- Motivo: permitir recorrer los tamaños 20/80/200 del reto con el mismo núcleo local mientras se prepara el dataset real.
- Archivos: `src/navira/demo.py`, `src/navira/simulador_demo.py`, `tests/test_simulador_demo.py`, README y documentos propietarios de datos, reglas, flujo, módulo, pruebas, plan, pendientes, SPEC-001 y estado.
- Resultado: `--sobrevivientes` acepta de 1 a 200; posiciones iniciales no refugio se distribuyen reproduciblemente por semilla. Población inicial se registra por turno. Si el fixture carece de nodos suficientes, pueden coincidir personajes.
- Verificación: ocho pruebas de `test_simulador_demo.py`; suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (84 pruebas OK), incluye poblaciones 20/80/200; `python3 scripts/check_docs.py` (53 Markdown en `docs/`, 55 archivos comprobados), `python3 scripts/check_sdd.py`, ocho regresiones de `test_check_sdd.py`, `compileall` y `git diff --check` correctos. Smoke del CLI con 200 sobrevivientes produjo JSONL de un turno (12.683 bytes). No es carga HTTP ni una medición de rendimiento.
- Límites: poblaciones sobre cinco nodos sintéticos no simulan 20/80/200 ubicaciones realistas, no producen concurrencia HTTP ni verifican T-11, dos segundos, p95, disponibilidad o supervivencia de evaluación. La distribución zombie oficial P-09 sigue pendiente.
- Siguiente paso: añadir mapa representativo de Manta y ejecutar la población a través del cliente HTTP bajo las ráfagas definidas en T-11; evitar afirmar resultados oficiales antes de esas mediciones.

## CAM-020 — Cliente concurrente para medir `/paso`

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario; siguiente paso concreto CAM-019: conectar cohortes sintéticas al cliente HTTP para T-11.
- Especificación/tareas: SPEC-002, CA-002-04 parcial; T-11 parcial. No se verifica la SPEC ni la prueba de fuego.
- Rama: `feat/navira-http-load-runner`.
- Motivo: medir desde un cliente la ruta HTTP real con las cohortes sintéticas, conservar el contrato y capturar latencias/errores sin incrustar credenciales.
- Archivos: `src/navira/main.py`, `src/navira/carga_http.py`, pruebas de carga/demo, README y documentos propietarios de API, backend, pruebas, SPEC-002 y evidencia local.
- Resultado: variables optativas del bootstrap demo fijan escenario/semilla/población del servidor; `python -m navira.carga_http` prepara solicitudes reproducibles y dispara hasta 200 llamadas concurrentes por ronda, verificando status, forma y destino esperado. El cliente requiere `NAVIRA_API_KEY` del entorno. Repite solicitudes sobre snapshot fijo; no avanza turnos.
- Verificación: dos pruebas del cliente y cinco del ensamblaje demo pasan; suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (88 pruebas OK); `python3 scripts/check_docs.py` (54 Markdown en `docs/`, 56 archivos comprobados), `python3 scripts/check_sdd.py`, ocho regresiones de `test_check_sdd.py`, `compileall` y `git diff --check` correctos. Smoke mediante CLI contra Uvicorn local: 20/80/200 solicitudes concurrentes recibieron 200, sin fallos; p95 7.872/11.972/26.066 ms. Detalle y límites en [reporte](../calidad/resultados/carga-local-cam020.md). No es T-11 completo ni prueba externa.
- Límites: una pasada local por cohorte, un proceso Uvicorn, mismo host, snapshot fijo, sin intervalo/150 rondas ni entorno evaluador. No es T-11 completado, disponibilidad ni promesa de rendimiento.
- Siguiente paso: finalizar verificación/commit; después hacer ejecución sostenida en el entorno objetivo con mundo/turno activos y recolectar una muestra completa.

## CAM-021 — Fixture geográfico de Manta con evidencia por amenaza

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario; solicita considerar zonas seguras de tsunami y terremoto en la ciudad real de Manta, Ecuador.
- Especificación/tareas: SPEC-001, CA-001-01/P1-01 parcial; P-13 parcialmente atendido, P-14 abierto. No se verifica SPEC-001.
- Rama: `feat/navira-manta-hazard-map`.
- Motivo: reemplazar el mapa pendiente por un fixture reproducible con red pública de Manta y destinos cuya evidencia de tsunami sea rastreable, sin atribuir seguridad sísmica no validada.
- Archivos: `scripts/exportar_mapa_manta.py`, `data/maps/manta-hackathon-v1.json`, `data/maps/manta-hackathon-v1.fuentes.json`, `tests/test_mapa_manta.py`, ADR-007 y documentos propietarios de contexto, producto, datos, reglas, mapa, plan, pendientes, SPEC-001 y estado.
- Resultado: el exportador descargó OSM en un recorte urbano declarado, simplificó la geometría y produjo 300 nodos, 599 sentidos de calle y cuatro refugios distintos. Los marcadores de Cristo Rey, Colinas de Rocafuerte, La Dolorosa y Plaza del Sol aparecen como “Zona Segura” en los mapas de evacuación por tsunami del GAD Manta; los ajustes a la red son 32,9–43,4 m. El grafo dirigido incluye un camino de cada nodo a algún refugio. Metadatos registran extracción, área, atribución/licencia ODbL y límites.
- Verificación: exportador ejecutado en vivo el 2026-10-26; suite completa `PYTHONPATH=src /tmp/navira-env/bin/python -m unittest discover -s tests -p 'test_*.py' -v` (90 pruebas OK), incluidas dos pruebas enfocadas del mapa. `python3 scripts/check_docs.py` (56 Markdown/58 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructurales), ocho regresiones documentales, `compileall` y `git diff --check` correctos. Los validadores SDD comprueban estructura/trazabilidad, no comportamiento ni verdad externa.
- Límites: fixture de simulación, no para navegación/evacuación real; cobertura completa de barrios y acceso peatonal no verificados; los límites de velocidad faltantes son valores de juego; zonas de tsunami no validan seguridad de terremoto. P-14 requiere microzonificación y validación de suelo/estructura. La SPEC y P1-01 permanecen parciales.
- Siguiente paso: cerrar un commit individual en esta rama. Luego revisar visualmente cobertura y, por separado, buscar datos oficiales de microzonificación sísmica para Manta.

## CAM-022 — Requisito de mundo estocástico y reproducción

- Fecha: 2026-10-26, Ecuador continental.
- Origen: aclaración del usuario: el simulador debe ser aleatorio y pequeños cambios pueden alterar rutas, hordas y la evolución del mundo.
- Especificación/tareas: PRD-02/07, TRD-11, SPEC-001 CA-001-07/09, P1-05. T-24 se define para implementación futura; no está ejecutada.
- Rama: `feat/navira-stochastic-simulation`.
- Motivo: hacer explícita la variación estocástica y su efecto en cascada, conservando la capacidad de reproducir una partida concreta para depurar y comparar.
- Archivos: ADR-008; contexto, PRD, TRD, ODDD, reglas, algoritmos, datos, pendientes P-15, plan, SPEC-001, trazabilidad, pruebas, estado e índices.
- Resultado: el objetivo es una semilla nueva por defecto, muestrear estados/decisiones permitidos por reglas y guardar contexto/RNG privado para replay dentro de la misma versión. El planificador permanece estable para una solicitud sobre el mismo snapshot. Diferencias de entrada pueden divergir, sin prometer que todo cambio mínimo necesariamente cambie el resultado final.
- Verificación: revisión de documentos propietarios y código actual (`demo.py`, `resolver.py`, `coordinador.py`); `python3 scripts/check_docs.py` (57 Markdown/59 archivos), `python3 scripts/check_sdd.py` (seis SPEC estructuralmente válidas), ocho pruebas de `test_check_sdd.py` y `git diff --check` correctos. No se ejecutaron pruebas de producto porque esta unidad solo especifica/documenta el requisito; T-24 queda pendiente de implementar.
- Límites: el código actual solo aleatoriza parte de la ubicación de sobrevivientes y movimiento de caminantes; perfiles/ubicaciones zombie son prefijados, corredores siguen persecución y desempate por ID, horda no se mueve y la semilla por defecto es fija. Densidad oficial P-09 y movimiento de horda P-07 siguen abiertos. Este CAM registra y traza el requisito, no implementa el generador estocástico.
- Siguiente paso: implementar P1-05 en una unidad de código: semilla de entropy por defecto con semilla explícita para replay, variación inicial parametrizada y pruebas de misma entrada/reproducción y divergencia controlada T-24. Mantener fuera de ese cambio cualquier distribución oficial sin fuente confirmada.

## CAM-023 — Semilla nueva y estado inicial estocástico de demo

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación autorizada del usuario y aclaración de que cambios pequeños pueden alterar rutas, hordas y evolución; implementación de P1-05 bajo ADR-008.
- Especificación/tareas: SPEC-001, P1-05; CA-001-07/08/09 y T-24 parciales.
- Rama: `feat/navira-stochastic-simulation`; commit individual `feat: randomize Navira demo simulations`.
- Motivo: dejar de repetir un mundo fijo cuando inicia una partida nueva y conservar entrada suficiente para reproducir ejecuciones locales.
- Archivos: `src/navira/demo.py`, `src/navira/simulador_demo.py`, `src/navira/main.py`, pruebas demo/CLI, `../README.md` y documentos propietarios de contrato, algoritmos, datos, flujo, pruebas, plan, SPEC e índice, trazabilidad, estado y este historial.
- Resultado: semilla de 64 bits generada desde entropía si no se indica; los inicios de sobrevivientes/zombies y la fase de caminantes se muestrean desde RNG privado; el CLI informa la semilla efectiva y permite replay al fijarla. Cada demo recibe runId distinto. Se conserva composición sintética fija; no se modifica persecución de corredor ni regla de horda.
- Verificación: suite completa con `/tmp/navira-env` (92 pruebas OK); `python3 scripts/check_docs.py` (57 Markdown/59 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho pruebas `test_check_sdd.py`, `compileall` y `git diff --check` correctos. T-24 cubre reproducción local y variación, no replay durable ni ejecución oficial.
- Límites: P1-05 sigue parcial. Distribución/cantidad oficial (P-09), movimiento de horda (P-07), eventos estocásticos, persistencia durable y carga con el mundo avanzando siguen pendientes. La divergencia puede ocurrir, no se garantiza que cada mínima perturbación cambie todo resultado.
- Siguiente paso: acordar/configurar escenarios solo con fuentes de reglas confirmadas, resolver P-09 y P-07 antes de variar composición y horda.

## CAM-024 — Replay estocástico multi-turno y estabilidad del snapshot

- Fecha: 2026-10-26, Ecuador continental.
- Origen: continuación del usuario para trabajar la siguiente fase; refinamiento de T-24 tras implementar semilla nueva y muestreo inicial en CAM-023.
- Especificación/tareas: SPEC-001, P1-05; CA-001-07/09 y T-24 parciales.
- Rama: `feat/navira-stochastic-replay-validation`; commit individual `test: verify stochastic replay across turns`.
- Motivo: verificar replay de una trayectoria y posible divergencia de rutas, además de asegurar que la aleatoriedad del mundo no vuelve aleatoria una decisión repetida sobre el mismo snapshot.
- Archivos: `tests/test_simulador_demo.py`, `tests/test_demo.py`, documentos propietarios de pruebas, SPEC-001, plan, trazabilidad, estado e historial.
- Resultado: la misma configuración/semilla reproduce cinco turnos con 20 sobrevivientes; otra semilla cambia la secuencia de rutas en un caso de prueba controlado. Repetir `/paso` sobre el mismo snapshot conserva respuesta y versión.
- Verificación: suite completa con `/tmp/navira-env` (94 pruebas OK); `python3 scripts/check_docs.py` (57 Markdown/59 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho regresiones SDD, `compileall` y `git diff --check` correctos. La repetición, divergencia controlada y snapshot se verifican por pruebas locales.
- Límites: no verifica persistencia/recovery durable, múltiples versiones del algoritmo, eventos oficiales, mapa Manta ni que toda semilla distinta produzca divergencia. No cierra P1-05.
- Siguiente paso: ejecutar cohortes sintéticas reproducibles de 20/80/200 sobre el fixture Manta y documentar un reporte exploratorio; después medir integración de `/paso` con avance de mundo.

## CAM-025 — Cohortes sintéticas sobre el fixture Manta

- Fecha: 2026-10-26, Ecuador continental.
- Origen: siguiente subpaso autorizado por el usuario para continuar la construcción por fases y probar el generador estocástico sobre la ciudad real modelada en el fixture disponible.
- Especificación/tareas: SPEC-001, P1-01/P1-05 parciales; CA-001-01/08/09 y T-07/T-24 parciales. No cierra P2-03 ni T-11.
- Rama: `feat/navira-manta-simulation-cohorts`; commit individual `test: exercise stochastic cohorts on Manta map`.
- Motivo: comprobar que el mapa versionado de 300 nodos funciona con el muestreo de inicio y el resolutor de rondas, antes de llevar el motor a medición HTTP.
- Archivos: `tests/test_simulacion_mapa_manta.py`, `docs/calidad/resultados/simulacion-manta-cam025.md`, README y documentos propietarios de mapa, flujo, pruebas, plan, SPEC, índice e historial.
- Resultado: con perfil `mixto`, semilla `20261026` y hasta tres turnos, cohortes sintéticas de 20/80/200 produjeron 2/8/28 evacuados, cero mordidos y 18/72/172 activos al final. Los movimientos comprobados son vecinos dirigidos o espera. La semilla/mapa/versión están en el reporte.
- Verificación: suite completa con `/tmp/navira-env` (95 pruebas OK); `python3 scripts/check_docs.py` (58 Markdown/60 archivos), `python3 scripts/check_sdd.py` (seis SPEC), ocho regresiones SDD, `compileall` y `git diff --check` correctos. El reporte no registra mediciones de latencia/carga.
- Límites: ensayo local único sobre perfiles reducidos; no son ejecuciones oficiales ni muestras independientes, no valida seguridad sísmica/cobertura cartográfica ni garantiza rutas reales. P-07, P-09, P-13 y P-14 continúan abiertos.
- Siguiente paso: ensayar `/paso` con avance del mundo por turnos en local y medición repetida, manteniendo separadas latencia HTTP y métricas de supervivencia.

## Próximas entradas

## CAM-058 — Priorizar la reducción de mordidas en las rutas

- Fecha: 2026-10-26, Ecuador continental.
- Origen: aclaración del usuario: la aplicación debe buscar durante la simulación la mejor ruta de evacuación y la prioridad es tener la menor cantidad de personas mordidas.
- Especificación/tareas: PRD-03/09/10, TRD-14, SPEC-002 CA-002-06, P3-03/T-30. No cierra T-22 integral, T-11 ni SPEC-002.
- Rama: `master`; commit individual creado al cerrar validación.
- Motivo: Dijkstra solo evita peligros actuales; el predictor/buscador temporal ya disponible no participaba en las decisiones reales. La evaluación anterior daba visibilidad a evacuados, pero no codificaba explícitamente la prioridad lexicográfica del usuario.
- Archivos: `src/navira/application/decidir_paso.py`, `src/navira/evaluacion_rutas.py`, `tests/test_decidir_paso.py`, `tests/test_evaluacion_rutas.py`; PRD, TRD, SPEC-002, trazabilidad, algoritmos, flujo de simulador, backend, plan, pruebas, ADR-012/018, índices, estado y resultado.
- Resultado: `/paso`, simulador automático y ruta prevista del panel usan búsqueda temporal por exposición observable, horizonte de hasta 12 turnos y presupuesto interno de 25 ms por búsqueda; Dijkstra responde cuando no hay trayecto temporal completo o se agota presupuesto. El pronóstico se calcula una vez por snapshot y se comparte entre recomendaciones de ese turno. El contrato HTTP se mantiene. El comparador ordena resultados reales por menos mordidos primero y más evacuados solo como desempate. Exposición pronosticada no equivale a mordida real ni a probabilidad calibrada.
- Verificación: suite completa (165 pruebas OK); pruebas dirigidas de decisión/API/ronda/evaluador; `python3 scripts/check_docs.py` (84 Markdown/86 archivos), `python3 scripts/check_sdd.py` (ocho SPEC), ocho regresiones `test_check_sdd.py`, compilación Python, `git diff --check` y build frontend correctos (advertencia conocida de bundle MapLibre). Ensayo emparejado de 27 pares sintéticos (3 semillas, 3 perfiles, poblaciones 20/80/200, 6 turnos, horizonte 12): −32 mordidos y +131 evacuados agregados; mordidos mejor/igual/peor en 13/8/6 pares; peor p95 local por recomendación temporal 25,194 ms. Smoke con Uvicorn/Vite: control inició una partida Manta y el panel publicó 64 zombies y 20 rutas previstas; al turno 2 el mundo tenía 7 mordidos, 2 evacuados y 11 activos. Ver método y límites en [reporte CAM-058](../calidad/resultados/politica-riesgo-cam058.md).
- Límites: solo tres semillas y reglas provisionales de movimiento; un mayor número agregado de supervivientes no prueba mejora por partida. En una comparación adicional de 12 turnos con semilla `582026`, Dijkstra dio 8 mordidos/5 evacuados y temporal 9 mordidos/8 evacuados; la corrida viva de 20 personas llegó al turno 33 con 19 mordidos y 0 evacuados. El predictor no reduce mordidas consistentemente por ejecución. Sin HTTP/concurrencia, no confirma presupuesto p95, T-11 ni ronda de cinco minutos. No es un sistema real de seguridad.
- Siguiente paso: medir el endpoint HTTP y el ciclo de dos segundos con la política nueva bajo cohortes, y comparar mordidas reales durante rondas más largas con nuevas semillas. El smoke local está activo, pero su corrida única no demuestra mejora frente a Dijkstra.
- Commit: individual en `master`; no implica publicación remota.

## CAM-057 — Intensidad sintética distribuida y cierres viales

- Fecha: 2026-10-26, Ecuador continental.
- Origen: el usuario pidió recapitulación de los roles y amenazas; señaló que solo se veían uno o dos focos y que la ciudad debía estar ampliamente amenazada para comparar evacuaciones.
- Especificación/tareas: PRD-02, SPEC-001 CA-001-10/11, P1-05; T-28/T-29 escritos, pendientes de ejecución. No se verifica SPEC-001.
- Rama: `master`; commit individual `350871d` (`feat: expand synthetic city threat scenarios`). Corrección de registro: el hash anterior `303e4fb` era incorrecto.
- Motivo: reemplazar la cantidad fija de zombies de demo por un perfil ajustable y espacialmente distribuido, y hacer que cierres viales afecten las rutas durante la partida.
- Archivos: `src/navira/demo.py`, control local/API, `ConsultarPanel`, esquemas HTTP, `frontend/src/app/App.tsx`, contratos de panel, ADR-017, pruebas demo/panel/control, y documentos propietarios/índices.
- Resultado implementado: intensidad sintética 6/14/25 % sobre nodos elegibles; perfiles `mixto` y `horda` distribuyen caminantes, corredores, hordas y dormidos; muestreo estratificado por sectores y semilla reproducible. El control local programa cierres de segmentos con `EventoCierre` en turnos 2/5/8 según intensidad. El panel agrega metadatos de incidentes solo desde `eventos_aplicados`, sin revelar los cierres futuros. La UI ofrece intensidad/incidentes y el registro los muestra al aplicarse.
- Verificación: `cd frontend && npm run build` correcto con advertencia de tamaño de bundle MapLibre; 28 pruebas focalizadas y suite completa (162 pruebas) con `/tmp/navira-env`; `compileall`, `check_docs.py` (82 Markdown/84 archivos), `check_sdd.py` (ocho SPEC estructuralmente válidas), ocho regresiones `test_check_sdd.py` y `git diff --check` correctos. Smoke con Vite/Uvicorn locales confirmó 65 amenazas al inicio, 67 al turno 4 y cierres aplicados en turnos 2/5/8; en turno 9, 6 activos, 5 evacuados y 9 mordidos.
- Límites: dificultad sintética no oficial; el fixture sigue conteniendo 300 nodos/599 aristas, dormidos ocultos, hordas estáticas y eventos viales genéricos. La política de rutas permanece Dijkstra; no hay claim de ruta óptima/segura. Consultar [reporte de verificación](../calidad/resultados/generador-amenazas-cam057.md).
- Siguiente paso: ejecutar pruebas/validadores en un Python con dependencias, corregir fallos y luego cerrar commit individual. No publicar a remoto en esta unidad.

Usar [plantilla de cambio](../metodo/plantillas/cambio.md). Cada entrada significativa explica qué disparó el cambio, por qué, qué áreas toca, qué se comprobó y cómo continuar. Conservar entradas anteriores; corregir datos erróneos dejando constancia, no reescribiendo la historia silenciosamente.
