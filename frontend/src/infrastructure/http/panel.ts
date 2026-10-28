import { parsePanelMap, parsePanelRoute, parsePanelState, type PanelMap, type PanelRoute, type PanelSnapshot } from '../../domain/panel'

export async function loadPanelSnapshot(signal?: AbortSignal): Promise<PanelSnapshot> {
  const stateResponse = await fetch('/panel/estado', { signal, headers: { Accept: 'application/json' } })
  if (!stateResponse.ok) {
    throw new Error('No se pudo obtener el estado del panel.')
  }
  const state = parsePanelState(await stateResponse.json())
  if (state.estado === 'sin_partida') return { map: null, state }

  const mapResponse = await fetch('/panel/mapa', { signal, headers: { Accept: 'application/json' } })
  if (!mapResponse.ok) {
    throw new Error('No se pudo obtener una proyección activa del panel.')
  }

  const map = parsePanelMap(await mapResponse.json())
  if (state.mapVersion !== map.version) {
    throw new Error('La versión del mapa no coincide con el snapshot recibido.')
  }
  return { map, state }
}

export async function loadPanelMap(expectedVersion: string, signal?: AbortSignal): Promise<PanelMap> {
  const response = await fetch('/panel/mapa', { signal, headers: { Accept: 'application/json' } })
  if (!response.ok) throw new Error('No se pudo obtener una proyección activa del panel.')
  const map = parsePanelMap(await response.json())
  if (map.version !== expectedVersion) throw new Error('La versión del mapa no coincide con el snapshot recibido.')
  return map
}

/** Pide al servidor la ruta de una sola persona, sin calcular la cohorte completa. */
export async function loadPanelRoute(survivorId: string, signal?: AbortSignal): Promise<PanelRoute> {
  const response = await fetch(`/panel/ruta/${encodeURIComponent(survivorId)}`, {
    signal,
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) {
    let detail = 'No se pudo obtener la ruta recomendada.'
    try {
      const body: unknown = await response.json()
      if (typeof body === 'object' && body !== null && 'detail' in body && typeof body.detail === 'string') detail = body.detail
    } catch {
      // Conserva el mensaje local si el servidor no envía JSON de error.
    }
    throw new Error(detail)
  }
  return parsePanelRoute(await response.json())
}
