import type { PanelMap, PanelState } from '../../domain/panel'
import type { Position } from './mapFeatures'

export type MapBounds = [Position, Position]

// OSM relation 112895 (Manta canton), rounded outwards with extraction margin.
// Includes urban/rural Manta; this rectangle is not an official municipal border.
export const MANTA_AREA: MapBounds = [[-80.920, -1.140], [-80.650, -0.920]]

// Approximate urban viewport traced from the user's reference image using the
// fixed coordinates of refuges R-01..R-04. This is a presentation window, not
// the geographic extent of the playable graph or an administrative boundary.
export const MANTA_CITY_VIEW: MapBounds = [[-80.807, -1.082], [-80.621, -0.897]]

/** Iteration avoids argument-count limits on large OSM graphs. */
export function boundsOfNodes(nodes: readonly { lng: number; lat: number }[]): MapBounds | null {
  if (nodes.length === 0) return null
  let west = Infinity, south = Infinity, east = -Infinity, north = -Infinity
  for (const node of nodes) {
    west = Math.min(west, node.lng)
    south = Math.min(south, node.lat)
    east = Math.max(east, node.lng)
    north = Math.max(north, node.lat)
  }
  return [[west, south], [east, north]]
}

/** Never clip a server-provided node when a new map version extends the graph. */
export function mapAreaBounds(map: Pick<PanelMap, 'nodos'>): MapBounds {
  const nodes = boundsOfNodes(map.nodos)
  if (!nodes) return MANTA_AREA
  return [
    [Math.min(MANTA_AREA[0][0], nodes[0][0]), Math.min(MANTA_AREA[0][1], nodes[0][1])],
    [Math.max(MANTA_AREA[1][0], nodes[1][0]), Math.max(MANTA_AREA[1][1], nodes[1][1])],
  ]
}

/** Allow map navigation up to five kilometres beyond the playable Manta box. */
export function paddedBounds(bounds: MapBounds): MapBounds {
  const [[west, south], [east, north]] = bounds
  const marginKm = 5
  const degreesPerKm = 1 / 111.32
  const latitudeMargin = marginKm * degreesPerKm
  const middleLatitudeRadians = ((south + north) / 2) * Math.PI / 180
  const longitudeMargin = latitudeMargin / Math.cos(middleLatitudeRadians)
  return [[west - longitudeMargin, south - latitudeMargin], [east + longitudeMargin, north + latitudeMargin]]
}

/** GeoJSON mask covering cartography outside a visible map window. */
export function outsideBoundsMask(bounds: MapBounds) {
  const [[west, south], [east, north]] = bounds
  const [outerWest, outerSouth, outerEast, outerNorth] = [-83, -3, -78, 2]
  const polygon = (ring: number[][]) => ({
    type: 'Feature' as const,
    properties: {},
    geometry: { type: 'Polygon' as const, coordinates: [ring] },
  })
  return {
    type: 'FeatureCollection' as const,
    features: [
      polygon([[outerWest, outerSouth], [west, outerSouth], [west, outerNorth], [outerWest, outerNorth], [outerWest, outerSouth]]),
      polygon([[east, outerSouth], [outerEast, outerSouth], [outerEast, outerNorth], [east, outerNorth], [east, outerSouth]]),
      polygon([[west, outerNorth], [east, outerNorth], [east, north], [west, north], [west, outerNorth]]),
      polygon([[west, outerSouth], [east, outerSouth], [east, south], [west, south], [west, outerSouth]]),
    ],
  }
}

/** Focus uses public characters and refuges, including terminal characters. */
export function gameBounds(map: PanelMap, state: PanelState): MapBounds {
  const ids = new Set([
    ...(state.sobrevivientes ?? []).map((actor) => actor.nodo),
    ...map.refugios.map((refuge) => refuge.nodo),
  ])
  return boundsOfNodes(map.nodos.filter((node) => ids.has(node.id))) ?? mapAreaBounds(map)
}

/** Restrict a camera focus rectangle to the visible urban window. */
export function boundsWithin(bounds: MapBounds, limit: MapBounds): MapBounds {
  const west = Math.max(bounds[0][0], limit[0][0])
  const south = Math.max(bounds[0][1], limit[0][1])
  const east = Math.min(bounds[1][0], limit[1][0])
  const north = Math.min(bounds[1][1], limit[1][1])
  if (west > east || south > north) return limit
  return [[west, south], [east, north]]
}
