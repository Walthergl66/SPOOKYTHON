import type { PanelMap, PanelState } from './panel'

export interface PlayerSession {
  runId: string
  playerId: string
  status: 'esperando_aparicion' | 'activo'
  node: string | null
  characterState: 'activo' | 'mordido' | 'evacuado' | null
  lastOrder: { actionId: string; turn: number; destination: string; sequence: number } | null
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

/** Sin sesión de jugador propietaria (HTTP 403). */
export class GameSessionMissingError extends Error {}
/** La sesión venció por inactividad (HTTP 410). */
export class GameSessionExpiredError extends Error {}
/** El servidor rechazó la solicitud (otro 4xx) o devolvió un cuerpo 2xx no válido. */
export class GameOrderRejectedError extends Error {}

export type GameErrorKind = 'missing' | 'expired' | 'rejected' | 'transient'

/** Todo lo que no es error de dominio (red, 5xx) es transitorio y reintentable. */
export function classifyGameError(error: unknown): GameErrorKind {
  if (error instanceof GameSessionMissingError) return 'missing'
  if (error instanceof GameSessionExpiredError) return 'expired'
  if (error instanceof GameOrderRejectedError) return 'rejected'
  return 'transient'
}

export function parseGameOrderReceipt(value: unknown): GameOrderReceipt {
  if (!isRecord(value) || typeof value.accionId !== 'string' || typeof value.secuencia !== 'number' ||
    value.estado !== 'recibida' || typeof value.turno !== 'number') {
    throw new Error('El servicio devolvió un acuse con formato no válido.')
  }
  return { accionId: value.accionId, secuencia: value.secuencia, estado: 'recibida', turno: value.turno }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function parsePlayerSession(value: unknown): PlayerSession {
  if (!isRecord(value) || typeof value.runId !== 'string' || typeof value.jugadorId !== 'string' ||
    (value.estado !== 'esperando_aparicion' && value.estado !== 'activo') ||
    !(typeof value.nodo === 'string' || value.nodo === null)) {
    throw new Error('El servicio devolvió una sesión con formato no válido.')
  }
  const characterState = value.estadoPersonaje
  if (!(characterState === undefined || characterState === null || characterState === 'activo' || characterState === 'mordido' || characterState === 'evacuado')) {
    throw new Error('El servicio devolvió el estado del personaje con un formato no válido.')
  }
  const last = value.ultimaOrden
  let lastOrder: PlayerSession['lastOrder'] = null
  if (last !== undefined && last !== null) {
    if (!isRecord(last) || typeof last.accionId !== 'string' || !Number.isInteger(last.turno) ||
      typeof last.siguienteNodo !== 'string' || !Number.isInteger(last.secuencia) || (last.secuencia as number) < 1) {
      throw new Error('El servicio devolvió la última orden con un formato no válido.')
    }
    lastOrder = {
      actionId: last.accionId,
      turn: last.turno as number,
      destination: last.siguienteNodo,
      sequence: last.secuencia as number,
    }
  }
  return {
    runId: value.runId,
    playerId: value.jugadorId,
    status: value.estado,
    node: value.nodo,
    characterState: characterState === undefined ? null : characterState,
    lastOrder,
  }
}

export type GamePlayer = NonNullable<PanelState['sobrevivientes']>[number]
export type GameMove = { node: string; street: PanelMap['calles'][number]; risk: boolean }

/** Solo una partida activa en modo juego habilita los controles humanos. */
export function activeGameState(state: PanelState | null): PanelState | null {
  return state?.estado === 'activa' && state.modo === 'juego' ? state : null
}

/** El personaje solo existe para la sesión si pertenece a la misma partida. */
export function findPlayer(state: PanelState | null, session: PlayerSession | null): GamePlayer | undefined {
  return state && session && session.runId === state.runId
    ? state.sobrevivientes?.find(({ id }) => id === session.playerId)
    : undefined
}

/** Calles abiertas desde el nodo del jugador, una por destino; `risk` marca zombie visible en el destino. */
export function legalMoves(state: PanelState | null, map: PanelMap | null, player: GamePlayer | undefined): GameMove[] {
  if (!state || !map || !player) return []
  const closedEdges = new Set(state.aristasBloqueadas ?? [])
  const closedSegments = new Set(state.segmentosBloqueados ?? [])
  const blockedNodes = new Set(state.nodosHorda ?? [])
  const zombieNodes = new Set((state.zombies ?? []).map(({ nodo }) => nodo))
  const byNode = new Map<string, PanelMap['calles'][number]>()
  for (const street of map.calles) {
    if (street.origen !== player.nodo || closedEdges.has(street.id) || closedSegments.has(street.segmentoId)) continue
    if (blockedNodes.has(street.destino) || byNode.has(street.destino)) continue
    byNode.set(street.destino, street)
  }
  return [...byNode.entries()].map(([node, street]) => ({ node, street, risk: zombieNodes.has(node) }))
}

/** Primer paso de la ruta prevista del servidor, solo si es una jugada legal en la fase de decisiones. */
export function radioSuggestion(state: PanelState | null, player: GamePlayer | undefined, choices: GameMove[]): { nextNode: string; move: GameMove } | null {
  if (!state || !player || state.fase !== 'decisiones') return null
  const route = state.rutasPrevistas?.find(({ sobrevivienteId }) => sobrevivienteId === player.id)?.trayecto
  if (!route || route[0] !== player.nodo || route.length < 2) return null
  const nextNode = route[1]
  const move = choices.find(({ node }) => node === nextNode)
  return move ? { nextNode, move } : null
}

export function buildGameOrder(state: PanelState, playerId: string, destination: string, actionId: string): GameOrderInput | null {
  if (!state.runId || state.turno === undefined) return null
  return { runId: state.runId, turno: state.turno, personajeId: playerId, siguienteNodo: destination, accionId: actionId }
}

/** Milisegundos locales hasta el cierre; nunca negativos. */
export function remainingMs(deadline: number, now: number): number {
  return Math.max(0, Math.ceil(deadline - now))
}

export function createActionId(c: Pick<Crypto, 'randomUUID' | 'getRandomValues'> = crypto): string {
  if (typeof c.randomUUID === 'function') return c.randomUUID()
  const bytes = new Uint8Array(16)
  c.getRandomValues(bytes)
  return [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}
