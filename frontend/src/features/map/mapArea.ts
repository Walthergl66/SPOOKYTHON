import type { PanelMap, PanelState } from '../../domain/panel'
import type { Position } from './mapFeatures'

export type MapBounds = [Position, Position]

// OSM relation 112895 (Manta canton), rounded outwards with extraction margin.
// Includes urban/rural Manta; this rectangle is not an official municipal border.
export const MANTA_AREA: MapBounds = [[-80.920, -1.140], [-80.650, -0.920]]

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

/** Navigation margin lets fitBounds show the entire area with screen padding. */
export function paddedBounds(bounds: MapBounds): MapBounds {
  const [[west, south], [east, north]] = bounds
  const x = Math.max((east - west) * 0.25, 0.005)
  const y = Math.max((north - south) * 0.25, 0.005)
  return [[west - x, south - y], [east + x, north + y]]
}

/** Focus uses public characters and refuges, including terminal characters. */
export function gameBounds(map: PanelMap, state: PanelState): MapBounds {
  const ids = new Set([
    ...(state.sobrevivientes ?? []).map((actor) => actor.nodo),
    ...map.refugios.map((refuge) => refuge.nodo),
  ])
  return boundsOfNodes(map.nodos.filter((node) => ids.has(node.id))) ?? mapAreaBounds(map)
}
