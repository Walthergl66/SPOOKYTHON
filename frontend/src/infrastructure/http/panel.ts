import { parsePanelMap, parsePanelState, type PanelMap, type PanelSnapshot } from '../../domain/panel'

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
