import { describe, expect, it } from 'vitest'
import type { PanelMap, PanelState } from '../../domain/panel'
import { createActorFeatures, createMovementAnimations, createSimulationFeatures, createStreetFeatures, mergeActiveMovements, movementDurationMs, positionAlongPath } from './mapFeatures'

describe('movementDurationMs', () => {
  it('acompaña el ritmo seleccionado sin saltarse turnos', () => {
    expect(movementDurationMs(1)).toBe(2000)
    expect(movementDurationMs(2)).toBe(1000)
    expect(movementDurationMs(4)).toBe(500)
    expect(movementDurationMs(4, 1200)).toBe(1200)
    expect(movementDurationMs(4, 300)).toBe(500)
  })
})

describe('mergeActiveMovements', () => {
  const move = { id: 'z', path: [[0, 0], [1, 0]] as [number, number][], startedAt: 100 }

  it('conserva un trayecto confirmado si el snapshot siguiente no trae otro movimiento', () => {
    expect(mergeActiveMovements(new Map([['z', move]]), [], new Set(['z']))).toEqual(new Map([['z', move]]))
  })

  it('retira actores que dejaron de estar visibles y sustituye por su trayecto confirmado nuevo', () => {
    const next = { ...move, startedAt: 200 }
    expect(mergeActiveMovements(new Map([['z', move], ['gone', move]]), [next], new Set(['z']))).toEqual(new Map([['z', next]]))
  })
})

const map: PanelMap = {
  version: 'm1',
  nodos: [
    { id: 'a', lat: 0, lng: 0 },
    { id: 'b', lat: 0, lng: 1 },
    { id: 'c', lat: 1, lng: 1 },
  ],
  calles: [
    { id: 'a-b', segmentoId: 's1', origen: 'a', destino: 'b', distanciaM: 10, tipo: 'x' },
    { id: 'b-a', segmentoId: 's1', origen: 'b', destino: 'a', distanciaM: 10, tipo: 'x' },
  ],
  refugios: [{ id: 'r1', nodo: 'c' }],
}

const state = (extra: Partial<PanelState> = {}): PanelState => ({ estado: 'activa', runId: 'r', snapshotVersion: 1, ...extra })
const kinds = (s: PanelState, sel?: string) => createSimulationFeatures(map, s, sel).features.map((f) => f.properties.kind)

describe('positionAlongPath', () => {
  const path: [number, number][] = [[0, 0], [2, 0], [2, 4]]
  it('devuelve inicio, centro y final exacto', () => {
    expect(positionAlongPath(path, 0)).toEqual([0, 0])
    expect(positionAlongPath(path, 0.5)).toEqual([2, 0])
    expect(positionAlongPath(path, 1)).toEqual([2, 4])
  })
  it('recorta fuera de rango', () => {
    expect(positionAlongPath(path, -3)).toEqual([0, 0])
    expect(positionAlongPath(path, 7)).toEqual([2, 4])
  })
})

describe('createMovementAnimations', () => {
  const prev = state({
    sobrevivientes: [{ id: 's', nodo: 'a', estado: 'activo', control: 'x' }, { id: 'o', nodo: 'a', estado: 'mordido', control: 'x' }],
    zombies: [{ id: 'z', tipo: 'zombie', nodo: 'a' }],
  })
  const cur = state({
    snapshotVersion: 2,
    sobrevivientes: [{ id: 's', nodo: 'b', estado: 'activo', control: 'x' }, { id: 'o', nodo: 'b', estado: 'mordido', control: 'x' }],
    zombies: [{ id: 'z', tipo: 'zombie', nodo: 'c' }],
    movimientosZombies: [{ id: 'z', trayecto: ['a', 'b', 'c'] }],
  })
  it('devuelve [] si cambia runId o se repite la versión', () => {
    expect(createMovementAnimations(map, prev, { ...cur, runId: 'otro' }, 0)).toEqual([])
    expect(createMovementAnimations(map, prev, { ...cur, snapshotVersion: 1 }, 0)).toEqual([])
  })
  it('anima activos, omite no activos y usa el trayecto del zombie', () => {
    const result = createMovementAnimations(map, prev, cur, 5)
    expect(result.map((m) => m.id)).toEqual(['s', 'z'])
    expect(result[0].path).toEqual([[0, 0], [1, 0]])
    expect(result[1].path).toHaveLength(3)
    expect(result[1].startedAt).toBe(5)
  })
  it('descarta el zombie si el trayecto no termina en su nodo', () => {
    const bad = { ...cur, movimientosZombies: [{ id: 'z', trayecto: ['a', 'b'] }] }
    expect(createMovementAnimations(map, prev, bad, 0).map((m) => m.id)).toEqual(['s'])
  })
})

describe('createSimulationFeatures', () => {
  const streets = () => createStreetFeatures(map).features
  it('indexa cada calle inmutable una vez y separa cierres por turno', () => {
    expect(streets()).toHaveLength(1)
    for (const s of [state({ segmentosBloqueados: ['s1'] }), state({ aristasBloqueadas: ['b-a'] })]) {
      const blocked = createSimulationFeatures(map, s, undefined).features.filter((feature) => feature.properties.kind === 'blocked-street')
      expect(blocked).toHaveLength(1)
    }
    expect(createSimulationFeatures(map, state(), undefined).features.some((feature) => feature.properties.kind === 'blocked-street')).toBe(false)
  })
  it('solo incluye la ruta del seleccionado', () => {
    const s = state({ rutasPrevistas: [{ sobrevivienteId: 's', trayecto: ['a', 'b'] }] })
    expect(kinds(s, 's')).toContain('route')
    expect(kinds(s, 'x')).not.toContain('route')
  })
  it('proyecta cada incidente aplicado como punto geográfico amarillo identificable', () => {
    const features = createSimulationFeatures(map, state({
      eventosCiudad: [{ id: 'event-1', turno: 2, causa: 'Incidente vial simulado', segmentoId: 's1', lat: 0.4, lng: 0.6 }],
    }), undefined).features
    const incident = features.find((feature) => feature.properties.kind === 'road-incident')
    expect(incident?.id).toBe('incident-event-1')
    expect(incident?.geometry).toEqual({ type: 'Point', coordinates: [0.6, 0.4] })
    expect(incident?.properties.glyph).toBe('!')
  })
  it('filtra nodos desconocidos', () => {
    const s = state({ rutasPrevistas: [{ sobrevivienteId: 's', trayecto: ['a', 'zz'] }] as never })
    expect(kinds(s, 's')).not.toContain('route')
    expect(kinds(s, 's')).toContain('refuge')
  })
})

describe('createActorFeatures', () => {
  const s = state({
    sobrevivientes: [{ id: 's', nodo: 'a', estado: 'activo', control: 'x' }, { id: 'o', nodo: 'a', estado: 'mordido', control: 'x' }],
    zombies: [{ id: 'h', tipo: 'horda', nodo: 'b' }],
  })
  it('overrides tiene prioridad, horda es H y omite no activos', () => {
    const { features } = createActorFeatures(map, s, new Map([['s', [9, 9]]]))
    expect(features.map((f) => f.id)).toEqual(['s', 'h'])
    expect(features[0].geometry).toEqual({ type: 'Point', coordinates: [9, 9] })
    expect(features[1].properties).toEqual({ kind: 'horde', glyph: 'H' })
  })
})
