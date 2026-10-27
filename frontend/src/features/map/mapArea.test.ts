import { describe, expect, it } from 'vitest'
import { boundsOfNodes, gameBounds, mapAreaBounds, MANTA_AREA, paddedBounds } from './mapArea'
import type { PanelMap } from '../../domain/panel'

describe('cobertura cartográfica de Manta', () => {
  it('incluye San Mateo y San Lorenzo aunque el grafo cargado sea el recorte antiguo', () => {
    const area = mapAreaBounds({ nodos: [{ id: 'centro', lng: -80.72, lat: -0.95 }] })
    for (const [lng, lat] of [[-80.81, -0.963], [-80.904, -1.064], [-80.91, -1.13]]) {
      expect(lng).toBeGreaterThan(area[0][0])
      expect(lng).toBeLessThan(area[1][0])
      expect(lat).toBeGreaterThan(area[0][1])
      expect(lat).toBeLessThan(area[1][1])
    }
  })
  it('no recorta nodos de una nueva versión más extensa', () => {
    const area = mapAreaBounds({ nodos: [{ id: 'nuevo', lng: -80.94, lat: -1.16 }] })
    expect(area[0]).toEqual([-80.94, -1.16])
    expect(paddedBounds(area)[0][0]).toBeLessThan(area[0][0])
  })
  it('recorre grafos grandes sin expandir arrays como argumentos', () => {
    const nodes = Array.from({ length: 150_000 }, (_, i) => ({ lng: -80.92 + i / 1_000_000, lat: -1.14 }))
    expect(boundsOfNodes(nodes)).toEqual([[-80.92, -1.14], [nodes.at(-1)!.lng, -1.14]])
    expect(boundsOfNodes([])).toBeNull()
    expect(mapAreaBounds({ nodos: [] })).toEqual(MANTA_AREA)
  })
  it('encuadra personajes y refugios sin incluir cada nodo ni datos ocultos', () => {
    const map: PanelMap = {
      version: 'test', calles: [], refugios: [{ id: 'r', nodo: 'destino' }],
      nodos: [{ id: 'persona', lng: -80.72, lat: -0.95 }, { id: 'destino', lng: -80.73, lat: -0.96 }, { id: 'lejos', lng: -80.91, lat: -1.13 }],
    }
    expect(gameBounds(map, { estado: 'activa', sobrevivientes: [{ id: 's', nodo: 'persona', estado: 'activo', control: 'automatico' }] })).toEqual([[-80.73, -0.96], [-80.72, -0.95]])
  })
})
