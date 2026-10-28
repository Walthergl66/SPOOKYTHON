import type { Map as MapLibreMap } from 'maplibre-gl'

const STREET_NAME_SOURCE_ID = 'navira-street-name-tiles'
const OPENFREEMAP_VECTOR_TILES = 'https://tiles.openfreemap.org/planet'

const MAJOR_ROAD_CLASSES = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary']
const LOCAL_ROAD_CLASSES = ['minor', 'service', 'track', 'path', 'pedestrian']

/**
 * Adds two collision-aware label layers backed by OpenMapTiles road-name vectors.
 * Major roads are readable at the city overview; local names wait for a closer zoom
 * so labels do not overwhelm Navira's actors, routes, and incident markers.
 */
export function addStreetNameLayers(map: MapLibreMap) {
  const style = map.getStyle()
  const sourceLayer = style.layers.find((layer) =>
    layer.type === 'symbol'
    && 'source-layer' in layer
    && layer['source-layer'] === 'transportation_name'
    && 'source' in layer
    && typeof layer.source === 'string',
  )
  const sourceId = sourceLayer && 'source' in sourceLayer && typeof sourceLayer.source === 'string'
    ? sourceLayer.source
    : STREET_NAME_SOURCE_ID

  if (!map.getSource(sourceId)) {
    map.addSource(sourceId, { type: 'vector', url: OPENFREEMAP_VECTOR_TILES })
  }

  const baseLayerId = 'navira-streets'
  const beforeId = map.getLayer(baseLayerId) ? undefined : map.getStyle().layers.find((layer) => layer.type === 'symbol')?.id
  const roadNameLayer = (id: string, minzoom: number, roadClasses: string[]) => ({
    id,
    source: sourceId,
    'source-layer': 'transportation_name',
    type: 'symbol' as const,
    minzoom,
    filter: [
      'all',
      ['has', 'name'],
      ['in', ['get', 'class'], ['literal', roadClasses]],
    ] as never,
    layout: {
      'symbol-placement': 'line' as const,
      'symbol-spacing': 420,
      'text-field': ['coalesce', ['get', 'name:es'], ['get', 'name']],
      'text-font': ['Open Sans Regular'],
      'text-size': ['interpolate', ['linear'], ['zoom'], minzoom, 9, 16, 12],
      'text-max-angle': 30,
      'text-padding': 3,
      'text-keep-upright': true,
      'text-allow-overlap': false,
      'text-ignore-placement': false,
    },
    paint: {
      'text-color': '#d6e4ef',
      'text-halo-color': '#111827',
      'text-halo-width': 1.3,
      'text-halo-blur': 0.2,
    },
  })

  map.addLayer(roadNameLayer('navira-road-names-major', 11.5, MAJOR_ROAD_CLASSES) as never, beforeId)
  map.addLayer(roadNameLayer('navira-road-names-local', 14, LOCAL_ROAD_CLASSES) as never, beforeId)
}
