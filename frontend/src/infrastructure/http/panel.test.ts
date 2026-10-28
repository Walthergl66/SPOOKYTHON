import { afterEach, describe, expect, it, vi } from 'vitest'
import { loadPanelRoute } from './panel'

afterEach(() => vi.unstubAllGlobals())

describe('loadPanelRoute', () => {
  it('consulta y valida la ruta del habitante solicitado', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      runId: 'r1', turno: 4, snapshotVersion: 12, sobrevivienteId: 'S 1', trayecto: ['n1', 'n2'],
    }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    const route = await loadPanelRoute('S 1')

    expect(fetchMock).toHaveBeenCalledWith('/panel/ruta/S%201', expect.objectContaining({ headers: { Accept: 'application/json' } }))
    expect(route.trayecto).toEqual(['n1', 'n2'])
  })

  it('propaga el detalle HTTP cuando el habitante ya no está activo', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'El sobreviviente activo no existe.' }), { status: 404 })))

    await expect(loadPanelRoute('S-1')).rejects.toThrow('El sobreviviente activo no existe.')
  })
})
