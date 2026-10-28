type RefugeIdentity = { id: string; nodo: string }
type MapNode = { id: string; lat: number; lng: number }

/** GAD Manta safe-point coordinates and their source parish/sector labels. */
const SECTOR_REFERENCES = [
  { lat: -0.9588192943885248, lng: -80.71242442236326, sector: 'Tarqui' },
  { lat: -0.9574742328837494, lng: -80.70208371535246, sector: 'Los Esteros' },
  { lat: -0.9522745219919659, lng: -80.72726572846808, sector: 'Manta' },
  { lat: -0.9460949, lng: -80.7488984, sector: 'Manta' },
]
const OFFICIAL_REFUGE_NODE_SECTORS: Record<string, string> = {
  'N-OSM-4135495376': 'Tarqui',
  'N-OSM-363670267': 'Los Esteros',
  'N-OSM-363657391': 'Manta',
  'N-OSM-4128106912': 'Manta',
}

/** Gives custom refuges the sector attached to the nearest official geographic reference. */
export function refugeSectorLabel(refuge: RefugeIdentity, nodes: MapNode[]): string {
  const officialSector = OFFICIAL_REFUGE_NODE_SECTORS[refuge.nodo]
  if (officialSector) return `Sector: ${officialSector}`

  const node = nodes.find((candidate) => candidate.id === refuge.nodo)
  if (!node) return 'Sector no identificado'

  let nearest = SECTOR_REFERENCES[0]
  let nearestDistance = distanceMeters(node, nearest)
  for (const reference of SECTOR_REFERENCES.slice(1)) {
    const distance = distanceMeters(node, reference)
    if (distance < nearestDistance) {
      nearest = reference
      nearestDistance = distance
    }
  }

  return `Sector cercano: ${nearest.sector}`
}

/** Haversine distance keeps sector choice based on geographic proximity. */
function distanceMeters(from: { lat: number; lng: number }, to: { lat: number; lng: number }): number {
  const radians = Math.PI / 180
  const lat1 = from.lat * radians
  const lat2 = to.lat * radians
  const deltaLat = (to.lat - from.lat) * radians
  const deltaLng = (to.lng - from.lng) * radians
  const haversine = Math.sin(deltaLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLng / 2) ** 2
  return 2 * 6_371_000 * Math.asin(Math.sqrt(haversine))
}
