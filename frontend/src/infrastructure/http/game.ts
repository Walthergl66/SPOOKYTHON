import { GameOrderRejectedError, GameSessionExpiredError, GameSessionMissingError, parseGameOrderReceipt, parsePlayerSession, type GameOrderInput, type GameOrderReceipt, type PlayerSession } from '../../domain/game'

export class GameApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
    this.name = 'GameApiError'
  }
}

/** Traduce el status HTTP a un error de dominio; el mensaje se conserva siempre. */
export function httpError(message: string, status: number): Error {
  if (status === 403) return new GameSessionMissingError(message)
  if (status === 410) return new GameSessionExpiredError(message)
  if (status < 500) return new GameOrderRejectedError(message)
  return new GameApiError(message, status)
}

/** La cookie HttpOnly permanece en el navegador; JavaScript solo recibe la identidad propia. */
export async function joinGame(): Promise<PlayerSession> {
  const response = await fetch('/juego/unirse', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  })
  const value = await readJson(response)
  return wrap(() => parsePlayerSession(value), 'Respuesta de juego no válida')
}

/** Recupera solo una sesión propietaria existente; nunca crea una nueva. */
export async function restoreGameSession(signal?: AbortSignal): Promise<PlayerSession> {
  const response = await fetch('/juego/mi-personaje', {
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
    signal,
  })
  const value = await readJson(response)
  return wrap(() => parsePlayerSession(value), 'Respuesta de juego no válida')
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
  return wrap(() => parseGameOrderReceipt(value), 'Respuesta de juego no válida')
}

/** Un cuerpo 2xx que no cumple el contrato es un rechazo de dominio; se conserva el mensaje. */
function wrap<T>(parse: () => T, fallback: string): T {
  try {
    return parse()
  } catch (error) {
    throw new GameOrderRejectedError(error instanceof Error ? error.message : fallback)
  }
}

async function readJson(response: Response): Promise<unknown> {
  let value: unknown
  try {
    value = await response.json()
  } catch {
    throw httpError('No se pudo leer la respuesta del modo juego.', response.status)
  }
  if (!response.ok) {
    const detail = isRecord(value) && typeof value.detail === 'string' ? value.detail : 'La solicitud de juego fue rechazada.'
    throw httpError(detail, response.status)
  }
  return value
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
