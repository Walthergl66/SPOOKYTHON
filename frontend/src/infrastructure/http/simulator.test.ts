import { afterEach, describe, expect, it, vi } from 'vitest'
import { SimulatorUnavailableError } from '../../domain/simulator'
import { controlSimulator, getSimulatorCandidates, getSimulatorStatus, SimulatorApiError, restartChallengeRound, startChallengeRound } from './simulator'

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
    stub(new Response(JSON.stringify({ version: 'v', limitesJugables: [[-80.807, -1.082], [-80.621, -0.897]], nodos: [], calles: [], refugios: [] }), { status: 200 }))
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
  const setup = { escenario: 'mixto', sobrevivientes: 20, zombies: 37, intensidad: 'media' } as const
  const estado = { habilitado: true, estado: 'activa', runId: 'r', turno: 0, escenario: 'mixto', sobrevivientesIniciales: 20, zombiesIniciales: 37, intensidad: 'media', eventosCiudad: true, velocidad: 1, error: null }
  it('envía refugios opcionales y no expone configuración para desactivar incidentes', async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(new Response(JSON.stringify(estado))))
    vi.stubGlobal('fetch', fetchMock)
    await controlSimulator('iniciar', setup, [{ id: 'R-01', nodo: 'N-1' }])
    await controlSimulator('iniciar', setup)
    expect(JSON.parse(fetchMock.mock.calls[0][1].body).refugios).toEqual([{ id: 'R-01', nodo: 'N-1' }])
    expect(JSON.parse(fetchMock.mock.calls[0][1].body).zombies).toBe(37)
    expect(JSON.parse(fetchMock.mock.calls[1][1].body).refugios).toBeUndefined()
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).not.toHaveProperty('eventosCiudad')
  })

  it('dirige pausa y continuación a los controles compartidos del run actual', async () => {
    const estado = { habilitado: true, estado: 'pausada', runId: 'reto-r2', turno: 12, escenario: 'reto_medianoche', sobrevivientesIniciales: 80, intensidad: 'media', eventosCiudad: false, velocidad: 1, error: null, rondaReto: 2 }
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(new Response(JSON.stringify(estado))))
    vi.stubGlobal('fetch', fetchMock)
    await controlSimulator('pausar')
    await controlSimulator('reanudar')
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/demo/simulador/pausar', expect.objectContaining({ method: 'POST', body: undefined }))
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/demo/simulador/reanudar', expect.objectContaining({ method: 'POST', body: undefined }))
  })
})

describe('startChallengeRound', () => {
  it('llama al endpoint separado con la ronda seleccionada', async () => {
    const estado = { habilitado: true, estado: 'activa', runId: 'r', turno: 0, escenario: 'reto_medianoche', sobrevivientesIniciales: 80, intensidad: 'media', eventosCiudad: false, velocidad: 1, error: null, rondaReto: 2 }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(estado)))
    vi.stubGlobal('fetch', fetchMock)
    const response = await startChallengeRound(2)
    expect(response.rondaReto).toBe(2)
    expect(fetchMock).toHaveBeenCalledWith('/reto/iniciar', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ ronda: 2 }),
    }))
  })
})

describe('restartChallengeRound', () => {
  it('reinicia el reto actual mediante el endpoint protegido', async () => {
    const estado = { habilitado: true, estado: 'activa', runId: 'nuevo', turno: 0, escenario: 'reto_medianoche', sobrevivientesIniciales: 80, intensidad: 'media', eventosCiudad: false, velocidad: 1, error: null, rondaReto: 2 }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(estado)))
    vi.stubGlobal('fetch', fetchMock)
    expect((await restartChallengeRound()).rondaReto).toBe(2)
    expect(fetchMock).toHaveBeenCalledWith('/reto/reiniciar', expect.objectContaining({ method: 'POST' }))
  })
})
