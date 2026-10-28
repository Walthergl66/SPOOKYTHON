import type { OperatorPlacement } from '../../domain/operator'
import { parseSimulatorStatus, SimulatorUnavailableError, type SimulatorStatus } from '../../domain/simulator'
import { SimulatorApiError } from './simulator'

export async function startOperatorWorld(): Promise<SimulatorStatus> {
  const response = await fetch('/demo/operador/iniciar', {
    method: 'POST',
    headers: { Accept: 'application/json' },
  })
  let value: unknown
  try { value = await response.json() } catch {
    if (response.status === 404) throw new SimulatorUnavailableError('El backend no ofrece el inicio de mundo vacío.')
    throw new SimulatorApiError('El servidor no devolvió una respuesta válida.', response.status)
  }
  if (!response.ok) {
    const detail = typeof value === 'object' && value !== null && 'detail' in value && typeof value.detail === 'string' ? value.detail : 'No se pudo iniciar un mundo vacío.'
    if (response.status === 404) throw new SimulatorUnavailableError(detail)
    throw new SimulatorApiError(detail, response.status)
  }
  try { return parseSimulatorStatus(value) } catch (error) {
    throw new SimulatorApiError(error instanceof Error ? error.message : 'El servidor devolvió un estado incompleto.', response.status)
  }
}

export async function placeOperatorElement(element: OperatorPlacement): Promise<string> {
  const response = await fetch('/demo/operador/elementos', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify(element),
  })
  let value: unknown
  try { value = await response.json() } catch { throw new Error('El servidor no devolvió una respuesta válida.') }
  if (!response.ok) {
    const detail = typeof value === 'object' && value !== null && 'detail' in value && typeof value.detail === 'string' ? value.detail : 'No se pudo colocar el elemento.'
    throw new Error(detail)
  }
  if (typeof value !== 'object' || value === null || !('aceptado' in value)) throw new Error('El servidor no confirmó la colocación.')
  const result = value as Record<string, unknown>
  if (result.aceptado !== true) throw new Error('El servidor no confirmó la colocación.')
  return typeof result.elementoId === 'string' ? result.elementoId : 'Elemento agregado'
}
