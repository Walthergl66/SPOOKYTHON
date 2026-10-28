import { afterEach, describe, expect, it, vi } from 'vitest'
import { startOperatorWorld } from './operator'

afterEach(() => vi.unstubAllGlobals())

describe('startOperatorWorld', () => {
  it('inicia un mundo operador vacío por su endpoint dedicado', async () => {
    const status = {
      habilitado: true,
      estado: 'activa',
      runId: 'navira-empty-world',
      turno: 0,
      escenario: 'demo-sintetico-mixto',
      sobrevivientesIniciales: 0,
      zombiesIniciales: 0,
      intensidad: 'media',
      eventosCiudad: false,
      velocidad: 4,
      error: null,
    }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(status), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(startOperatorWorld()).resolves.toMatchObject({
      estado: 'activa',
      sobrevivientesIniciales: 0,
      zombiesIniciales: 0,
      eventosCiudad: false,
    })
    expect(fetchMock).toHaveBeenCalledWith('/demo/operador/iniciar', {
      method: 'POST',
      headers: { Accept: 'application/json' },
    })
  })
})
