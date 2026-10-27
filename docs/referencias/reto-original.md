# Referencia — texto original del reto

Fuente: texto pegado por el usuario el 26 de octubre de 2026. Se conserva íntegro para consulta local; las aclaraciones posteriores se documentan en `../pendientes.md` y en decisiones, sin modificar esta fuente. No se ha verificado una publicación externa adicional.

---

Track A · Escape de Manta Zombie 🧟
La noche del 31 de octubre, Manta amanece infestada. Hay sobrevivientes atrapados en Tarqui, Los Esteros, Barbasquillo y Jocay, y los refugios están en puntos fijos de la ciudad. Los zombies no se quedan quietos: caminan, corren, se agrupan en hordas y algunos duermen escondidos hasta que alguien pasa cerca. Tu sistema es la única radio que les queda a los sobrevivientes: les dice, paso a paso, por dónde ir. LA PROBLEMÁTICA REAL Encontrar la mejor ruta es fácil cuando el mapa no cambia. El problema real es cuando el mapa cambia mientras te mueves: calles cerradas, tráfico, accidentes, zonas peligrosas. Es el núcleo de Uber, de las apps de delivery y de las rutas de evacuación ante desastres. UTILIDAD REAL Este motor es la base de una app de delivery, de un sistema de despacho de taxis o ambulancias, o de una ruta de evacuación ante tsunamis en la costa de Manabí: solo hay que cambiar "zombie" por "calle cerrada" o "zona inundada".

Publicado
Asignado 26 oct 2026, 12:01 a. m.
01
Objetivo
Construir en AWS un motor de rutas que recalcule en tiempo real según obstáculos móviles y que responda rápido aunque haya cientos de personas pidiendo ruta al mismo tiempo. El servicio:
1. Recibe el mapa de Manta como grafo (intersecciones y calles).
2. Escucha la posición de los zombies, que se actualiza cada turno.
3. Decide para cada sobreviviente cuál es su siguiente paso para llegar a un refugio sin ser mordido y lo antes posible.
4. Muestra todo en un mapa en vivo: zombies, sobrevivientes, rutas y refugios.

02
Requisitos
EL MUNDO DEL JUEGO
- Mapa: el equipo construye el grafo de Manta (por ejemplo con datos abiertos de OpenStreetMap): unas 300 intersecciones (id, lat, lng), calles con distancia_m y tipo (avenida, calle, callejon, puente; cada tipo con su velocidad) y 4 refugios.
- Turnos de 2 segundos: primero se mueven los zombies y después los sobrevivientes.
- Zombies: Caminante (1 calle cada 2 turnos, dirección aleatoria) · Corredor (2 calles por turno; persigue si hay un sobreviviente a 3 nodos o menos) · Horda (casi inmóvil, bloquea su nodo y todos los vecinos) · Dormido (invisible hasta que un sobreviviente está a 2 nodos o menos; ahí despierta como caminante).
- Eventos de ciudad: un puente colapsa o una avenida se bloquea; la arista desaparece del mapa en vivo.
- Mordida: si al final de un turno comparte nodo con un zombie, o si se cruzan por la misma calle en direcciones opuestas. El mordido queda fuera.

CONTRATO TÉCNICO
- El equipo construye su Simulador del Apocalipsis: mueve a los zombies según sus reglas y publica el estado del mundo en cada turno por GET /estado o WebSocket (turno, zombies con id/tipo/nodo y aristasBloqueadas).
- El equipo DEBE exponer POST /paso, que su simulador consulta por cada sobreviviente en cada turno. Pregunta: {"sobrevivienteId": "S-0089", "nodoActual": "N-0117", "turno": 142}. Respuesta: {"siguienteNodo": "N-0118"}.
- DEBE responder en menos de 500 ms; si no, el sobreviviente se queda quieto ese turno.
- siguienteNodo DEBE ser vecino por una calle no bloqueada, o el mismo nodo. Un movimiento inválido equivale a quedarse quieto.
- Cada sobreviviente va al refugio que el equipo considere mejor.
- Autenticación por API key en la cabecera x-api-key.
- Mapa en vivo: interfaz web actualizada en cada turno con zombies (ícono por tipo), sobrevivientes, ruta planificada y refugios.

NIVEL BASE 🟢
- POST /paso con rutas válidas que eviten zombies visibles.
- Algoritmo de rutas (Dijkstra, A* u otro) que considere distancia y tipo de calle.
- Mapa en vivo funcionando y todo desplegado en AWS.

NIVEL PRO 🔴 (puntos extra)
- Predicción: anticipar hacia dónde se mueven los corredores.
- Capacidad de refugios: repartir sobrevivientes para que ninguno llegue a un refugio lleno.
- Flota de rescate: 5 camionetas el doble de rápidas que llevan hasta 4 personas; decidir a quién recoger y en qué orden.

