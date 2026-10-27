import { parseSimulatorCandidatos, parseSimulatorStatus, SimulatorUnavailableError, type RefugioAsignado, type SimulatorAction, type SimulatorCandidatos, type SimulatorSetup, type SimulatorStatus } from '../../domain/simulator'

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

export async function getSimulatorCandidates(signal?: AbortSignal): Promise<SimulatorCandidatos> {
  const response = await fetch('/demo/simulador/candidatos', { headers: { Accept: 'application/json' }, signal })
  const value = await readJson(response)
  try {
    return parseSimulatorCandidatos(value)
  } catch (error) {
    throw new SimulatorApiError(error instanceof Error ? error.message : 'Candidatos incompletos.', response.status)
  }
}

export async function controlSimulator(action: SimulatorAction, setup?: SimulatorSetup, refugios?: RefugioAsignado[]): Promise<SimulatorStatus> {
  const response = await fetch(`/demo/simulador/${action}`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: action === 'iniciar' || action === 'reiniciar' ? JSON.stringify(refugios ? { ...setup, refugios } : setup) : undefined,
  })
  return parseStatus(await readJson(response), response.status)
}

/** El dominio lanza Error; aquí se conserva el mensaje y se añade el status HTTP. */
function parseStatus(value: unknown, status: number): SimulatorStatus {
  try {
    return parseSimulatorStatus(value)
  } catch (error) {
    throw new SimulatorApiError(error instanceof Error ? error.message : 'El backend devolvió un estado de simulador incompleto.', status)
  }
}

function httpError(message: string, status: number): Error {
  return status === 404 ? new SimulatorUnavailableError(message) : new SimulatorApiError(message, status)
}

async function readJson(response: Response): Promise<unknown> {
  let value: unknown
  try { value = await response.json() } catch {
    throw httpError('El backend no devolvió una respuesta JSON válida.', response.status)
  }
  if (!response.ok) {
    const detail = isRecord(value) && typeof value.detail === 'string' ? value.detail : 'No se pudo controlar el simulador.'
    throw httpError(detail, response.status)
  }
  return value
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
