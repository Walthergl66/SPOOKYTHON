export interface PlayerSession {
  runId: string
  playerId: string
  status: 'esperando_aparicion' | 'activo'
  node: string | null
}

export interface GameOrderReceipt {
  accionId: string
  secuencia: number
  estado: 'recibida'
  turno: number
}

export interface GameOrderInput {
  runId: string
  turno: number
  personajeId: string
  siguienteNodo: string
  accionId: string
}

export class GameApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
    this.name = 'GameApiError'
  }
}

/** La cookie HttpOnly permanece en el navegador; JavaScript solo recibe la identidad propia. */
export async function joinGame(): Promise<PlayerSession> {
  const response = await fetch('/juego/unirse', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  })
  const value = await readJson(response)
  if (!isRecord(value) || typeof value.runId !== 'string' || typeof value.jugadorId !== 'string' ||
    (value.estado !== 'esperando_aparicion' && value.estado !== 'activo') ||
    !(typeof value.nodo === 'string' || value.nodo === null)) {
    throw new GameApiError('El servicio devolvió una sesión con formato no válido.', response.status)
  }
  return { runId: value.runId, playerId: value.jugadorId, status: value.estado, node: value.nodo }
}

/** Devuelve solo el acuse del servidor; no confirma que el personaje ya se movió. */
export async function sendGameOrder(order: GameOrderInput): Promise<GameOrderReceipt> {
  const response = await fetch('/juego/accion', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify(order),
  })
  const value = await readJson(response)
  if (!isRecord(value) || typeof value.accionId !== 'string' || typeof value.secuencia !== 'number' ||
    value.estado !== 'recibida' || typeof value.turno !== 'number') {
    throw new GameApiError('El servicio devolvió un acuse con formato no válido.', response.status)
  }
  return { accionId: value.accionId, secuencia: value.secuencia, estado: 'recibida', turno: value.turno }
}

async function readJson(response: Response): Promise<unknown> {
  let value: unknown
  try {
    value = await response.json()
  } catch {
    throw new GameApiError('No se pudo leer la respuesta del modo juego.', response.status)
  }
  if (!response.ok) {
    const detail = isRecord(value) && typeof value.detail === 'string' ? value.detail : 'La solicitud de juego fue rechazada.'
    throw new GameApiError(detail, response.status)
  }
  return value
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
