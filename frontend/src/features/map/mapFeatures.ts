import type { PanelMap, PanelState } from '../../domain/panel'
import type { SimulatorSpeed } from '../../domain/simulator'

export type Position = [number, number]
type Geometry = { type: 'Point'; coordinates: Position } | { type: 'LineString'; coordinates: Position[] }
type Feature = { type: 'Feature'; id?: string; geometry: Geometry; properties: Record<string, string | number | boolean> }
export type FeatureCollection = { type: 'FeatureCollection'; features: Feature[] }

/** Reused across animation frames; the graph is immutable for a map version. */
export function indexMapPositions(map: PanelMap): ReadonlyMap<string, Position> {
  return new Map(map.nodos.map((node) => [node.id, [node.lng, node.lat] as Position]))
}

type MapStreet = PanelMap['calles'][number]
type StreetIndex = { bySegment: Map<string, MapStreet>; byEdge: Map<string, MapStreet> }
const streetIndexes = new WeakMap<PanelMap, StreetIndex>()

/** Builds each OSM segment once for the immutable map version; turns do not resend this GeoJSON. */
export function createStreetFeatures(map: PanelMap, pointById = indexMapPositions(map)): FeatureCollection {
  const features: Feature[] = []
  for (const street of getStreetIndex(map).bySegment.values()) {
    const from = pointById.get(street.origen)
    const to = pointById.get(street.destino)
    if (!from || !to) continue
    features.push({
      type: 'Feature', id: street.segmentoId,
      geometry: { type: 'LineString', coordinates: [from, to] },
      properties: { kind: 'street' },
    })
  }
  return { type: 'FeatureCollection', features }
}

function getStreetIndex(map: PanelMap): StreetIndex {
  const cached = streetIndexes.get(map)
  if (cached) return cached
  const bySegment = new Map<string, MapStreet>()
  const byEdge = new Map<string, MapStreet>()
  for (const street of map.calles) {
    if (!bySegment.has(street.segmentoId)) bySegment.set(street.segmentoId, street)
    byEdge.set(street.id, street)
  }
  const index = { bySegment, byEdge }
  streetIndexes.set(map, index)
  return index
}

/** Projects changing public panel data. Immutable OSM streets use createStreetFeatures once per map. */
export function createSimulationFeatures(map: PanelMap, state: PanelState, selectedSurvivorId: string | undefined, pointById = indexMapPositions(map)): FeatureCollection {
  const features: Feature[] = []
  const blocked = new Set(state.segmentosBloqueados ?? [])
  const streetIndex = getStreetIndex(map)
  for (const edgeId of state.aristasBloqueadas ?? []) {
    const street = streetIndex.byEdge.get(edgeId)
    if (street) blocked.add(street.segmentoId)
  }
  for (const segmentId of blocked) {
    const street = streetIndex.bySegment.get(segmentId)
    if (!street) continue
    const from = pointById.get(street.origen)
    const to = pointById.get(street.destino)
    if (!from || !to) continue
    features.push({
      type: 'Feature', id: `blocked-${segmentId}`,
      geometry: { type: 'LineString', coordinates: [from, to] },
      properties: { kind: 'blocked-street' },
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
  for (const event of state.eventosCiudad ?? []) {
    if (typeof event.lat !== 'number' || typeof event.lng !== 'number') continue
    features.push({
      type: 'Feature', id: `incident-${event.id}`,
      geometry: { type: 'Point', coordinates: [event.lng, event.lat] },
      properties: { kind: 'road-incident', glyph: '!' },
    })
  }
  return { type: 'FeatureCollection', features }
}

export interface AnimatedMovement {
  id: string
  path: Position[]
  startedAt: number
  /** Duration is captured at confirmation so later cadence samples cannot rewind an actor. */
  durationMs?: number
}

/** Matches the visual transition to the local turn cadence while retaining every confirmed move. */
export function movementDurationMs(speed: SimulatorSpeed, observedTurnMs?: number | null): number {
  const nominal = 2000 / speed
  return observedTurnMs && Number.isFinite(observedTurnMs) && observedTurnMs > 0
    ? Math.max(nominal, observedTurnMs)
    : nominal
}

/** Keeps a confirmed transition alive across snapshots that only advance phase or metadata. */
export function mergeActiveMovements(active: ReadonlyMap<string, AnimatedMovement>, confirmed: AnimatedMovement[], visibleActorIds: ReadonlySet<string>): Map<string, AnimatedMovement> {
  const merged = new Map(active)
  for (const id of merged.keys()) {
    if (!visibleActorIds.has(id)) merged.delete(id)
  }
  for (const movement of confirmed) merged.set(movement.id, movement)
  return merged
}

/** Builds only public actor positions so animation frames never rebuild the street graph. */
export function createActorFeatures(map: PanelMap, state: PanelState, overrides = new Map<string, Position>(), pointById = indexMapPositions(map)): FeatureCollection {
  const features: Feature[] = []
  for (const survivor of state.sobrevivientes ?? []) {
    if (survivor.estado !== 'activo') continue
    const coordinates = overrides.get(survivor.id) ?? pointById.get(survivor.nodo)
    if (coordinates) features.push({ type: 'Feature', id: survivor.id, geometry: { type: 'Point', coordinates }, properties: { kind: 'survivor', glyph: 'S', actorId: survivor.id } })
  }
  for (const zombie of state.zombies ?? []) {
    const coordinates = overrides.get(zombie.id) ?? pointById.get(zombie.nodo)
    if (coordinates) features.push({ type: 'Feature', id: zombie.id, geometry: { type: 'Point', coordinates }, properties: { kind: zombie.tipo === 'horda' ? 'horde' : 'zombie', glyph: zombie.tipo === 'horda' ? 'H' : 'Z' } })
  }
  return { type: 'FeatureCollection', features }
}

/** Creates transitions only from consecutive public snapshots; it cannot commit or predict a move. */
export function createMovementAnimations(map: PanelMap, previous: PanelState, current: PanelState, startedAt: number, pointById = indexMapPositions(map)): AnimatedMovement[] {
  if (!previous.runId || previous.runId !== current.runId || previous.snapshotVersion === current.snapshotVersion) return []
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
