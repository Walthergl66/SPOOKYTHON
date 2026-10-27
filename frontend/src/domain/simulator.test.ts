import { describe, expect, it } from 'vitest'
import { nodoMasCercano, refugiosParaEnviar, parseSimulatorCandidatos, parseSimulatorStatus } from './simulator'

const estado = {
  habilitado: true, estado: 'activa', runId: 'run', turno: 5, escenario: 'mixto',
  sobrevivientesIniciales: 10, intensidad: 'media', eventosCiudad: true, error: null,
}

describe('parseSimulatorStatus', () => {
  it('acepta un estado válido y descarta campos extra', () => {
    expect(parseSimulatorStatus({ ...estado, extra: 1 })).toEqual(estado)
  })
  it('acepta campos null', () => {
    const vacio = { ...estado, estado: 'sin_partida', runId: null, turno: null, escenario: null, sobrevivientesIniciales: null, intensidad: null, eventosCiudad: null }
    expect(parseSimulatorStatus(vacio)).toEqual(vacio)
  })
  it('rechaza un simulador no habilitado', () => {
    expect(() => parseSimulatorStatus({ ...estado, habilitado: false }))
      .toThrow('El backend devolvió un estado de simulador incompleto.')
  })
  it('rechaza una intensidad desconocida', () => {
    expect(() => parseSimulatorStatus({ ...estado, intensidad: 'extrema' }))
      .toThrow('El backend devolvió un estado de simulador incompleto.')
  })
})

describe('parseSimulatorCandidatos', () => {
  const valido = { version: 'v1', nodos: [{ id: 'N-1', lat: -0.95, lng: -80.72 }], calles: [{ origen: 'N-1', destino: 'N-2' }], refugios: [{ id: 'R-01', nodo: 'N-1' }] }
  it('acepta una forma válida', () => expect(parseSimulatorCandidatos(valido)).toEqual(valido))
  it('rechaza formas inválidas', () => {
    expect(() => parseSimulatorCandidatos(null)).toThrow()
    expect(() => parseSimulatorCandidatos({ ...valido, nodos: [{ id: 'N-1', lat: 'x', lng: 1 }] })).toThrow()
    expect(() => parseSimulatorCandidatos({ ...valido, calles: undefined })).toThrow()
  })
})

describe('nodoMasCercano', () => {
  const nodos = [{ id: 'A', lat: -0.95, lng: -80.72 }, { id: 'B', lat: -0.9505, lng: -80.72 }]
  it('elige el más cercano dentro del radio', () => expect(nodoMasCercano({ lat: -0.9504, lng: -80.72 }, nodos)?.id).toBe('B'))
  it('devuelve null fuera del radio', () => expect(nodoMasCercano({ lat: -0.96, lng: -80.72 }, nodos)).toBeNull())
  it('devuelve null con lista vacía', () => expect(nodoMasCercano({ lat: 0, lng: 0 }, [])).toBeNull())
})

describe('refugiosParaEnviar', () => {
  const ids = ['R-01', 'R-02']
  it('envía los refugios al iniciar y al reiniciar con todos colocados', () => {
    for (const accion of ['iniciar', 'reiniciar'] as const) {
      expect(refugiosParaEnviar(accion, ['N-1', 'N-2'], ids)).toEqual([{ id: 'R-01', nodo: 'N-1' }, { id: 'R-02', nodo: 'N-2' }])
    }
  })
  it('no envía nada si falta un slot o la acción es otra', () => {
    expect(refugiosParaEnviar('reiniciar', ['N-1', null], ids)).toBeUndefined()
    expect(refugiosParaEnviar('pausar', ['N-1', 'N-2'], ids)).toBeUndefined()
  })
})
