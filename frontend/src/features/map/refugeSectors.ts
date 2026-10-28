type Position = [number, number]
type LinearRing = Position[]
type PolygonCoordinates = LinearRing[]
type SectorGeometry =
  | { type: 'Polygon'; coordinates: PolygonCoordinates }
  | { type: 'MultiPolygon'; coordinates: PolygonCoordinates[] }

export type MapNode = { id: string; lat: number; lng: number }
export type SectorFeature = {
  type: 'Feature'
  properties: { tipo: 'barrio' | 'parroquia'; nombre: string | null; parroquia?: string | null; fuente?: 'GeoManta' | 'CONALI'; areaM2?: number }
  geometry: SectorGeometry
}
export type SectorCollection = { type: 'FeatureCollection'; features: SectorFeature[] }

const SECTOR_DATA_URL = '/data/manta-sectores-2026-10-28.geojson'
let sectorDataPromise: Promise<SectorCollection> | undefined

/** Loads the dated GeoManta boundary snapshot once, avoiding a live dependency on its WFS during each run. */
export function loadMantaSectors(): Promise<SectorCollection> {
  if (!sectorDataPromise) {
    sectorDataPromise = fetch(SECTOR_DATA_URL)
      .then(async (response) => {
        if (!response.ok) throw new Error(`No se pudo cargar la cartografía territorial (${response.status}).`)
        return response.json() as Promise<SectorCollection>
      })
      .catch((error: unknown) => {
        sectorDataPromise = undefined
        throw error
      })
  }
  return sectorDataPromise
}

/** Returns the barrio that contains the refuge, with its parish; parish geometry is the fallback. */
export function refugeSectorLabel(
  node: MapNode | undefined,
  sectors: SectorCollection,
): string {
  if (!node) return 'Sector no identificado'
  const point: Position = [node.lng, node.lat]
  const barrio = sectors.features
    .filter((feature) => feature.properties.tipo === 'barrio'
      && hasName(feature.properties.nombre)
      // GeoManta contains a named zero-area placeholder with repeated vertices.
      // It is not a usable neighborhood boundary and must not label every refuge.
      && (feature.properties.areaM2 === undefined || feature.properties.areaM2 > 0)
      && contains(feature.geometry, point))
    .sort((a, b) => (a.properties.areaM2 ?? Number.POSITIVE_INFINITY) - (b.properties.areaM2 ?? Number.POSITIVE_INFINITY))[0]

  if (barrio) {
    const parish = barrio.properties.parroquia
    const barrioName = displayName(barrio.properties.nombre!)
    return parish ? `${barrioName} · ${displayName(parish)}` : barrioName
  }

  const parish = sectors.features
    .filter((feature) => feature.properties.tipo === 'parroquia' && hasName(feature.properties.nombre) && contains(feature.geometry, point))
    .sort((a, b) => {
      const sourcePriority = (a.properties.fuente === 'GeoManta' ? 0 : 1) - (b.properties.fuente === 'GeoManta' ? 0 : 1)
      return sourcePriority || (a.properties.areaM2 ?? Number.POSITIVE_INFINITY) - (b.properties.areaM2 ?? Number.POSITIVE_INFINITY)
    })[0]

  if (parish) return `Parroquia ${displayName(parish.properties.nombre!)}`
  return 'Sector no identificado'
}

function displayName(name: string): string {
  return name.toLocaleLowerCase('es-EC').replace(/(^|[\s-])([\p{L}])/gu, (_, separator: string, letter: string) => separator + letter.toLocaleUpperCase('es-EC'))
}

function hasName(name: string | null | undefined): name is string {
  return Boolean(name?.trim())
}

function contains(geometry: SectorGeometry, point: Position): boolean {
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates
  return polygons.some((rings) => pointInPolygon(rings, point))
}

function pointInPolygon(rings: PolygonCoordinates, point: Position): boolean {
  const [outer, ...holes] = rings
  return Boolean(outer && pointInRing(outer, point) && !holes.some((hole) => pointInRing(hole, point)))
}

/** Boundary points count as inside, making adjacent polygon edges stable for map-node coordinates. */
function pointInRing(ring: LinearRing, point: Position): boolean {
  let inside = false
  for (let index = 0, previous = ring.length - 1; index < ring.length; previous = index, index += 1) {
    const [x1, y1] = ring[previous]
    const [x2, y2] = ring[index]
    if (pointOnSegment(point, [x1, y1], [x2, y2])) return true

    const crossesLatitude = (y1 > point[1]) !== (y2 > point[1])
    if (crossesLatitude && point[0] < ((x2 - x1) * (point[1] - y1)) / (y2 - y1) + x1) inside = !inside
  }
  return inside
}

function pointOnSegment(point: Position, start: Position, end: Position): boolean {
  const lengthSquared = (end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2
  if (lengthSquared === 0) return point[0] === start[0] && point[1] === start[1]

  const cross = (point[1] - start[1]) * (end[0] - start[0]) - (point[0] - start[0]) * (end[1] - start[1])
  if (Math.abs(cross) > 1e-9) return false
  const dot = (point[0] - start[0]) * (end[0] - start[0]) + (point[1] - start[1]) * (end[1] - start[1])
  if (dot < 0) return false
  return dot <= lengthSquared
}