03
Reglas
ENTORNO
- Cada equipo DEBE trabajar en una cuenta AWS propia (o la sandbox que entregue la organización) en la región us-east-1 (por confirmar).
- La cuenta DEBE tener un AWS Budget con alerta desde el primer día (captura en el README).
- Se permite usar asistentes de IA para programar, pero el equipo DEBE poder explicar cualquier parte de su código.
- Lenguajes y frameworks libres.

CÓMO LEER EL RETO
- DEBE: obligatorio. Si no se cumple, ese criterio vale 0.
- DEBERÍA: esperado. No cumplirlo resta, pero no anula.
- PUEDE: opcional. Suma puntos si está bien hecho.

RÚBRICA BASE (sobre 10)
- Prueba de fuego (40 %): resultado de la prueba del track, en escala 0–10.
- Calidad técnica (25 %): arquitectura adecuada, seguridad básica (sin llaves en el código, mínimo privilegio), código legible.
- Producto (15 %): que una persona real pueda usarlo sin explicación.
- Costos (10 %): declaración de costos coherente con lo que muestra la cuenta.
- Presentación (10 %): claridad, respeto del tiempo y respuestas a preguntas.
En caso de empate gana el equipo con mejor prueba de fuego; si persiste, el de menor costo declarado.

PRUEBA DE FUEGO (Track A)
El equipo ejecuta en vivo, con su simulador, tres rondas seguidas de 5 minutos:
- Ronda 1 · Anochecer: 20 sobrevivientes, solo caminantes.
- Ronda 2 · Medianoche: 80 sobrevivientes, caminantes, corredores y hordas; un puente colapsa.
- Ronda 3 · Apocalipsis: 200 a la vez, todos los tipos incluidos dormidos; dos calles se bloquean en vivo.

Puntuación (0–10): Supervivencia 50 % (ponderada R1 ×1, R2 ×2, R3 ×3) · Eficiencia 20 % (turnos vs. ruta más corta sin zombies) · Latencia 15 % (p95 de POST /paso: ≤150 ms 10 · ≤300 ms 7 · ≤500 ms 4 · más 0) · Disponibilidad 15 % (errores o fuera de tiempo: <0,5 % 10 · <2 % 6 · <5 % 3 · más 0).

LO QUE EL JURADO VA A BUSCAR
- Calcular la ruta una sola vez y no recalcularla cuando los zombies se mueven.
- Evitar el nodo de la horda pero no sus vecinos.
- Guardar el estado en memoria de una Lambda (cada instancia tiene su copia).
- Arranques en frío que pasan de 500 ms en la ronda 3.
- Un mapa en vivo bonito pero congelado.

04
Entregables
Todo se entrega en la plataforma (Mi equipo → Entrega) hasta el miércoles 28 de octubre a las 10:00 (hora de Ecuador). Lo que llegue después no se evalúa.

LISTA DE ENTREGABLES
- Repositorio público (GitHub, GitLab o Bitbucket) con el código completo y un historial de commits real, no un solo commit final.
- README en la raíz con: qué hace el proyecto, cómo desplegarlo, cómo probarlo, decisiones de diseño, limitaciones conocidas y la captura del AWS Budget con alerta.
- Diagrama de arquitectura dentro del repositorio y enlazado desde el README: servicios de AWS usados, flujo de datos y qué partes son públicas. Herramienta libre: draw.io (diagrams.net), Excalidraw, Lucidchart, Cloudcraft, AWS Infrastructure Composer o Mermaid. Suban la imagen (PNG o SVG) y, si existe, el archivo fuente (por ejemplo .drawio).
- Declaración de costos en el README o en docs/costos.md: cuánto costaría operar el sistema al mes, con el cálculo visible, y cuánto se gastó realmente durante el evento.
- Aplicación desplegada en AWS con una URL pública que funcione hasta el día del pitch.
- Presentación del pitch (PDF, PPT o PPTX, máximo 20 MB).
- Video de demostración (opcional): enlace público.
- Track A: URL del endpoint POST /paso, cómo ejecutar el simulador y cómo se mide la latencia, documentados en el README.

ESTRUCTURA SUGERIDA DEL REPOSITORIO
README.md
docs/arquitectura.png (o .svg) y docs/arquitectura.drawio
docs/costos.md
docs/budget.png
src/
infra/ (opcional: CDK, SAM o Terraform)

DEMO EN VIVO
Viernes 30 de octubre en la ULEAM: 5 minutos de pitch + 3 minutos de preguntas del jurado.

05
Recursos
SERVICIOS AWS SUGERIDOS (no hay arquitectura obligatoria)
- API de /paso: API Gateway + Lambda, o ECS Fargate con un contenedor.
- Estado del mundo: DynamoDB o ElastiCache (Redis).
- Mapa en la web: Amazon Location Service, o Leaflet con tiles abiertos.
- Hosting del front: S3 + CloudFront o Amplify.
- Tiempo real al panel: API Gateway WebSocket o AppSync.
- Monitoreo: CloudWatch (latencia y errores).
- Datos del mapa: OpenStreetMap (por ejemplo exportando Manta con Overpass o usando OSMnx).