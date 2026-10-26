# ADR-007 — Mapa de Manta y evidencia diferenciada por amenaza

Fecha: 2026-10-26  
Estado: aceptada para fixture de simulación  
Origen: solicitud del usuario de considerar zonas seguras frente a tsunami o terremoto en Manta, Ecuador.  

## Contexto y restricciones

P1-01 requiere unas 300 intersecciones y cuatro refugios. Navira no está certificada para emergencias. El mapa de evacuación por tsunami del GAD Manta publica zonas seguras por parroquia; esa fuente no constituye evaluación sísmica de cada sitio. El dataset vial público requiere atribución y conservar procedencia.

## Decisión

Usar OSM como fuente de red vial para el fixture reproducible de Manta y transcribir cuatro puntos finales que el GAD Manta marca como “Zona Segura” en sus mapas de evacuación por tsunami: Cristo Rey (Tarqui), Colinas de Rocafuerte (Los Esteros), La Dolorosa y Plaza del Sol (Manta). Guardar fecha de extracción, límites, versión/hash, atribución/licencia y distancia de ajuste a la red en un sidecar de fuentes.

Registrar evidencia de tsunami por separado de la evaluación sísmica. Marcar sismo como no evaluado mientras no existan datos locales de microzonificación, suelo y estructuras que respalden una clasificación. El fixture es para simulación de hackathon y no se publica como navegación ni guía de emergencia.

## Alternativas consideradas

- Llamar “seguros ante desastres” a los mismos puntos: rechazado porque la fuente confirma una capa de evacuación por tsunami, no seguridad frente a todos los peligros.
- Elegir refugios solo por altura o distancia de la costa: rechazado porque no prueba acceso, suelo ni resistencia estructural.
- Esperar a disponer de capas cartográficas perfectas antes de crear el fixture: rechazado para el avance local; el mapa se mantiene en estado parcial y no se presenta como evaluación completa.

## Consecuencias y pendientes

Se puede probar un grafo realista de tamaño aproximado, con cuatro destinos oficiales de tsunami. La cobertura incluida es una muestra conectada a refugios y no representa exhaustivamente todos los barrios ni rutas peatonales. Los límites de velocidad por defecto son parámetros de juego. P-13 conserva la validación de extensión/cobertura; P-14 registra la evaluación sísmica faltante. Una futura afirmación de seguridad requiere una fuente competente y validación específica por amenaza.

Documentos propietarios: [datos](../datos.md), [reglas](../reglas-juego.md), [mapa Manta](../mapa-manta.md), [pendientes](../pendientes.md), [plan](../plan-implementacion.md) y [SPEC-001](../especificaciones/SPEC-001-mundo-simulacion.md).

Evidencia de implementación: CAM-021 y [fixture con fuentes](../../data/maps/manta-hackathon-v1.fuentes.json). La prueba valida 300 nodos, cuatro nodos-refugio distintos, camino dirigido a refugio para cada nodo incluido, procedencia/atribución y estado sísmico no evaluado.
