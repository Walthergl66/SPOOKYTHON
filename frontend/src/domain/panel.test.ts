import { describe, expect, it } from 'vitest'
import { classifyCursor, nextPanelLog, parsePanelMap, parsePanelState, pickMap, type PanelLog } from './panel'

const mapa = {
  version: 'm1',
  nodos: [{ id: 'a', lat: 1, lng: 2 }, { id: 'b', lat: 3, lng: 4 }],
  calles: [{ id: 'c1', segmentoId: 's1', origen: 'a', destino: 'b', distanciaM: 10, tipo: 'calle', extra: 1 }],
  refugios: [{ id: 'r1', nodo: 'b' }],
}

const estadoActivo = {
  estado: 'activa', runId: 'run', modo: 'juego', turno: 3, fase: 'decision', decisionRestanteMs: 100,
  mapVersion: 'm1', snapshotVersion: 7,
  zombies: [{ id: 'z', tipo: 'caminante', nodo: 'a' }],
  movimientosZombies: [{ id: 'z', trayecto: ['a', 'b'] }],
  sobrevivientes: [{ id: 's', nodo: 'a', estado: 'activo', control: 'humano' }],
  rutasPrevistas: [{ sobrevivienteId: 's', trayecto: ['a', 'b'] }],
  aristasBloqueadas: ['c1'], segmentosBloqueados: ['s1'], nodosHorda: ['a'],
  eventosCiudad: [{ id: 'e', turno: 1, causa: 'x', segmentoId: 's1', lat: 0.25, lng: 0.75 }],
  metricas: { sobrevivientesActivos: 1, mordidos: 0, mordidosUltimoTurno: 0, evacuados: 0, zombiesVisibles: 1 },
}

describe('parsePanelMap', () => {
  it('acepta un mapa válido y descarta campos extra', () => {
    const r = parsePanelMap(mapa)
    expect(r.version).toBe('m1')
    expect(r.calles[0]).toEqual({ id: 'c1', segmentoId: 's1', origen: 'a', destino: 'b', distanciaM: 10, tipo: 'calle' })
    expect(r.refugios).toEqual([{ id: 'r1', nodo: 'b' }])
  })
  it('rechaza una calle con nodo desconocido', () => {
    const malo = { ...mapa, calles: [{ ...mapa.calles[0], destino: 'zz' }] }
    expect(() => parsePanelMap(malo)).toThrow('El servicio devolvió una calle con un formato no válido.')
  })
  it('rechaza un valor que no es mapa', () => {
    expect(() => parsePanelMap(null)).toThrow('El servicio devolvió un mapa con un formato no válido.')
  })
})

describe('parsePanelState', () => {
  it('acepta sin_partida', () => {
    expect(parsePanelState({ estado: 'sin_partida', otro: 1 })).toEqual({ estado: 'sin_partida' })
  })
  it('acepta un snapshot activo completo', () => {
    const r = parsePanelState(estadoActivo)
    expect(r).toEqual(estadoActivo)
  })
  it('conserva por separado el acumulado y las mordidas de la última resolución', () => {
    const r = parsePanelState({ ...estadoActivo, metricas: { ...estadoActivo.metricas, mordidos: 4, mordidosUltimoTurno: 2 } })
    expect(r.metricas?.mordidos).toBe(4)
    expect(r.metricas?.mordidosUltimoTurno).toBe(2)
  })
  it('no inventa un conteo por turno con un backend anterior', () => {
    const { mordidosUltimoTurno: _legacy, ...metricasAnteriores } = estadoActivo.metricas
    const r = parsePanelState({ ...estadoActivo, metricas: metricasAnteriores })
    expect(r.metricas?.mordidosUltimoTurno).toBeNull()
  })
  it('rechaza un estado desconocido', () => {
    expect(() => parsePanelState({ estado: 'x' })).toThrow('El servicio devolvió un estado del panel no válido.')
  })
  it('rechaza un snapshot activo incompleto', () => {
    expect(() => parsePanelState({ estado: 'activa' })).toThrow('El servicio devolvió un snapshot incompleto para el panel.')
  })
  it('rechaza un plazo de decisión negativo', () => {
    expect(() => parsePanelState({ ...estadoActivo, decisionRestanteMs: -1 }))
      .toThrow('El servicio devolvió el plazo de decisiones con un formato no válido.')
  })
  it('rechaza coordenadas de incidente parciales o fuera de rango numérico', () => {
    expect(() => parsePanelState({ ...estadoActivo, eventosCiudad: [{ id: 'e', turno: 1, causa: 'x', lat: 2 }] }))
      .toThrow('El servicio devolvió eventos de ciudad con un formato no válido.')
    expect(() => parsePanelState({ ...estadoActivo, eventosCiudad: [{ id: 'e', turno: 1, causa: 'x', segmentoId: 's1', lat: Number.NaN, lng: 0 }] }))
      .toThrow('El servicio devolvió eventos de ciudad con un formato no válido.')
  })
})

describe('classifyCursor', () => {
  const prev = { runId: 'r', sequence: 5 }
  it('clasifica stale, same y new', () => {
    expect(classifyCursor(prev, { runId: 'r', sequence: 4 })).toBe('stale')
    expect(classifyCursor(prev, { runId: 'r', sequence: 5 })).toBe('same')
    expect(classifyCursor(prev, { runId: 'r', sequence: 6 })).toBe('new')
  })
  it('es new sin cursor previo o con otro runId', () => {
    expect(classifyCursor(null, { runId: 'r', sequence: 0 })).toBe('new')
    expect(classifyCursor(prev, { runId: 'otro', sequence: 1 })).toBe('new')
    expect(classifyCursor({ runId: null, sequence: 0 }, { runId: null, sequence: 0 })).toBe('same')
  })
})

describe('pickMap', () => {
  const m = (version: string) => ({ version, nodos: [], calles: [], refugios: [] })
  it('prefiere el mapa nuevo, luego el cacheado, si coincide la versión', () => {
    expect(pickMap(m('v1'), m('v1'), 'v1')?.version).toBe('v1')
    const cached = m('v1')
    expect(pickMap(m('v2'), cached, 'v1')).toBe(cached)
    expect(pickMap(undefined, cached, 'v9')).toBeNull()
    expect(pickMap(null, null, undefined)).toBeNull()
  })
})

describe('nextPanelLog', () => {
  const activo = () => parsePanelState(estadoActivo)
  it('antepone incidente y turno, y deduplica por id', () => {
    const first = nextPanelLog([], activo())
    expect(first.map((l) => l.id)).toEqual(['run:e', 'run:7'])
    expect(first[0].label).toBe('Incidente vial · Turno 1')
    expect(nextPanelLog(first, activo())).toEqual(first)
  })
  it('limita a 5 entradas conservando las más recientes', () => {
    const viejo: PanelLog[] = Array.from({ length: 6 }, (_, i) => ({ id: `o${i}`, label: 'l', detail: 'd' }))
    const log = nextPanelLog(viejo, activo())
    expect(log).toHaveLength(5)
    expect(log.map((l) => l.id)).toEqual(['run:e', 'run:7', 'o0', 'o1', 'o2'])
  })
})
