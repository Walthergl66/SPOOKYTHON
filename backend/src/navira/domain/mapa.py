"""Modelo y carga validada del grafo vial de Navira.

Las calles dirigidas conservan un ID de segmento físico compartido cuando
representan los dos sentidos de una misma calle. Así, los cierres pueden
aplicarse por dirección o al segmento completo sin confundir calles paralelas.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


class TipoCalle(StrEnum):
    """Categorías viales reconocidas en el reto."""

    AVENIDA = "avenida"
    CALLE = "calle"
    CALLEJON = "callejon"
    PUENTE = "puente"


@dataclass(frozen=True, slots=True)
class Nodo:
    """Intersección de la ciudad expresada en coordenadas WGS84."""

    id: str
    lat: float
    lng: float

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("El nodo requiere un id no vacío.")
        if not math.isfinite(self.lat) or not -90 <= self.lat <= 90:
            raise ValueError(f"Latitud fuera de rango para el nodo {self.id}.")
        if not math.isfinite(self.lng) or not -180 <= self.lng <= 180:
            raise ValueError(f"Longitud fuera de rango para el nodo {self.id}.")


@dataclass(frozen=True, slots=True)
class Calle:
    """Arista dirigida; segmento_id identifica el tramo físico subyacente."""

    id: str
    segmento_id: str
    origen: str
    destino: str
    distancia_m: float
    tipo: TipoCalle
    velocidad_kmh: float

    def __post_init__(self) -> None:
        for nombre, valor in (
            ("id", self.id),
            ("segmento_id", self.segmento_id),
            ("origen", self.origen),
            ("destino", self.destino),
        ):
            if not valor.strip():
                raise ValueError(f"La calle requiere {nombre} no vacío.")
        if self.origen == self.destino:
            raise ValueError(f"La calle {self.id} no puede conectar un nodo consigo mismo.")
        if not math.isfinite(self.distancia_m) or self.distancia_m <= 0:
            raise ValueError(f"La distancia de la calle {self.id} debe ser positiva y finita.")
        if not math.isfinite(self.velocidad_kmh) or self.velocidad_kmh <= 0:
            raise ValueError(f"La velocidad de la calle {self.id} debe ser positiva y finita.")
        if not isinstance(self.tipo, TipoCalle):
            raise ValueError(f"La categoría de la calle {self.id} no está reconocida.")


@dataclass(frozen=True, slots=True)
class Refugio:
    """Destino fijo dentro del grafo."""

    id: str
    nodo: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.nodo.strip():
            raise ValueError("El refugio requiere id y nodo no vacíos.")


@dataclass(frozen=True, slots=True)
class Mapa:
    """Conjunto inmutable de nodos, sentidos de calle y refugios."""

    version: str
    nodos: tuple[Nodo, ...]
    calles: tuple[Calle, ...]
    refugios: tuple[Refugio, ...]
    _nodos_por_id: Mapping[str, Nodo] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("El mapa requiere una versión no vacía.")
        object.__setattr__(self, "nodos", tuple(self.nodos))
        object.__setattr__(self, "calles", tuple(self.calles))
        object.__setattr__(self, "refugios", tuple(self.refugios))
        nodos_por_id = _indice_unico(self.nodos, "id", "nodo")
        _indice_unico(self.calles, "id", "calle")
        _indice_unico(self.refugios, "id", "refugio")
        if not nodos_por_id:
            raise ValueError("El mapa debe contener al menos un nodo.")

        for calle in self.calles:
            if calle.origen not in nodos_por_id or calle.destino not in nodos_por_id:
                raise ValueError(f"La calle {calle.id} referencia un nodo inexistente.")
        for refugio in self.refugios:
            if refugio.nodo not in nodos_por_id:
                raise ValueError(f"El refugio {refugio.id} referencia un nodo inexistente.")

        object.__setattr__(self, "_nodos_por_id", MappingProxyType(nodos_por_id))

    @property
    def nodos_por_id(self) -> Mapping[str, Nodo]:
        """Índice de solo lectura para consultas por identificador."""

        return self._nodos_por_id

    def validar_mapa_evaluacion(self, minimo_nodos: int = 200) -> None:
        """Exige el tamaño aproximado y los cuatro refugios del reto.

        El mínimo permite tolerar variaciones al recortar OSM; el umbral se
        puede reducir explícitamente en grafos sintéticos de prueba.
        """

        if minimo_nodos < 1:
            raise ValueError("minimo_nodos debe ser al menos 1.")
        if len(self.nodos) < minimo_nodos:
            raise ValueError(
                f"El mapa tiene {len(self.nodos)} nodos; se requieren al menos {minimo_nodos}."
            )
        if len(self.refugios) != 4:
            raise ValueError(f"El mapa de evaluación requiere 4 refugios; recibió {len(self.refugios)}.")
        if len({refugio.nodo for refugio in self.refugios}) != 4:
            raise ValueError("Los cuatro refugios deben ocupar nodos distintos.")


class Grafo:
    """Índice de adyacencia dirigido sobre un mapa inmutable."""

    def __init__(self, mapa: Mapa) -> None:
        self.mapa = mapa
        por_origen: dict[str, list[Calle]] = {nodo_id: [] for nodo_id in mapa.nodos_por_id}
        for calle in mapa.calles:
            por_origen[calle.origen].append(calle)
        self._salientes = MappingProxyType(
            {nodo_id: tuple(sorted(calles, key=lambda calle: calle.id)) for nodo_id, calles in por_origen.items()}
        )

    def calles_desde(
        self,
        nodo_id: str,
        *,
        aristas_cerradas: frozenset[str] = frozenset(),
        segmentos_cerrados: frozenset[str] = frozenset(),
    ) -> tuple[Calle, ...]:
        """Devuelve sentidos salientes habilitados, respetando ambos cierres.

        Un cierre por arista afecta solo ese sentido. Un cierre por segmento
        físico afecta a todas sus aristas, incluida la dirección opuesta.
        """

        if nodo_id not in self._salientes:
            raise KeyError(f"Nodo desconocido: {nodo_id}")
        return tuple(
            calle
            for calle in self._salientes[nodo_id]
            if calle.id not in aristas_cerradas and calle.segmento_id not in segmentos_cerrados
        )

    def vecinos_desde(self, nodo_id: str, **cierres: frozenset[str]) -> tuple[str, ...]:
        """Lista destinos adyacentes únicos en orden estable por ID de calle."""

        return tuple(calle.destino for calle in self.calles_desde(nodo_id, **cierres))


def nodos_elegibles_refugio(mapa: Mapa) -> tuple[Nodo, ...]:
    """Nodos con al menos una calle de entrada y una de salida."""

    con_entrada = {calle.destino for calle in mapa.calles}
    con_salida = {calle.origen for calle in mapa.calles}
    return tuple(nodo for nodo in mapa.nodos if nodo.id in con_entrada and nodo.id in con_salida)


def mapa_con_refugios(mapa: Mapa, refugios: tuple[Refugio, ...]) -> Mapa:
    """Copia del mapa con cuatro refugios R-01..R-04 elegidos por el operador.

    Valida ids, nodos distintos y elegibilidad; la versión resultante lleva un
    sufijo con hash para no confundirse con el mapa base.
    """

    if sorted(refugio.id for refugio in refugios) != ["R-01", "R-02", "R-03", "R-04"]:
        raise ValueError("Se requieren exactamente 4 refugios con ids R-01, R-02, R-03 y R-04, cada uno una vez.")
    if len({refugio.nodo for refugio in refugios}) != 4:
        raise ValueError("Los cuatro refugios deben ocupar nodos distintos.")
    elegibles = {nodo.id for nodo in nodos_elegibles_refugio(mapa)}
    for refugio in refugios:
        if refugio.nodo not in mapa.nodos_por_id:
            raise ValueError(f"El nodo {refugio.nodo} del refugio {refugio.id} no existe en el mapa.")
        if refugio.nodo not in elegibles:
            raise ValueError(
                f"El nodo {refugio.nodo} del refugio {refugio.id} no tiene calle de entrada y de salida."
            )
    ordenados = tuple(sorted(refugios, key=lambda refugio: refugio.id))
    huella = hashlib.sha1("|".join(f"{r.id}:{r.nodo}" for r in ordenados).encode()).hexdigest()[:8]
    return Mapa(
        version=f"{mapa.version}+refugios-{huella}",
        nodos=mapa.nodos,
        calles=mapa.calles,
        refugios=ordenados,
    )


def cargar_mapa(ruta: str | Path) -> Mapa:
    """Carga JSON validando estructura, referencias e invariantes del dominio."""

    try:
        contenido = json.loads(Path(ruta).read_text(encoding="utf-8"))
        nodos = tuple(Nodo(**elemento) for elemento in contenido["nodos"])
        calles = tuple(
            Calle(
                id=elemento["id"],
                segmento_id=elemento["segmentoId"],
                origen=elemento["origen"],
                destino=elemento["destino"],
                distancia_m=elemento["distancia_m"],
                tipo=TipoCalle(elemento["tipo"]),
                velocidad_kmh=elemento["velocidad_kmh"],
            )
            for elemento in contenido["calles"]
        )
        refugios = tuple(
            Refugio(id=elemento["id"], nodo=elemento["nodo"])
            for elemento in contenido["refugios"]
        )
        return Mapa(
            version=contenido["version"],
            nodos=nodos,
            calles=calles,
            refugios=refugios,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"Mapa inválido en {ruta}: {error}") from error


def _indice_unico(elementos: tuple[object, ...], campo: str, entidad: str) -> dict[str, object]:
    indice: dict[str, object] = {}
    for elemento in elementos:
        identificador = getattr(elemento, campo)
        if identificador in indice:
            raise ValueError(f"Id de {entidad} duplicado: {identificador}.")
        indice[identificador] = elemento
    return indice
