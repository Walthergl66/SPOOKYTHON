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

export class SimulatorApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
    this.name = 'SimulatorApiError'
  }
}

export async function getSimulatorStatus(signal?: AbortSignal): Promise<SimulatorStatus> {
  const response = await fetch('/demo/simulador', { headers: { Accept: 'application/json' }, signal })
  return parseStatus(await readJson(response), response.status)
}

export async function controlSimulator(action: 'iniciar' | 'pausar' | 'reanudar' | 'reiniciar', setup?: SimulatorSetup): Promise<SimulatorStatus> {
  const response = await fetch(`/demo/simulador/${action}`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: action === 'iniciar' || action === 'reiniciar' ? JSON.stringify(setup) : undefined,
  })
  return parseStatus(await readJson(response), response.status)
}

async function readJson(response: Response): Promise<unknown> {
  let value: unknown
  try { value = await response.json() } catch {
    throw new SimulatorApiError('El backend no devolvió una respuesta JSON válida.', response.status)
  }
  if (!response.ok) {
    const detail = isRecord(value) && typeof value.detail === 'string' ? value.detail : 'No se pudo controlar el simulador.'
    throw new SimulatorApiError(detail, response.status)
  }
  return value
}

function parseStatus(value: unknown, status: number): SimulatorStatus {
  if (!isRecord(value) || value.habilitado !== true ||
    !['sin_partida', 'activa', 'pausada', 'finalizada', 'error'].includes(String(value.estado)) ||
    !(typeof value.runId === 'string' || value.runId === null) ||
    !(typeof value.turno === 'number' || value.turno === null) ||
    !(typeof value.escenario === 'string' || value.escenario === null) ||
    !(typeof value.sobrevivientesIniciales === 'number' || value.sobrevivientesIniciales === null) ||
    !(value.intensidad === 'baja' || value.intensidad === 'media' || value.intensidad === 'alta' || value.intensidad === null) ||
    !(typeof value.eventosCiudad === 'boolean' || value.eventosCiudad === null) ||
    !(typeof value.error === 'string' || value.error === null)) {
    throw new SimulatorApiError('El backend devolvió un estado de simulador incompleto.', status)
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
