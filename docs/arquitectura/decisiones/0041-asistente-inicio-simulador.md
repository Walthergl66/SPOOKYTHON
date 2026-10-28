# ADR-041 — Inicio del Simulador por pasos y velocidad fija

- Estado: aceptada para implementación local.
- Fecha: 2026-10-27.
- Contexto: el panel libre mostraba controles de escenario, población, intensidad y velocidad antes de iniciar. La persona usuaria pidió que la vista inicial presente «Iniciar simulación», después permita escoger puntos seguros, y luego las cantidades de habitantes y zombies, dejando la velocidad en 4× sin selector.
- Decisión: usar un asistente de dos pasos dentro del diálogo del simulador. El primero exige asignar los cuatro refugios; el segundo permite conteos enteros de 1–200 para habitantes y zombies y crea el run al confirmar. El escenario mixto y 4× son valores fijos de esta experiencia. El cliente envía la cantidad de zombies; el generador conserva la composición y ubicación aleatorias y publica el conteo inicial en el estado del control local. El campo HTTP es opcional para clientes existentes; si se omite se conserva el fallback de intensidad.
- Alternativa descartada: mantener presets de intensidad en lugar de un conteo directo; no cumple la solicitud de elegir cantidad de zombies.
- Consecuencias: cambia solo el flujo de Simulador local, no los presets Reto, el modo humano ni `POST /paso`. El rango 1–200 es un límite de interfaz/control; el número real también está limitado por nodos disponibles no ocupados por habitantes. 42 es el valor inicial del tablero para conservar aproximadamente la densidad media anterior en el fixture Manta, no un parámetro oficial.
- Requisitos y aceptación: PRD-02, TRD-17, SPEC-007 CA-007-09/10.
- Verificación prevista: T-51, build y suite frontend, pruebas backend de generador/control, validadores documentales y smoke visual del flujo.
- Historial: [CAM-100](../../seguimiento/cambios.md#cam-100--asistente-de-inicio-y-configuración-del-simulador).
