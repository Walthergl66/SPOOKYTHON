export type SimulatorStatus = {
  habilitado: true
  estado: 'sin_partida' | 'activa' | 'pausada' | 'finalizada' | 'error'
  runId: string | null
  turno: number | null
  escenario: string | null
  sobrevivientesIniciales: number | null
  intensidad: 'baja' | 'media' | 'alta' | null
  eventosCiudad: boolean | null
  error: string | null
}

export type SimulatorSetup = {
  escenario: 'libre' | 'caminantes' | 'mixto' | 'horda'
  sobrevivientes: number
  intensidad: 'baja' | 'media' | 'alta'
  eventosCiudad: boolean
  semilla?: number
}

/** El backend no expone el control local de demo (HTTP 404). */
export class SimulatorUnavailableError extends Error {}

export type SimulatorAction = 'iniciar' | 'pausar' | 'reanudar' | 'reiniciar'

export function parseSimulatorStatus(value: unknown): SimulatorStatus {
  if (!isRecord(value) || value.habilitado !== true ||
    !['sin_partida', 'activa', 'pausada', 'finalizada', 'error'].includes(String(value.estado)) ||
    !(typeof value.runId === 'string' || value.runId === null) ||
    !(typeof value.turno === 'number' || value.turno === null) ||
    !(typeof value.escenario === 'string' || value.escenario === null) ||
    !(typeof value.sobrevivientesIniciales === 'number' || value.sobrevivientesIniciales === null) ||
    !(value.intensidad === 'baja' || value.intensidad === 'media' || value.intensidad === 'alta' || value.intensidad === null) ||
    !(typeof value.eventosCiudad === 'boolean' || value.eventosCiudad === null) ||
    !(typeof value.error === 'string' || value.error === null)) {
    throw new Error('El backend devolvió un estado de simulador incompleto.')
  }
  return {
    habilitado: true,
    estado: value.estado as SimulatorStatus['estado'],
    runId: value.runId,
    turno: value.turno,
    escenario: value.escenario,
    sobrevivientesIniciales: value.sobrevivientesIniciales,
    intensidad: value.intensidad,
    eventosCiudad: value.eventosCiudad,
    error: value.error,
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
