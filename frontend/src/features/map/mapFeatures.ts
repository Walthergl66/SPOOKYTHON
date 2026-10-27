import type { PanelMap, PanelState } from '../../domain/panel'

export type Position = [number, number]
type Geometry = { type: 'Point'; coordinates: Position } | { type: 'LineString'; coordinates: Position[] }
type Feature = { type: 'Feature'; id?: string; geometry: Geometry; properties: Record<string, string | number | boolean> }
export type FeatureCollection = { type: 'FeatureCollection'; features: Feature[] }

/** Projects only public panel data into local GeoJSON; no gameplay state is sent to the tile provider. */
export function createSimulationFeatures(map: PanelMap, state: PanelState, selectedSurvivorId: string | undefined): FeatureCollection {
  const pointById = new Map(map.nodos.map((node) => [node.id, [node.lng, node.lat] as Position]))
  const features: Feature[] = []
  const blockedEdges = new Set(state.aristasBloqueadas ?? [])
  const blockedSegments = new Set(state.segmentosBloqueados ?? [])
  // Streets are undirected for display, so a closure on either directed edge marks the shared segment.
  const streetsBySegment = new Map<string, typeof map.calles>()
  for (const street of map.calles) {
    const segment = streetsBySegment.get(street.segmentoId) ?? []
    segment.push(street)
    streetsBySegment.set(street.segmentoId, segment)
  }
  const seenSegments = new Set<string>()
  for (const street of map.calles) {
    if (seenSegments.has(street.segmentoId)) continue
    const from = pointById.get(street.origen)
    const to = pointById.get(street.destino)
    if (!from || !to) continue
    seenSegments.add(street.segmentoId)
    const blocked = blockedSegments.has(street.segmentoId) || (streetsBySegment.get(street.segmentoId) ?? []).some(({ id }) => blockedEdges.has(id))
    features.push({
      type: 'Feature', id: street.segmentoId,
      geometry: { type: 'LineString', coordinates: [from, to] },
      properties: { kind: 'street', blocked },
    })
  }
  for (const route of state.rutasPrevistas ?? []) {
    if (route.sobrevivienteId !== selectedSurvivorId) continue
    const coordinates = route.trayecto.map((id) => pointById.get(id)).filter((point): point is Position => point !== undefined)
    if (coordinates.length > 1) features.push({ type: 'Feature', id: `route-${route.sobrevivienteId}`, geometry: { type: 'LineString', coordinates }, properties: { kind: 'route' } })
  }
  for (const movement of state.movimientosZombies ?? []) {
    const coordinates = movement.trayecto.map((id) => pointById.get(id)).filter((point): point is Position => point !== undefined)
    if (coordinates.length > 1) features.push({ type: 'Feature', id: `trail-${movement.id}`, geometry: { type: 'LineString', coordinates }, properties: { kind: 'zombie-trail' } })
  }
  for (const refuge of map.refugios) {
    const coordinates = pointById.get(refuge.nodo)
    if (coordinates) features.push({ type: 'Feature', id: refuge.id, geometry: { type: 'Point', coordinates }, properties: { kind: 'refuge', label: refuge.id } })
  }
  return { type: 'FeatureCollection', features }
}

export interface AnimatedMovement {
  id: string
  path: Position[]
  startedAt: number
}

/** Builds only public actor positions so animation frames never rebuild the street graph. */
export function createActorFeatures(map: PanelMap, state: PanelState, overrides = new Map<string, Position>()): FeatureCollection {
  const pointById = new Map(map.nodos.map((node) => [node.id, [node.lng, node.lat] as Position]))
  const features: Feature[] = []
  for (const survivor of state.sobrevivientes ?? []) {
    if (survivor.estado !== 'activo') continue
    const coordinates = overrides.get(survivor.id) ?? pointById.get(survivor.nodo)
    if (coordinates) features.push({ type: 'Feature', id: survivor.id, geometry: { type: 'Point', coordinates }, properties: { kind: 'survivor', glyph: 'S' } })
  }
  for (const zombie of state.zombies ?? []) {
    const coordinates = overrides.get(zombie.id) ?? pointById.get(zombie.nodo)
    if (coordinates) features.push({ type: 'Feature', id: zombie.id, geometry: { type: 'Point', coordinates }, properties: { kind: zombie.tipo === 'horda' ? 'horde' : 'zombie', glyph: zombie.tipo === 'horda' ? 'H' : 'Z' } })
  }
  return { type: 'FeatureCollection', features }
}

/** Creates transitions only from consecutive public snapshots; it cannot commit or predict a move. */
export function createMovementAnimations(map: PanelMap, previous: PanelState, current: PanelState, startedAt: number): AnimatedMovement[] {
  if (!previous.runId || previous.runId !== current.runId || previous.snapshotVersion === current.snapshotVersion) return []
  const pointById = new Map(map.nodos.map((node) => [node.id, [node.lng, node.lat] as Position]))
  const movements: AnimatedMovement[] = []
  const previousSurvivors = new Map((previous.sobrevivientes ?? []).map((actor) => [actor.id, actor]))
  for (const actor of current.sobrevivientes ?? []) {
    const origin = previousSurvivors.get(actor.id)
    if (actor.estado !== 'activo' || !origin || origin.nodo === actor.nodo) continue
    const path = [pointById.get(origin.nodo), pointById.get(actor.nodo)].filter((point): point is Position => point !== undefined)
    if (path.length > 1) movements.push({ id: actor.id, path, startedAt })
  }

  const previousZombies = new Map((previous.zombies ?? []).map((actor) => [actor.id, actor]))
  const movementsByZombie = new Map((current.movimientosZombies ?? []).map((movement) => [movement.id, movement]))
  for (const actor of current.zombies ?? []) {
    const origin = previousZombies.get(actor.id)
    if (!origin || origin.nodo === actor.nodo) continue
    const confirmedPath = movementsByZombie.get(actor.id)?.trayecto ?? [origin.nodo, actor.nodo]
    const path = confirmedPath.map((nodeId) => pointById.get(nodeId)).filter((point): point is Position => point !== undefined)
    if (path.length > 1 && samePosition(path[path.length - 1], pointById.get(actor.nodo))) movements.push({ id: actor.id, path, startedAt })
  }
  return movements
}

/** Advances evenly across each server-confirmed graph segment for a brief visual transition. */
export function positionAlongPath(path: Position[], progress: number): Position {
  const scaled = Math.min(1, Math.max(0, progress)) * (path.length - 1)
  const segment = Math.min(path.length - 2, Math.floor(scaled))
  const fraction = progress >= 1 ? 1 : scaled - segment
  const from = path[segment]
  const to = path[segment + 1]
  return [from[0] + (to[0] - from[0]) * fraction, from[1] + (to[1] - from[1]) * fraction]
}

function samePosition(left: Position | undefined, right: Position | undefined): boolean {
  return Boolean(left && right && left[0] === right[0] && left[1] === right[1])
}

export function emptyCollection(): FeatureCollection {
  return { type: 'FeatureCollection', features: [] }
}
