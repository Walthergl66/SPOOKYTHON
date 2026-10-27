import { useEffect, useRef, useState } from 'react'
import { Map as MapLibreMap, NavigationControl, ScaleControl, setWorkerUrl } from 'maplibre-gl'
import type { GeoJSONSource } from 'maplibre-gl'
import mapWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { PanelMap, PanelState } from '../../domain/panel'
import { createActorFeatures, createMovementAnimations, createSimulationFeatures, emptyCollection, positionAlongPath } from './mapFeatures'
import type { FeatureCollection, Position } from './mapFeatures'

interface CityMapProps {
  map: PanelMap
  state: PanelState
  selectedSurvivorId: string | undefined
}

const STYLE_URL = import.meta.env.VITE_NAVIRA_MAP_STYLE || 'https://tiles.openfreemap.org/styles/dark'
const BUILDING_TILES = 'https://tiles.openfreemap.org/planet'
const MAP_CENTER: Position = [-80.720, -0.954]
// Extends the OSM extraction window by approximately 15 km in every direction.
// This is a cartographic viewport, not Manta's official boundary or simulation coverage.
const MANTA_BOUNDS: [Position, Position] = [[-80.890, -1.103], [-80.540, -0.799]]

setWorkerUrl(mapWorkerUrl)

export function CityMap({ map, state, selectedSurvivorId }: CityMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const latestDataRef = useRef<FeatureCollection>(emptyCollection())
  const latestActorsRef = useRef<FeatureCollection>(emptyCollection())
  const previousStateRef = useRef<PanelState | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const [ready, setReady] = useState(false)
  const [is3d, setIs3d] = useState(true)
  const [mapError, setMapError] = useState<string | null>(null)

  latestDataRef.current = createSimulationFeatures(map, state, selectedSurvivorId)
  latestActorsRef.current = createActorFeatures(map, state)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    let initialized = false
    let failed = false
    let instance: MapLibreMap
    try {
      instance = new MapLibreMap({
        container,
        style: STYLE_URL,
        center: MAP_CENTER,
        zoom: 15.2,
        pitch: 30,
        bearing: -8,
        maxBounds: MANTA_BOUNDS,
        renderWorldCopies: false,
        canvasContextAttributes: { antialias: true },
      })
    } catch {
      setMapError('Este dispositivo no pudo inicializar el mapa WebGL.')
      return
    }

    mapRef.current = instance
    instance.addControl(new NavigationControl({ visualizePitch: true }), 'top-right')
    instance.addControl(new ScaleControl({ unit: 'metric' }), 'bottom-right')
    instance.once('load', () => {
      initialized = true
      fitMapToMantaArea(instance)
      addMapLayers(instance, latestDataRef.current, latestActorsRef.current)
      setReady(true)
      setMapError(null)
    })
    instance.on('error', () => {
      if (!initialized && !failed) {
        failed = true
        setMapError('No se pudo cargar la cartografía. Revisa tu conexión; los controles de Navira siguen disponibles.')
      }
    })
    return () => {
      if (animationFrameRef.current !== null) window.cancelAnimationFrame(animationFrameRef.current)
      mapRef.current = null
      instance.remove()
    }
  }, [])

  useEffect(() => {
    const instance = mapRef.current
    if (!ready || !instance) return
    instance.setMaxBounds(MANTA_BOUNDS)
    fitMapToMantaArea(instance)
  }, [map.version, ready])

  useEffect(() => {
    const instance = mapRef.current
    const previous = previousStateRef.current
    previousStateRef.current = state
    if (!ready || !instance) return

    const staticSource = instance.getSource('navira-simulation') as GeoJSONSource | undefined
    const actorSource = instance.getSource('navira-actors') as GeoJSONSource | undefined
    staticSource?.setData(latestDataRef.current as never)
    if (!actorSource) return
    // Selection changes redraw the suggested route but must not cancel an in-flight actor transition.
    if (previous?.runId === state.runId && previous?.snapshotVersion === state.snapshotVersion) return

    if (animationFrameRef.current !== null) window.cancelAnimationFrame(animationFrameRef.current)
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const animations = previous && !reducedMotion ? createMovementAnimations(map, previous, state, performance.now()) : []
    if (animations.length === 0) {
      actorSource.setData(latestActorsRef.current as never)
      return
    }

    const durationMs = 1600
    const animate = (now: number) => {
      const positions = new Map<string, Position>()
      let stillMoving = false
      for (const movement of animations) {
        const elapsed = Math.max(0, now - movement.startedAt)
        const progress = Math.min(1, elapsed / durationMs)
        positions.set(movement.id, positionAlongPath(movement.path, progress))
        if (progress < 1) stillMoving = true
      }
      actorSource.setData(createActorFeatures(map, state, positions) as never)
      if (stillMoving) animationFrameRef.current = window.requestAnimationFrame(animate)
      else animationFrameRef.current = null
    }
    animationFrameRef.current = window.requestAnimationFrame(animate)
  }, [ready, map, state, selectedSurvivorId])

  const togglePitch = () => {
    const instance = mapRef.current
    const next = !is3d
    setIs3d(next)
    if (instance) instance.easeTo({ pitch: next ? 52 : 0, bearing: next ? -18 : 0, duration: 700 })
  }

  return (
    <div className="maplibre-stage" aria-label="Mapa cartográfico 3D de Manta">
      <div ref={containerRef} className="maplibre-canvas" />
      <button className="map-view-toggle" type="button" onClick={togglePitch} aria-pressed={is3d} disabled={!ready}>
        {is3d ? 'Vista 3D' : 'Vista 2D'}
      </button>
      {mapError ? <div className="map-provider-error" role="status">{mapError}</div> : null}
      {!ready && !mapError ? <div className="map-provider-loading" role="status">Cargando mapa de Manta…</div> : null}
      <span className="map-provider-label">Cartografía OSM · representación de simulación</span>
    </div>
  )
}

