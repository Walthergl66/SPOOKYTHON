"""Catálogo ficticio de perfiles narrativos, independiente de las reglas."""

from __future__ import annotations

import hashlib
import random
from dataclasses import replace
from typing import Iterable

from navira.domain.modelo import PerfilNarrativo, Sobreviviente


VERSION_CATALOGO_PERFILES = 1
TOTAL_PERFILES_NARRATIVOS = 500

_NOMBRES = (
    "Ana", "Andrés", "Camila", "Carlos", "Daniela", "David", "Elena", "Emilio",
    "Fernanda", "Gabriel", "Isabel", "Javier", "Lucía", "Manuel", "María",
    "Mateo", "Mónica", "Nicolás", "Paola", "Pablo", "Rosa", "Sofía", "Tomás",
    "Valeria", "Víctor",
)
_APELLIDOS = (
    "Acosta", "Alcívar", "Andrade", "Ávila", "Cedeño", "Delgado", "Egas", "Farías",
    "García", "Gómez", "Loor", "López", "Mendoza", "Mera", "Moreira", "Párraga",
    "Pincay", "Reyes", "Salazar", "Zambrano",
)
_OCUPACIONES = (
    ("comercio", "Conoce el ritmo del comercio local y procura apoyar a su comunidad."),
    ("docencia", "Disfruta compartir conocimientos y mantener la calma ante los imprevistos."),
    ("estudiante", "Mantiene curiosidad por su ciudad y suele aprender de quienes le rodean."),
    ("transporte", "Se orienta por la ciudad y presta atención a los caminos."),
    ("pesca", "Valora el trabajo en equipo y conoce las rutinas junto al mar."),
    ("artesanía", "Dedica tiempo a crear objetos útiles y aprecia las tradiciones locales."),
    ("salud", "Suele ofrecer ayuda práctica y mantener la serenidad en momentos difíciles."),
    ("gastronomía", "Disfruta reunir a las personas y compartir recetas de su entorno."),
    ("mecánica", "Tiene facilidad para resolver problemas cotidianos con paciencia."),
    ("agricultura", "Valora el esfuerzo constante y los vínculos de colaboración."),
    ("diseño", "Observa los detalles de su entorno y busca soluciones creativas."),
    ("biblioteca", "Disfruta aprender, organizar información y compartirla con otras personas."),
    ("deporte", "Encuentra motivación en la constancia y en avanzar junto a su equipo."),
    ("emprendimiento", "Le gusta convertir ideas en proyectos y construir relaciones de confianza."),
    ("soporte técnico", "Suele analizar cada situación paso a paso antes de actuar."),
    ("música", "Encuentra inspiración en los sonidos y las historias de su ciudad."),
    ("conservación ambiental", "Siente aprecio por los espacios naturales y el cuidado colectivo."),
    ("contabilidad", "Prefiere organizar sus actividades y planificar con anticipación."),
    ("panadería", "Disfruta los oficios cotidianos y el contacto cercano con sus vecinos."),
    ("fotografía", "Presta atención a los cambios de su entorno y guarda recuerdos en imágenes."),
)
_MATICES = (
    "En sus ratos libres disfruta caminar por espacios públicos.",
    "Suele mantenerse en contacto con amistades y familiares.",
    "Le gusta conocer nuevas historias de las personas de su ciudad.",
    "Prefiere organizar sus actividades y colaborar cuando hace falta.",
    "Disfruta aprender rutas y lugares nuevos de forma tranquila.",
)


def _crear_catalogo() -> tuple[PerfilNarrativo, ...]:
    """Compone 500 registros compactos y únicos desde vocabulario curado."""

    perfiles: list[PerfilNarrativo] = []
    for indice in range(TOTAL_PERFILES_NARRATIVOS):
        nombre = _NOMBRES[indice % len(_NOMBRES)]
        apellido = _APELLIDOS[indice // len(_NOMBRES)]
        ocupacion, frase = _OCUPACIONES[indice % len(_OCUPACIONES)]
        matiz = _MATICES[(indice // len(_NOMBRES)) % len(_MATICES)]
        perfiles.append(
            PerfilNarrativo(
                id=f"NAV-P{indice + 1:04d}",
                nombre=f"{nombre} {apellido}",
                edad=18 + ((indice * 17 + 11) % 58),
                ocupacion=ocupacion,
                descripcion=f"{frase} {matiz}",
            )
        )
    return tuple(perfiles)


CATALOGO_PERFILES_NARRATIVOS = _crear_catalogo()


def asignar_perfiles_narrativos(
    sobrevivientes: Iterable[Sobreviviente], semilla: int
) -> tuple[Sobreviviente, ...]:
    """Asigna perfiles sin repetir usando RNG aislado de la simulación.

    La semilla derivada no consume el generador del mundo: sumar esta narración
    no cambia zombies, cierres, posiciones ni decisiones del run.
    """

    personas = tuple(sobrevivientes)
    if len(personas) > len(CATALOGO_PERFILES_NARRATIVOS):
        raise ValueError("La población supera el catálogo de perfiles narrativos.")
    digest = hashlib.sha256(
        f"navira-perfiles-v{VERSION_CATALOGO_PERFILES}:{semilla}".encode("utf-8")
    ).digest()
    indices = random.Random(int.from_bytes(digest[:8], "big")).sample(
        range(len(CATALOGO_PERFILES_NARRATIVOS)), len(personas)
    )
    return tuple(
        replace(persona, perfil_narrativo=CATALOGO_PERFILES_NARRATIVOS[indice])
        for persona, indice in zip(personas, indices, strict=True)
    )


def perfil_narrativo_disponible(
    sobrevivientes: Iterable[Sobreviviente], *, run_id: str, sobreviviente_id: str
) -> PerfilNarrativo:
    """Elige un perfil no usado para un habitante agregado durante el run."""

    usados = {
        persona.perfil_narrativo.id
        for persona in sobrevivientes
        if persona.perfil_narrativo is not None
    }
    disponibles = tuple(
        perfil for perfil in CATALOGO_PERFILES_NARRATIVOS if perfil.id not in usados
    )
    if not disponibles:
        raise ValueError("No quedan perfiles narrativos disponibles en este run.")
    digest = hashlib.sha256(
        f"navira-perfil-nuevo-v{VERSION_CATALOGO_PERFILES}:{run_id}:{sobreviviente_id}".encode("utf-8")
    ).digest()
    indice = int.from_bytes(digest[:8], "big") % len(disponibles)
    return disponibles[indice]
