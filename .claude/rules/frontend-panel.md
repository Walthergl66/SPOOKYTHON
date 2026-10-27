---
paths:
  - "frontend/src/**"
---
# Frontend y panel

Fuentes: [módulos frontend](../../docs/arquitectura/modulos/frontend.md), [guía de Clean Architecture](../../docs/arquitectura/guia-clean-architecture.md), [eventos](../../docs/arquitectura/contratos/eventos.md), [SPEC-003](../../docs/metodo/especificaciones/SPEC-003-panel-vivo.md), [SPEC-004](../../docs/metodo/especificaciones/SPEC-004-juego-humano.md), [SPEC-007](../../docs/metodo/especificaciones/SPEC-007-panel-operador-local.md).

- El navegador no modifica el mundo: envía órdenes y muestra estado. Posición, turno, mordida y propiedad los decide el servidor; una animación nunca confirma un movimiento.
- Toda respuesta HTTP/WebSocket se parsea y valida en `shared/api` o `shared/realtime`; los componentes reciben tipos del producto, no JSON sin comprobar.
- La cookie de sesión es `HttpOnly` y no se lee ni se guarda desde JavaScript. Clientes same-origin; sin `localStorage` de tokens.
- Ninguna API key de servicio ni credencial administrativa en código, `.env` expuestos por Vite (`VITE_*`) o bundle. Los controles de demo local no transmiten claves.
- Solo se consume la proyección observable: no asumir ni mostrar dormidos ocultos ni estado aleatorio.
- Cada `panel.snapshot` reemplaza el estado completo; descartar secuencias repetidas/antiguas y cambiar de `runId` reemplaza la partida. Mostrar desconexión y desactualización sin simular conexión.
- Orden humana: `sin_orden → enviando → recibida → aplicada`. Un acuse es recepción, no movimiento; una sugerencia de radio solo se envía tras acción explícita.
- Rutas previstas y riesgos estimados se distinguen visualmente de posiciones confirmadas; el contador `decisionRestanteMs` es informativo, no autoridad.
- Accesibilidad por teclado (T-19): controles nativos con etiqueta, foco visible, sin depender de hover ni de color solamente; respetar movimiento reducido.
- No reconstruir capas completas del mapa por turno en el hilo principal. Los datos de Navira no se envían al proveedor de tiles.
- Verificar con `npm run build` desde `frontend/`; esto no sustituye auditoría T-19 ni pruebas de navegador.