/** Frames the documented Manta data window instead of surrounding regions. */
function fitMapToMantaArea(mapInstance: MapLibreMap) {
  mapInstance.fitBounds(
    MANTA_BOUNDS,
    { padding: 32, maxZoom: 14.3, duration: 0 },
  )
  // Keep zoom-out at the scale that fits the whole declared area in this viewport.
  mapInstance.setMinZoom(mapInstance.getZoom())
}

function addMapLayers(map: MapLibreMap, data: FeatureCollection, actors: FeatureCollection) {
  map.addSource('openfreemap-buildings', { type: 'vector', url: BUILDING_TILES })
  const firstSymbolLayer = map.getStyle().layers.find((layer) => layer.type === 'symbol')?.id
  // render_height/render_min_height are provider tile attributes in metres; omit unknown heights instead of inventing them.
  map.addLayer({
    id: 'navira-3d-buildings',
    source: 'openfreemap-buildings',
    'source-layer': 'building',
    type: 'fill-extrusion',
    minzoom: 14,
    filter: ['all', ['has', 'render_height'], ['!=', ['get', 'hide_3d'], true]],
    paint: {
      'fill-extrusion-color': '#849ab8',
      'fill-extrusion-height': ['get', 'render_height'],
      'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
      'fill-extrusion-opacity': 0.68,
    },
  }, firstSymbolLayer)
  map.addSource('navira-simulation', { type: 'geojson', data: data as never })
  map.addSource('navira-actors', { type: 'geojson', data: actors as never })
  map.addLayer({
    id: 'navira-streets', source: 'navira-simulation', type: 'line',
    filter: ['==', ['get', 'kind'], 'street'],
    paint: {
      'line-color': ['case', ['get', 'blocked'], '#f05e62', '#85b9d2'],
      'line-width': ['interpolate', ['linear'], ['zoom'], 11, 1.2, 16, 3.2],
      'line-opacity': ['case', ['get', 'blocked'], 0.95, 0.28],
    },
  })
  map.addLayer({
    id: 'navira-route', source: 'navira-simulation', type: 'line',
    filter: ['==', ['get', 'kind'], 'route'],
    paint: { 'line-color': '#36d7bc', 'line-width': 5, 'line-opacity': 0.96 },
  })
  map.addLayer({
    id: 'navira-zombie-trail', source: 'navira-simulation', type: 'line',
    filter: ['==', ['get', 'kind'], 'zombie-trail'],
    paint: { 'line-color': '#ef9b54', 'line-width': 3, 'line-dasharray': [1.3, 1.2], 'line-opacity': 0.95 },
  })
  map.addLayer({
    id: 'navira-horde-area', source: 'navira-actors', type: 'circle',
    filter: ['==', ['get', 'kind'], 'horde'],
    paint: { 'circle-radius': 24, 'circle-color': '#f05058', 'circle-opacity': 0.24, 'circle-stroke-color': '#f05058', 'circle-stroke-width': 2 },
  })
  map.addLayer({
    id: 'navira-markers', source: 'navira-simulation', type: 'circle',
    filter: ['==', ['get', 'kind'], 'refuge'],
    paint: {
      'circle-radius': 9,
      'circle-color': '#47cf91',
      'circle-stroke-color': '#f4f7fc', 'circle-stroke-width': 1.5,
    },
  })
  map.addLayer({
    id: 'navira-actor-markers', source: 'navira-actors', type: 'circle',
    filter: ['in', ['get', 'kind'], ['literal', ['survivor', 'zombie', 'horde']]],
    paint: {
      'circle-radius': ['match', ['get', 'kind'], 'survivor', 11, 'horde', 13, 12],
      'circle-color': ['match', ['get', 'kind'], 'survivor', '#18c6e4', 'horde', '#ff8b43', '#ed4c58'],
      'circle-stroke-color': '#f4f7fc', 'circle-stroke-width': 2,
    },
  })
  map.addLayer({
    id: 'navira-actor-glyphs', source: 'navira-actors', type: 'symbol',
    filter: ['in', ['get', 'kind'], ['literal', ['survivor', 'zombie', 'horde']]],
    layout: { 'text-field': ['get', 'glyph'], 'text-size': 10, 'text-font': ['Open Sans Bold'], 'text-allow-overlap': true, 'text-ignore-placement': true },
    paint: { 'text-color': '#ffffff', 'text-halo-color': '#152238', 'text-halo-width': 0.7 },
  })
  map.addLayer({
    id: 'navira-refuge-labels', source: 'navira-simulation', type: 'symbol',
    filter: ['==', ['get', 'kind'], 'refuge'],
    layout: { 'text-field': ['get', 'label'], 'text-offset': [0, 1.25], 'text-size': 11, 'text-allow-overlap': false },
    paint: { 'text-color': '#e8fff2', 'text-halo-color': '#142034', 'text-halo-width': 1.4 },
  })

  // The inner ring leaves the documented Manta extraction window visible and
  // paints a dark mask over provider tiles everywhere outside it.
  map.addSource('navira-outside-manta-mask', { type: 'geojson', data: outsideMantaMask() as never })
  map.addLayer({
    id: 'navira-outside-manta-mask',
    source: 'navira-outside-manta-mask',
    type: 'fill',
    paint: { 'fill-color': '#111827', 'fill-opacity': 0.98 },
  })
}

function outsideMantaMask() {
  const [[west, south], [east, north]] = MANTA_BOUNDS
  const [outerWest, outerSouth, outerEast, outerNorth] = [-83, -3, -78, 2]
  const polygon = (ring: number[][]) => ({
    type: 'Feature',
    properties: {},
    geometry: { type: 'Polygon', coordinates: [ring] },
  })
  return {
    type: 'FeatureCollection',
    features: [
      polygon([[outerWest, outerSouth], [west, outerSouth], [west, outerNorth], [outerWest, outerNorth], [outerWest, outerSouth]]),
      polygon([[east, outerSouth], [outerEast, outerSouth], [outerEast, outerNorth], [east, outerNorth], [east, outerSouth]]),
      polygon([[west, outerNorth], [east, outerNorth], [east, north], [west, north], [west, outerNorth]]),
      polygon([[west, outerSouth], [east, outerSouth], [east, south], [west, south], [west, outerSouth]]),
    ],
  }
}

