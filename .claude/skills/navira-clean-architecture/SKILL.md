---
name: navira-clean-architecture
description: Usar al mover código entre capas, crear un puerto o adaptador, o dividir un módulo del backend o del frontend de Navira; sigue la guía de Clean Architecture y su línea base.
---

# Clean Architecture en Navira

Fuente canónica: [guía de Clean Architecture](../../../docs/arquitectura/guia-clean-architecture.md). Decisión: [ADR-025](../../../docs/arquitectura/decisiones/0025-agentes-de-proyecto-y-clean-architecture.md). No copies la guía aquí; sigue sus pasos.

1. **Elige el paso.** Busca el paso B1–B6 (backend) o F1–F6 (frontend) de la guía. Si la tarea no encaja en ninguno, descríbela como nuevo paso antes de tocar código.
2. **Consulta a un subagente de arquitectura** antes de editar: `arquitecto-backend` o `arquitecto-frontend` (Opus, solo lectura). Pide el diagnóstico y el plan del paso, no la implementación.
3. **Implementa solo ese paso.** Mantén la regla de dependencia: el núcleo no importa FastAPI, boto3, React ni `fetch`; los puertos se definen en la capa que los usa; los adaptadores los implementan.
4. **Verifica.** Backend: `cd backend && python -m unittest discover -s tests -p 'test_*.py' -v`, con las pruebas del paso en verde. Frontend: `cd frontend && npm run build`. Después, `revisor-arquitectura` con las búsquedas de la guía: no debe haber violaciones nuevas.
5. **Registra.** `documentador-sdd` añade el CAM, actualiza `docs/seguimiento/estado-actual.md` y ejecuta los validadores. Si el paso cambia un contrato, actualiza `docs/arquitectura/contratos/api.md`.

Límites:
- No cambies el contrato de `POST /paso`, el límite de 500 ms ni la ocultación de dormidos y RNG.
- No crees capas, servicios ni puertos sin una necesidad concreta.
- F6 (pruebas y lint del frontend) requiere aprobación del usuario; no lo añadas dentro de un paso.
