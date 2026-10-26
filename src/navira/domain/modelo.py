"""Entidades e intenciones del mundo compartido de Navira.

Este módulo registra estado e invariantes de identidad. No mueve zombies ni
resuelve mordidas: esas políticas pertenecen al servicio de simulación.
"""

from dataclasses import dataclass
from enum import StrEnum

from navira.domain.mapa import Mapa


class ModoPartida(StrEnum):
    SIMULADOR = "simulador"
    JUEGO = "juego"


class EstadoPartida(StrEnum):
    PREPARADA = "preparada"
    ACTIVA = "activa"
    FINALIZADA = "finalizada"
    INTERRUMPIDA = "interrumpida"


class FaseTurno(StrEnum):
    PREPARACION = "preparacion"
    ZOMBIES_MOVIDOS = "zombies_movidos"
    DECISIONES = "decisiones"
    RESUELTA = "resuelta"


class ControlSobreviviente(StrEnum):
    AUTOMATICO = "automatico"
    HUMANO = "humano"


class EstadoSobreviviente(StrEnum):
    ACTIVO = "activo"
    MORDIDO = "mordido"
    EVACUADO = "evacuado"


class TipoZombie(StrEnum):
    CAMINANTE = "caminante"
    CORREDOR = "corredor"
    HORDA = "horda"
    DORMIDO = "dormido"


class EstadoZombie(StrEnum):
    ACTIVO = "activo"
    DORMIDO = "dormido"


@dataclass(frozen=True, slots=True)
class Sobreviviente:
    """Personaje del mundo; su control solo cambia quién produce intención."""

    id: str
    nodo: str
    control: ControlSobreviviente = ControlSobreviviente.AUTOMATICO
    estado: EstadoSobreviviente = EstadoSobreviviente.ACTIVO
    refugio_objetivo: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.nodo.strip():
            raise ValueError("El sobreviviente requiere id y nodo no vacíos.")
        if not isinstance(self.control, ControlSobreviviente):
            raise ValueError("Control de sobreviviente no reconocido.")
        if not isinstance(self.estado, EstadoSobreviviente):
            raise ValueError("Estado de sobreviviente no reconocido.")
        if self.refugio_objetivo is not None and not self.refugio_objetivo.strip():
            raise ValueError("El refugio objetivo no puede ser vacío.")


@dataclass(frozen=True, slots=True)
class Zombie:
    """Zombie con fase privada; la proyección observable se define aparte."""

    id: str
    tipo: TipoZombie
    nodo: str
    estado: EstadoZombie = EstadoZombie.ACTIVO
    turno_activacion: int | None = None
    fase_movimiento: int = 0

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.nodo.strip():
            raise ValueError("El zombie requiere id y nodo no vacíos.")
        if not isinstance(self.tipo, TipoZombie):
            raise ValueError("Tipo de zombie no reconocido.")
        if not isinstance(self.estado, EstadoZombie):
            raise ValueError("Estado de zombie no reconocido.")
        if (self.tipo is TipoZombie.DORMIDO) != (self.estado is EstadoZombie.DORMIDO):
            raise ValueError("Solo un zombie de tipo dormido puede estar en estado dormido.")
        if self.turno_activacion is not None and self.turno_activacion < 0:
            raise ValueError("El turno de activación no puede ser negativo.")
        if self.fase_movimiento not in (0, 1):
            raise ValueError("La fase de movimiento del caminante debe ser 0 o 1.")


@dataclass(frozen=True, slots=True)
class Partida:
    """Raíz de consistencia: modo/versiones fijos y colecciones inmutables."""

    run_id: str
    modo: ModoPartida
    escenario: str
    map_version: str
    sobrevivientes: tuple[Sobreviviente, ...] = ()
    zombies: tuple[Zombie, ...] = ()
    estado: EstadoPartida = EstadoPartida.PREPARADA
    turno: int = 0
    fase: FaseTurno = FaseTurno.PREPARACION

    def __post_init__(self) -> None:
        if not all(valor.strip() for valor in (self.run_id, self.escenario, self.map_version)):
            raise ValueError("Partida requiere run_id, escenario y map_version.")
        if not isinstance(self.modo, ModoPartida):
            raise ValueError("El modo de partida no es válido.")
        if not isinstance(self.estado, EstadoPartida) or not isinstance(self.fase, FaseTurno):
            raise ValueError("Estado o fase de partida no reconocidos.")
        if self.turno < 0:
            raise ValueError("El turno de partida no puede ser negativo.")

        object.__setattr__(self, "sobrevivientes", tuple(self.sobrevivientes))
        object.__setattr__(self, "zombies", tuple(self.zombies))
        ids = [entidad.id for entidad in (*self.sobrevivientes, *self.zombies)]
        if len(ids) != len(set(ids)):
            raise ValueError("Los IDs de personajes y zombies deben ser únicos en la partida.")

    def validar_mapa(self, mapa: Mapa) -> None:
        """Comprueba que la partida usa el mapa versionado y nodos existentes."""

        if self.map_version != mapa.version:
            raise ValueError("La versión de mapa no coincide con la partida.")
        nodos = mapa.nodos_por_id
        refugios = {refugio.id for refugio in mapa.refugios}
        for entidad in (*self.sobrevivientes, *self.zombies):
            if entidad.nodo not in nodos:
                raise ValueError(f"{entidad.id} referencia el nodo inexistente {entidad.nodo}.")
        for sobreviviente in self.sobrevivientes:
            if sobreviviente.refugio_objetivo is not None and sobreviviente.refugio_objetivo not in refugios:
                raise ValueError(
                    f"{sobreviviente.id} referencia el refugio inexistente {sobreviviente.refugio_objetivo}."
                )


@dataclass(frozen=True, slots=True)
class IntencionMovimiento:
    """Propuesta de destino, ligada a una partida, fase y turno concretos."""

    run_id: str
    turno: int
    fase: FaseTurno
    sobreviviente_id: str
    destino: str

    def __post_init__(self) -> None:
        if not all(valor.strip() for valor in (self.run_id, self.sobreviviente_id, self.destino)):
            raise ValueError("La intención requiere partida, sobreviviente y destino.")
        if self.turno < 0:
            raise ValueError("El turno de la intención no puede ser negativo.")
        if not isinstance(self.fase, FaseTurno):
            raise ValueError("La fase de la intención no es válida.")


def validar_contexto_intencion(partida: Partida, sobreviviente: Sobreviviente, intencion: IntencionMovimiento) -> None:
    """Verifica identidad temporal antes de cualquier política de movimiento."""

    if partida.estado is not EstadoPartida.ACTIVA:
        raise ValueError("La partida no está activa.")
    if partida.fase is not FaseTurno.DECISIONES or intencion.fase is not FaseTurno.DECISIONES:
        raise ValueError("La intención solo se acepta en la fase de decisiones.")
    if intencion.run_id != partida.run_id or intencion.turno != partida.turno:
        raise ValueError("La intención pertenece a otra partida o turno.")
    if intencion.sobreviviente_id != sobreviviente.id:
        raise ValueError("La intención no pertenece a este sobreviviente.")
    if sobreviviente.estado is not EstadoSobreviviente.ACTIVO:
        raise ValueError("Un sobreviviente inactivo no puede producir intención.")
