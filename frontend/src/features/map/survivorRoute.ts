import type { PanelMap, PanelState } from '../../domain/panel'

export interface SurvivorRouteDetails {
  survivor: NonNullable<PanelState['sobrevivientes']>[number]
  path: string[]
  nextNode: string | null
  destination: string | null
}

/** Resolves only the selected inhabitant's route from the current public snapshot. */
export function getSurvivorRouteDetails(state: PanelState, map: PanelMap, survivorId: string | undefined): SurvivorRouteDetails | null {
  const survivor = state.sobrevivientes?.find(({ id }) => id === survivorId)
  if (!survivor) return null
  const route = survivor.estado === 'activo'
    ? state.rutasPrevistas?.find(({ sobrevivienteId }) => sobrevivienteId === survivor.id)
    : undefined
  const path = route?.trayecto ?? []
  const refuge = path.length > 0 ? map.refugios.find(({ nodo }) => nodo === path[path.length - 1]) : undefined
  return {
    survivor,
    path,
    nextNode: path[1] ?? null,
    destination: refuge?.id ?? (path.length > 0 ? path[path.length - 1] : null),
  }
}
