# Navira frontend

Frontend web mínimo de Navira, construido con React, TypeScript y Vite. Ejecutar desde esta carpeta:

```bash
npm ci
npm run dev
```

La pantalla inicial presenta los modos simulador y juego, con una vista cartográfica ilustrativa de Manta. El selector solo cambia la vista previa; no inicia partidas ni se conecta al backend. El panel en vivo, capas reales, refugios, rutas, métricas y sincronización pertenecen a P4-01/P4-02 y requieren los contratos de panel/eventos.

Para comprobar la salida de producción:

```bash
npm run build
```
