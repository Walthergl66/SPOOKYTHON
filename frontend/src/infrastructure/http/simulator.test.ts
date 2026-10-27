import { afterEach, describe, expect, it, vi } from 'vitest'
import { SimulatorUnavailableError } from '../../domain/simulator'
import { controlSimulator, getSimulatorCandidates, getSimulatorStatus, SimulatorApiError } from './simulator'

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

describe('getSimulatorCandidates', () => {
  it('parsea candidatos válidos', async () => {
    stub(new Response(JSON.stringify({ version: 'v', nodos: [], calles: [], refugios: [] }), { status: 200 }))
    expect((await getSimulatorCandidates()).version).toBe('v')
  })
  it('traduce 404 a SimulatorUnavailableError', async () => {
    stub(new Response(JSON.stringify({ detail: 'off' }), { status: 404 }))
    expect(await getSimulatorCandidates().catch((e: unknown) => e)).toBeInstanceOf(SimulatorUnavailableError)
  })
  it('traduce 500 a SimulatorApiError con status', async () => {
    stub(new Response(JSON.stringify({ detail: 'boom' }), { status: 500 }))
    const error = await getSimulatorCandidates().catch((e: unknown) => e)
    expect(error).toBeInstanceOf(SimulatorApiError)
    expect((error as SimulatorApiError).status).toBe(500)
  })
})

describe('controlSimulator con refugios', () => {
  const setup = { escenario: 'mixto', sobrevivientes: 20, intensidad: 'media', eventosCiudad: true } as const
  const estado = { habilitado: true, estado: 'activa', runId: 'r', turno: 0, escenario: 'mixto', sobrevivientesIniciales: 20, intensidad: 'media', eventosCiudad: true, error: null }
  it('incluye refugios en el body solo si se pasan', async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(new Response(JSON.stringify(estado))))
    vi.stubGlobal('fetch', fetchMock)
    await controlSimulator('iniciar', setup, [{ id: 'R-01', nodo: 'N-1' }])
    await controlSimulator('iniciar', setup)
    expect(JSON.parse(fetchMock.mock.calls[0][1].body).refugios).toEqual([{ id: 'R-01', nodo: 'N-1' }])
    expect(JSON.parse(fetchMock.mock.calls[1][1].body).refugios).toBeUndefined()
  })
})
