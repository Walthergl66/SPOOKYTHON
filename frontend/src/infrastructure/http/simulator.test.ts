import { afterEach, describe, expect, it, vi } from 'vitest'
import { SimulatorUnavailableError } from '../../domain/simulator'
import { getSimulatorStatus, SimulatorApiError } from './simulator'

afterEach(() => vi.unstubAllGlobals())

const stub = (response: Response) => vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))

describe('getSimulatorStatus', () => {
  it('traduce 404 con JSON a SimulatorUnavailableError conservando detail', async () => {
    stub(new Response(JSON.stringify({ detail: 'deshabilitado' }), { status: 404 }))
    const error = await getSimulatorStatus().catch((e: unknown) => e)
    expect(error).toBeInstanceOf(SimulatorUnavailableError)
    expect((error as Error).message).toBe('deshabilitado')
  })

  it('traduce 404 con cuerpo inválido a SimulatorUnavailableError', async () => {
    stub(new Response('<html>', { status: 404 }))
    const error = await getSimulatorStatus().catch((e: unknown) => e)
    expect(error).toBeInstanceOf(SimulatorUnavailableError)
    expect((error as Error).message).toBe('El backend no devolvió una respuesta JSON válida.')
  })

  it('mantiene SimulatorApiError con status 500', async () => {
    stub(new Response(JSON.stringify({ detail: 'boom' }), { status: 500 }))
    const error = await getSimulatorStatus().catch((e: unknown) => e)
    expect(error).toBeInstanceOf(SimulatorApiError)
    expect(error).not.toBeInstanceOf(SimulatorUnavailableError)
    expect((error as SimulatorApiError).status).toBe(500)
  })
})
