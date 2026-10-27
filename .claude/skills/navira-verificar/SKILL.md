---
name: navira-verificar
description: Usar cuando se pida verificar, probar o comprobar que algo funciona en Navira; elige los comandos del área tocada y reporta resultados reales sin sobreafirmar.
---

# Verificar con honestidad

Fuentes: [pruebas](../../../docs/calidad/pruebas.md) (matriz T-01 a T-37) y [SDD](../../../docs/metodo/SDD.md) (comandos). Usar `docs/`.

1. Identificar el área tocada y sus T-NN en `pruebas.md`.
2. Elegir solo los comandos de esa área (tabla); no ejecutar toda la batería sin motivo.
3. Ejecutarlos con el `backend/.venv` (nunca `/tmp/navira-env`). En fish, variables con `env VAR=valor comando`.
4. Reportar la salida real: éxitos, fallos y errores tal cual; leer y diagnosticar un fallo antes de repetir.
5. Separar explícitamente lo verificado de lo no ejecutado y la causa.
6. No declarar el sistema desplegado, seguro ni con rendimiento medido sin evidencia real (p95, carga, AWS son metas hasta medirlas).

| Área | Comando | Demuestra / no demuestra |
|---|---|---|
| Backend | `cd backend && python -m unittest discover -s tests -p 'test_*.py' -v` | Reglas, resolutor, planificador y contrato HTTP locales. No carga, persistencia durable ni despliegue. |
| Frontend | `cd frontend && npm ci && npm run build` | Compilación TypeScript/bundle. No comportamiento visual ni accesibilidad. |
| Docs | `python backend/scripts/check_docs.py` | Enlaces e inventario (T-20). No prueba la app. |
| SDD | `python backend/scripts/check_sdd.py` | IDs, trazabilidad y evidencia (T-21). No mide latencia ni seguridad. |
| Validador SDD | `python3 -m unittest discover -s backend/tests -p 'test_check_sdd.py'` | Regresiones del comprobador SDD. |

## Cierre

Al terminar: lista de comandos ejecutados con resultado, lista de lo no ejecutado con motivo, y el riesgo material restante. Si cambió documentación, añadir los validadores.
