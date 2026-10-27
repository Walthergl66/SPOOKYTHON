# Frontend Navira (`frontend/`)

Referencia: [módulos frontend](../docs/arquitectura/modulos/frontend.md), [contrato de eventos](../docs/arquitectura/contratos/eventos.md) y [SPEC-008 mapa](../docs/metodo/especificaciones/SPEC-008-mapa-cartografico-3d.md).

## Stack (`package.json`)

React 19.3.1, TypeScript 7.0.2, Vite 8.3.5 con `@vitejs/plugin-react` 6.1.2, MapLibre GL JS 6.16.0. Scripts: `npm run dev`, `npm run build` (`tsc -b && vite build`), `npm run preview`.

## Estructura de `src/`

- `app/`: composición y selector de modo.
- `features/`: `game/` (unirse y órdenes), `map/` (MapLibre y capas), `mode/` (tarjetas de modo).
- `shared/`: `api/` (HTTP), `realtime/` (WebSocket), `ui/` (componentes comunes).

## Vite

El proxy de desarrollo reenvía `/salud`, `/panel`, `/juego`, `/demo` y `/ws` (WebSocket) a `NAVIRA_API_TARGET` o `http://127.0.0.1:8000` (`vite.config.ts`).

## Reglas

- Única frontera HTTP en `shared/api`; validar respuestas allí. Los componentes reciben tipos del producto, no JSON sin comprobar.
- El servidor manda sobre posiciones, turnos, mordidas y propiedad; una animación o sugerencia no confirma un movimiento.
- Sin claves de servicio, credenciales administrativas ni dormidos ocultos en el bundle ni en mensajes; la cookie de sesión es HttpOnly.
- El proveedor de mapas externo (OpenFreeMap) solo para la capa base; no enviarle datos de Navira.
- Accesibilidad: foco visible, teclado, sin depender solo del color, respetar movimiento reducido.
