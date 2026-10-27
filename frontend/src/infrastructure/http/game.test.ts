import { afterEach, describe, expect, it, vi } from 'vitest'
import type { GameOrderInput } from '../../domain/game'
import { GameOrderRejectedError, GameSessionExpiredError, GameSessionMissingError } from '../../domain/game'
import { GameApiError, joinGame, restoreGameSession, sendGameOrder } from './game'

afterEach(() => vi.unstubAllGlobals())

const stub = (response: Response) => vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
const failure = (status: number, detail = 'detalle') => {
  stub(new Response(JSON.stringify({ detail }), { status }))
  return joinGame().catch((e: unknown) => e)
}

describe('traducción HTTP del modo juego', () => {
  it('403 -> GameSessionMissingError conservando detail', async () => {
    const error = await failure(403)
    expect(error).toBeInstanceOf(GameSessionMissingError)
    expect((error as Error).message).toBe('detalle')
  })
  it('410 -> GameSessionExpiredError', async () => {
    expect(await failure(410)).toBeInstanceOf(GameSessionExpiredError)
  })
  it('422 -> GameOrderRejectedError', async () => {
    expect(await failure(422)).toBeInstanceOf(GameOrderRejectedError)
  })
  it('502 -> GameApiError con status', async () => {
    const error = await failure(502)
    expect(error).toBeInstanceOf(GameApiError)
    expect((error as GameApiError).status).toBe(502)
  })
  it('JSON 2xx inválido -> GameOrderRejectedError; 502 inválido -> GameApiError', async () => {
    stub(new Response('<html>', { status: 200 }))
    expect(await joinGame().catch((e: unknown) => e)).toBeInstanceOf(GameOrderRejectedError)
    stub(new Response('<html>', { status: 502 }))
    expect(await joinGame().catch((e: unknown) => e)).toBeInstanceOf(GameApiError)
  })
})

const json = (body: unknown, status: number) => stub(new Response(JSON.stringify(body), { status }))
const order = { runId: 'r1', turno: 1, jugadorId: 'p1', siguienteNodo: 'n2', accionId: 'a1' } as unknown as GameOrderInput
const receipt = { accionId: 'a1', secuencia: 1, estado: 'recibida', turno: 1 }
const sessionBody = { runId: 'r1', jugadorId: 'p1', estado: 'activo', nodo: 'n1' }
const caught = (call: () => Promise<unknown>) => call().catch((e: unknown) => e)

describe('sendGameOrder', () => {
  it('200 válido devuelve el recibo', async () => {
    json(receipt, 200)
    expect(await sendGameOrder(order)).toEqual(receipt)
  })
  it.each([
    [403, GameSessionMissingError],
    [410, GameSessionExpiredError],
    [422, GameOrderRejectedError],
    [502, GameApiError],
  ])('%i -> error esperado', async (status, Type) => {
    json({ detail: 'x' }, status)
    expect(await caught(() => sendGameOrder(order))).toBeInstanceOf(Type)
  })
  it('recibo inválido con 200 -> GameOrderRejectedError', async () => {
    json({ foo: 1 }, 200)
    expect(await caught(() => sendGameOrder(order))).toBeInstanceOf(GameOrderRejectedError)
  })
})

describe('restoreGameSession', () => {
  it('200 válido devuelve la sesión', async () => {
    json(sessionBody, 200)
    expect(await restoreGameSession()).toMatchObject({ runId: 'r1', playerId: 'p1' })
  })
  it.each([[403, GameSessionMissingError], [410, GameSessionExpiredError]])('%i -> error esperado', async (status, Type) => {
    json({ detail: 'x' }, status)
    expect(await caught(() => restoreGameSession())).toBeInstanceOf(Type)
  })
})
