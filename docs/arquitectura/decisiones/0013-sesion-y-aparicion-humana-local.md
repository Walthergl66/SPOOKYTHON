# ADR-013 — Sesión propietaria y aparición humana local

Fecha: 2026-10-26  
Estado: implementada parcialmente en un adaptador local; no habilitada en la app predeterminada  
Origen: P4B-01 de SPEC-004

## Contexto

El mínimo de juego admite un jugador humano por partida activa. El navegador no puede decidir posición confirmada ni solicitar aparición cuando el turno ya movió zombies. P-11/P-12 dejan pendientes TLS pública, expiración y recuperación de sesión.

## Decisión

Agregar `UnirseAJuego` y `RepositorioSesionesMemoria`, inyectados explícitamente. Crear un token aleatorio opaco; almacenar solo SHA-256 como clave local y entregarlo solo mediante cookie `HttpOnly`, `Secure` por defecto, `SameSite=Strict`, `Path=/juego`. Rechazar Origin ausente o distinto. La sesión identifica run/personaje/estado, y CAS confirma la aparición en el snapshot.

En fase `PREPARACION`, elegir con el RNG privado del snapshot un nodo no-refugio, desocupado por sobrevivientes o zombies activos, no bloqueado, con ruta habilitada a un refugio. La fase de generación actualizada se guarda junto a la aparición para mantener reproducción. Si la fase ya pasó, reservar la única plaza como `esperando_aparicion`; el coordinador debe invocar el hook antes del movimiento zombie del siguiente turno. El jugador no recibe IDs, nodos ni razones asociadas a dormidos.

## Consecuencias y límites

- Una segunda sesión o unión concurrente no obtiene el personaje reservado.
- El `POST /juego/unirse` devuelve el estado de su personaje y nunca el token en JSON.
- Sesiones y snapshot usan adaptadores separados y locales: no hay transacción durable, alta disponibilidad, expiración, revocación automática ni recuperación tras reinicio.
- La aplicación y modo demo predeterminados no habilitan esta ruta; requiere una instancia explícitamente ensamblada con modo juego y repositorio de sesión.
- El juego no está listo para internet hasta resolver P-11/P-12, seguridad/deploy y conectar el hook al ciclo de turnos.

## Evidencia

CAM-036 y siete pruebas en `tests/test_juego_sesion.py`. Cubren creación, repetición de cookie, una plaza concurrente, aparición no válida, rechazo de modo simulador, espera hasta turno siguiente y Origin/cookie. No cubren orden humana ni continuidad durable.
