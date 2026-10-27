import { describe, expect, it } from 'vitest'
import { parseSimulatorStatus } from './simulator'

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
