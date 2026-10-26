# Navira — Escape de Manta Zombie

Proyecto para el Track A del hackathon: evacuación sobre un grafo de Manta con zombies móviles, rutas recalculadas y dos modos previstos: simulador automático y juego con un personaje humano.

**Estado real al 26 de octubre de 2026:** documentación preparada. Todavía no hay aplicación, pruebas de aplicación ejecutables, mapa generado ni despliegue AWS. Las tecnologías y contratos descritos son decisiones de diseño pendientes de implementar.

## Empezar

1. Agentes y colaboradores: leer [AGENTS.md](AGENTS.md) y seguir el protocolo de lectura antes de editar.
2. Documentación central: [doc/README.md](doc/README.md).
3. Qué estamos construyendo: [contexto](doc/contexto.md).
4. Qué existe y qué sigue: [estado actual](doc/estado-actual.md).
5. Tareas y dependencias: [plan de implementación](doc/plan-implementacion.md).

## Documentos principales

- [Arquitectura](doc/arquitectura.md), [módulos backend](doc/modulos/backend.md) y [módulos frontend](doc/modulos/frontend.md).
- [Reglas](doc/reglas-juego.md), [modos](doc/modos.md) y [flujos por rol](doc/flujos/roles.md).
- [API](doc/contratos/api.md), [eventos](doc/contratos/eventos.md) y [datos](doc/datos.md).
- [Pruebas](doc/pruebas.md), [infraestructura](doc/infraestructura.md), [seguridad](doc/seguridad.md) y [costos](doc/costos.md).
- [Decisiones](doc/decisiones/README.md), [pendientes](doc/pendientes.md), [cambios](doc/cambios.md) y [continuidad entre agentes](doc/continuidad.md).
- [PRD](doc/PRD.md), [TRD](doc/TRD.md), [ODDD: OO + DDD](doc/ODDD.md) y [SDD](doc/SDD.md).
- [Especificaciones por funcionalidad](doc/especificaciones/README.md) y [trazabilidad](doc/trazabilidad.md).

No hay comandos de instalación, endpoints operativos o métricas reales que podamos anunciar todavía. Se añadirán al implementar y verificar cada componente.

Comprobación documental disponible, sin dependencias externas:

```bash
python3 scripts/check_docs.py
```

Comprueba enlaces locales y que los Markdown de `doc/` sean accesibles desde su índice. No comprueba URLs externas, renderizado o comportamiento de la aplicación.

Validación estructural SDD y regresiones del comprobador:

```bash
python3 scripts/check_sdd.py
python3 -m unittest discover -s tests -p 'test_check_sdd.py'
```

La metodología está incorporada; las especificaciones funcionales todavía no representan una aplicación implementada o verificada.
