import type { OperatorPlacement } from '../../domain/operator'

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
