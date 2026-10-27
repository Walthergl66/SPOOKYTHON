import { describe, expect, it, vi } from 'vitest'
import type { PanelMap, PanelState } from './panel'
import { buildGameOrder, classifyGameError, createActionId, legalMoves, radioSuggestion, remainingMs, GameOrderRejectedError, GameSessionExpiredError, GameSessionMissingError, parseGameOrderReceipt, parsePlayerSession } from './game'

describe('parsePlayerSession', () => {
  it('traduce una sesión válida a nombres del producto', () => {
    const r = parsePlayerSession({
      runId: 'run', jugadorId: 'p1', estado: 'activo', nodo: 'a', estadoPersonaje: 'mordido',
      ultimaOrden: { accionId: 'x', turno: 2, siguienteNodo: 'b', secuencia: 1 },
    })
    expect(r).toEqual({
      runId: 'run', playerId: 'p1', status: 'activo', node: 'a', characterState: 'mordido',
      lastOrder: { actionId: 'x', turn: 2, destination: 'b', sequence: 1 },
    })
  })
  it('usa null por defecto en estadoPersonaje y ultimaOrden', () => {
    const r = parsePlayerSession({ runId: 'run', jugadorId: 'p1', estado: 'esperando_aparicion', nodo: null })
    expect(r.characterState).toBeNull()
    expect(r.lastOrder).toBeNull()
  })
  it('rechaza una sesión con estado inválido', () => {
    expect(() => parsePlayerSession({ runId: 'r', jugadorId: 'p', estado: 'z', nodo: null }))
      .toThrow('El servicio devolvió una sesión con formato no válido.')
  })
  it('rechaza un estado de personaje inválido', () => {
    expect(() => parsePlayerSession({ runId: 'r', jugadorId: 'p', estado: 'activo', nodo: 'a', estadoPersonaje: 'x' }))
      .toThrow('El servicio devolvió el estado del personaje con un formato no válido.')
  })
  it('rechaza una última orden con secuencia menor a 1', () => {
    const ultimaOrden = { accionId: 'x', turno: 2, siguienteNodo: 'b', secuencia: 0 }
    expect(() => parsePlayerSession({ runId: 'r', jugadorId: 'p', estado: 'activo', nodo: 'a', ultimaOrden }))
      .toThrow('El servicio devolvió la última orden con un formato no válido.')
  })
})

describe('parseGameOrderReceipt', () => {
  it('acepta un acuse válido', () => {
    expect(parseGameOrderReceipt({ accionId: 'x', secuencia: 1, estado: 'recibida', turno: 4, extra: 1 }))
      .toEqual({ accionId: 'x', secuencia: 1, estado: 'recibida', turno: 4 })
  })
  it('rechaza un acuse con estado distinto de recibida', () => {
    expect(() => parseGameOrderReceipt({ accionId: 'x', secuencia: 1, estado: 'aplicada', turno: 4 }))
      .toThrow('El servicio devolvió un acuse con formato no válido.')
  })
})

describe('classifyGameError', () => {
  it('clasifica los errores de dominio y trata el resto como transitorio', () => {
    expect(classifyGameError(new GameSessionMissingError('x'))).toBe('missing')
    expect(classifyGameError(new GameSessionExpiredError('x'))).toBe('expired')
    expect(classifyGameError(new GameOrderRejectedError('x'))).toBe('rejected')
    expect(classifyGameError(new TypeError('red'))).toBe('transient')
  })
})

const street = (id: string, origen: string, destino: string, segmentoId = `s-${id}`) => ({ id, segmentoId, origen, destino, distanciaM: 10, tipo: 'calle' })
const map: PanelMap = {
  version: 'v', nodos: [], refugios: [],
  calles: [street('e1', 'A', 'B'), street('e2', 'A', 'C'), street('e3', 'A', 'D'), street('e4', 'A', 'E', 'seg-x'), street('e5', 'A', 'F'), street('e6', 'A', 'B'), street('e7', 'Z', 'B')],
}
const player = { id: 'p1', nodo: 'A', estado: 'activo', control: 'humano' }
const base: PanelState = { estado: 'activa', modo: 'juego', runId: 'r1', turno: 3, fase: 'decisiones' }

describe('legalMoves', () => {
  it('excluye aristas, segmentos y nodos de horda cerrados, deduplica y marca riesgo', () => {
    const state: PanelState = { ...base, aristasBloqueadas: ['e2'], segmentosBloqueados: ['seg-x'], nodosHorda: ['F'], zombies: [{ id: 'z', tipo: 'a', nodo: 'D' }] }
    const moves = legalMoves(state, map, player)
    expect(moves.map(({ node, risk }) => [node, risk])).toEqual([['B', false], ['D', true]])
    expect(moves[0].street.id).toBe('e1')
  })
  it('devuelve lista vacía sin salidas', () => {
    expect(legalMoves(base, map, { ...player, nodo: 'Q' })).toEqual([])
  })
})

describe('radioSuggestion', () => {
  const choices = legalMoves(base, map, player)
  const withRoute = (trayecto: string[], extra: Partial<PanelState> = {}): PanelState => ({ ...base, rutasPrevistas: [{ sobrevivienteId: 'p1', trayecto }], ...extra })
  it('sugiere el siguiente nodo si es legal', () => {
    expect(radioSuggestion(withRoute(['A', 'B', 'C']), player, choices)?.nextNode).toBe('B')
  })
  it('es null fuera de decisiones, con ruta ajena, corta o con siguiente ilegal', () => {
    expect(radioSuggestion(withRoute(['A', 'B'], { fase: 'resolucion' }), player, choices)).toBeNull()
    expect(radioSuggestion(withRoute(['X', 'B']), player, choices)).toBeNull()
    expect(radioSuggestion(withRoute(['A']), player, choices)).toBeNull()
    expect(radioSuggestion(withRoute(['A', 'Q']), player, choices)).toBeNull()
  })
})

describe('buildGameOrder', () => {
  it('arma la orden y devuelve null sin runId o turno', () => {
    expect(buildGameOrder(base, 'p1', 'B', 'a1')).toEqual({ runId: 'r1', turno: 3, personajeId: 'p1', siguienteNodo: 'B', accionId: 'a1' })
    expect(buildGameOrder({ ...base, runId: undefined }, 'p1', 'B', 'a1')).toBeNull()
    expect(buildGameOrder({ ...base, turno: undefined }, 'p1', 'B', 'a1')).toBeNull()
  })
})

describe('remainingMs', () => {
  it('redondea hacia arriba y nunca es negativo', () => {
    expect(remainingMs(1000.2, 1000)).toBe(1)
    expect(remainingMs(1000, 1500)).toBe(0)
  })
})

describe('createActionId', () => {
  it('usa randomUUID si existe', () => {
    expect(createActionId({ randomUUID: () => 'uuid', getRandomValues: vi.fn() } as unknown as Crypto)).toBe('uuid')
  })
  it('respalda con 32 hex', () => {
    const fake = { getRandomValues: (b: Uint8Array) => { b.fill(10); return b } } as unknown as Crypto
    expect(createActionId(fake)).toBe('0a'.repeat(16))
  })
})
