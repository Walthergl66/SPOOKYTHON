import { describe, expect, it } from 'vitest'
import type { PanelMap, PanelState } from '../../domain/panel'
import { getSurvivorRouteDetails } from './survivorRoute'

const map: PanelMap = {
  version: 'm1',
  nodos: [{ id: 'a', lat: 0, lng: 0 }, { id: 'b', lat: 0, lng: 1 }, { id: 'c', lat: 1, lng: 1 }],
  calles: [],
  refugios: [{ id: 'R-01', nodo: 'c' }],
}
const state: PanelState = {
  estado: 'activa',
  sobrevivientes: [
    { id: 'S-01', nodo: 'a', estado: 'activo', control: 'automatico' },
    { id: 'S-02', nodo: 'b', estado: 'mordido', control: 'humano' },
  ],
  rutasPrevistas: [{ sobrevivienteId: 'S-01', trayecto: ['a', 'b', 'c'] }],
}

describe('getSurvivorRouteDetails', () => {
  it('resuelve posición, siguiente paso y refugio de la ruta vigente del seleccionado', () => {
    expect(getSurvivorRouteDetails(state, map, 'S-01')).toEqual({
      survivor: state.sobrevivientes?.[0], path: ['a', 'b', 'c'], nextNode: 'b', destination: 'R-01',
    })
  })

  it('no asigna una ruta a un sobreviviente terminal ni filtra otro habitante', () => {
    expect(getSurvivorRouteDetails(state, map, 'S-02')).toMatchObject({
      survivor: state.sobrevivientes?.[1], path: [], nextNode: null, destination: null,
    })
    expect(getSurvivorRouteDetails(state, map, 'unknown')).toBeNull()
  })
})
