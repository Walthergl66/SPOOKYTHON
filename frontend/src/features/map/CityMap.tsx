import { useEffect, useMemo, useRef, useState } from 'react'
import { Map as MapLibreMap, NavigationControl, ScaleControl, setWorkerUrl } from 'maplibre-gl'
import type { GeoJSONSource, MapLayerMouseEvent } from 'maplibre-gl'
import mapWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { PanelMap, PanelState } from '../../domain/panel'
import type { SimulatorSpeed } from '../../domain/simulator'
import type { OperatorTool } from '../../domain/operator'
import { createActorFeatures, createMovementAnimations, createSimulationFeatures, createStreetFeatures, emptyCollection, indexMapPositions, mergeActiveMovements, movementDurationMs, positionAlongPath } from './mapFeatures'
import type { AnimatedMovement, FeatureCollection, Position } from './mapFeatures'
import { boundsWithin, gameBounds, MANTA_CITY_VIEW, outsideBoundsMask, type MapBounds } from './mapArea'

interface CityMapProps {
  map: PanelMap
  state: PanelState
  selectedSurvivorId: string | undefined
  onSelectSurvivor: (survivorId: string) => void
  animationSpeed: SimulatorSpeed
  paused?: boolean
  operatorTool?: OperatorTool | null
  onOperatorPlacement?: (placement: { tipo: OperatorTool; nodo?: string; segmentoId?: string }) => void
}

const STYLE_URL = import.meta.env.VITE_NAVIRA_MAP_STYLE || 'https://tiles.openfreemap.org/styles/dark'
const BUILDING_TILES = 'https://tiles.openfreemap.org/planet'
const MAP_CENTER: Position = [-80.714, -0.9895]

setWorkerUrl(mapWorkerUrl)

export function CityMap({ map, state, selectedSurvivorId, onSelectSurvivor, animationSpeed, paused = false, operatorTool = null, onOperatorPlacement }: CityMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const latestDataRef = useRef<FeatureCollection>(emptyCollection())
  const latestStreetsRef = useRef<FeatureCollection>(emptyCollection())
  const latestActorsRef = useRef<FeatureCollection>(emptyCollection())
  const previousStateRef = useRef<PanelState | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const activeAnimationsRef = useRef(new Map<string, AnimatedMovement>())
  const latestStateRef = useRef(state)
  const latestMapRef = useRef(map)
  const animationSpeedRef = useRef(animationSpeed)
  const onSelectSurvivorRef = useRef(onSelectSurvivor)
  const operatorToolRef = useRef(operatorTool)
  const onOperatorPlacementRef = useRef(onOperatorPlacement)
  const cadenceRef = useRef<{ runId: string | undefined; turno: number | undefined; startedAt: number | null; observedTurnMs: number | null }>({ runId: state.runId, turno: state.turno, startedAt: null, observedTurnMs: null })
  const seenIncidentsRef = useRef(new Set<string>())
  const [incidentAlert, setIncidentAlert] = useState<{ id: string; turno: number; causa: string } | null>(null)
  latestStateRef.current = state
  latestMapRef.current = map
  animationSpeedRef.current = animationSpeed
  onSelectSurvivorRef.current = onSelectSurvivor
  operatorToolRef.current = operatorTool
  onOperatorPlacementRef.current = onOperatorPlacement
  const [ready, setReady] = useState(false)
  const [is3d, setIs3d] = useState(false)
  const [mapError, setMapError] = useState<string | null>(null)

  useEffect(() => {
    const incident = (state.eventosCiudad ?? []).find((event) => {
      const key = `${state.runId}:${event.id}`
      if (seenIncidentsRef.current.has(key)) return false
      seenIncidentsRef.current.add(key)
      return true
    })
    if (!incident) return
    setIncidentAlert(incident)
  }, [state.runId, state.eventosCiudad])

  useEffect(() => {
    if (!incidentAlert) return
    const timer = window.setTimeout(() => setIncidentAlert((current) => current?.id === incidentAlert.id ? null : current), 8000)
    return () => window.clearTimeout(timer)
  }, [incidentAlert])

  const points = useMemo(() => indexMapPositions(map), [map])
  const area = MANTA_CITY_VIEW
  const areaRef = useRef(area)
  areaRef.current = area
  const overviewRef = useRef(true)
  latestStreetsRef.current = useMemo(() => createStreetFeatures(map, points), [map, points])
  latestDataRef.current = useMemo(() => createSimulationFeatures(map, state, selectedSurvivorId, points), [map, state, selectedSurvivorId, points])
  latestActorsRef.current = useMemo(() => createActorFeatures(map, state, undefined, points), [map, state, points])

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
        pitch: 0,
        bearing: 0,
        maxBounds: areaRef.current,
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
      fitMapToMantaArea(instance, areaRef.current)
      highlightWater(instance)
      addMapLayers(instance, latestDataRef.current, latestActorsRef.current, latestStreetsRef.current, areaRef.current)
      const selectSurvivor = (event: MapLayerMouseEvent) => {
        if (operatorToolRef.current) return
        const survivor = event.features?.find((feature) => feature.properties?.kind === 'survivor')
        const survivorId = survivor?.properties?.actorId
        if (typeof survivorId === 'string') onSelectSurvivorRef.current(survivorId)
      }
      const setActorCursor = () => { instance.getCanvas().style.cursor = 'pointer' }
      const clearActorCursor = () => { instance.getCanvas().style.cursor = '' }
      for (const layer of ['navira-actor-markers', 'navira-actor-glyphs']) {
        instance.on('click', layer, selectSurvivor)
        instance.on('mouseenter', layer, setActorCursor)
        instance.on('mouseleave', layer, clearActorCursor)
      }
      instance.on('click', (event) => {
        const tool = operatorToolRef.current
        const place = onOperatorPlacementRef.current
        if (!tool || !place) return
        if (tool === 'incidente') {
          const street = instance.queryRenderedFeatures(event.point, { layers: ['navira-streets'] })[0]
          const segmentId = street?.properties?.segmentoId
          if (typeof segmentId === 'string' && segmentId.length > 0) place({ tipo: tool, segmentoId: segmentId })
          return
        }
        const target = nearestNodeAtMapClick(instance, latestMapRef.current, event.lngLat.lng, event.lngLat.lat, event.point.x, event.point.y)
        if (target) place({ tipo: tool, nodo: target })
      })
      setReady(true)
      setMapError(null)
    })
    instance.on('error', () => {
      if (!initialized && !failed) {
        failed = true
        setMapError('No se pudo cargar la cartografía. Revisa tu conexión; los controles de Navira siguen disponibles.')
      }
    })
    instance.on('dragstart', () => { overviewRef.current = false })
    instance.on('zoomstart', (event) => { if (event.originalEvent) overviewRef.current = false })
    const resizeObserver = new ResizeObserver(() => {
      if (container.clientWidth === 0 || container.clientHeight === 0) return
      instance.resize()
      if (initialized && overviewRef.current) fitMapToMantaArea(instance, areaRef.current)
    })
    resizeObserver.observe(container)
    return () => {
      resizeObserver.disconnect()
      if (animationFrameRef.current !== null) window.cancelAnimationFrame(animationFrameRef.current)
      mapRef.current = null
      instance.remove()
    }
  }, [])

  useEffect(() => {
    const instance = mapRef.current
    if (!ready || !instance) return
    instance.setMaxBounds(area)
    const mask = instance.getSource('navira-outside-manta-mask') as GeoJSONSource | undefined
    mask?.setData(outsideBoundsMask(area) as never)
    fitMapToMantaArea(instance, area)
    overviewRef.current = true
    setIs3d(false)
  }, [area, ready])

  useEffect(() => {
    const instance = mapRef.current
    if (!ready || !instance || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let visible = true
    const timer = window.setInterval(() => {
      visible = !visible
      if (!instance.getLayer('navira-incident-halo')) return
      instance.setPaintProperty('navira-incident-halo', 'circle-radius', visible ? 20 : 12)
      instance.setPaintProperty('navira-incident-halo', 'circle-opacity', visible ? 0.26 : 0.08)
    }, 650)
    return () => window.clearInterval(timer)
  }, [ready])

  useEffect(() => {
    const instance = mapRef.current
    if (!ready || !instance) return
    const source = instance.getSource('navira-streets') as GeoJSONSource | undefined
    source?.setData(latestStreetsRef.current as never)
  }, [map, points, ready])

  useEffect(() => {
    const instance = mapRef.current
    const previous = previousStateRef.current
    previousStateRef.current = state
    if (!ready || !instance) return

    const staticSource = instance.getSource('navira-simulation') as GeoJSONSource | undefined
    const actorSource = instance.getSource('navira-actors') as GeoJSONSource | undefined
    staticSource?.setData(latestDataRef.current as never)
    if (!actorSource) return
    if (paused) {
      activeAnimationsRef.current.clear()
      if (animationFrameRef.current !== null) window.cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
      actorSource.setData(latestActorsRef.current as never)
      return
    }
    const changedRun = previous !== null && previous.runId !== state.runId
    const now = performance.now()
    if (changedRun || cadenceRef.current.runId !== state.runId || cadenceRef.current.startedAt === null) {
      cadenceRef.current = { runId: state.runId, turno: state.turno, startedAt: now, observedTurnMs: null }
    } else if (previous?.snapshotVersion !== state.snapshotVersion && state.turno !== undefined && cadenceRef.current.turno !== undefined && state.turno > cadenceRef.current.turno) {
      const turnsElapsed = state.turno - cadenceRef.current.turno
      const sample = cadenceRef.current.startedAt === null ? null : (now - cadenceRef.current.startedAt) / turnsElapsed
      // Ignore long gaps caused by pause, background tabs, or reconnect before adapting visual playback.
      const observedTurnMs = sample !== null && sample <= 5000
        ? cadenceRef.current.observedTurnMs === null ? sample : cadenceRef.current.observedTurnMs * 0.5 + sample * 0.5
        : cadenceRef.current.observedTurnMs
      cadenceRef.current = { runId: state.runId, turno: state.turno, startedAt: now, observedTurnMs }
    }
    // Selection changes redraw the suggested route but must not cancel an in-flight actor transition.
    if (previous?.runId === state.runId && previous?.snapshotVersion === state.snapshotVersion) return

    if (changedRun) {
      activeAnimationsRef.current.clear()
      if (animationFrameRef.current !== null) window.cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const animations = previous && !reducedMotion ? createMovementAnimations(map, previous, state, now, points) : []
    if (reducedMotion) {
      activeAnimationsRef.current.clear()
      if (animationFrameRef.current !== null) window.cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
      actorSource.setData(latestActorsRef.current as never)
      return
    }

    const actorIds = new Set([
      ...(state.sobrevivientes ?? []).filter((actor) => actor.estado === 'activo').map((actor) => actor.id),
      ...(state.zombies ?? []).map((actor) => actor.id),
    ])
    const durationMs = movementDurationMs(animationSpeedRef.current, cadenceRef.current.observedTurnMs)
    const timedAnimations = animations.map((movement) => ({ ...movement, durationMs }))
    activeAnimationsRef.current = mergeActiveMovements(activeAnimationsRef.current, timedAnimations, actorIds)

    if (activeAnimationsRef.current.size === 0) {
      actorSource.setData(latestActorsRef.current as never)
      return
    }

    const animate = (now: number) => {
      animationFrameRef.current = null
      const positions = new Map<string, Position>()
      for (const [id, movement] of activeAnimationsRef.current) {
        const elapsed = Math.max(0, now - movement.startedAt)
        const progress = Math.min(1, elapsed / (movement.durationMs ?? movementDurationMs(animationSpeedRef.current)))
        positions.set(id, positionAlongPath(movement.path, progress))
        if (progress >= 1) activeAnimationsRef.current.delete(id)
      }
      actorSource.setData(createActorFeatures(map, latestStateRef.current, positions, points) as never)
      if (activeAnimationsRef.current.size > 0) animationFrameRef.current = window.requestAnimationFrame(animate)
    }
    if (animationFrameRef.current === null) animationFrameRef.current = window.requestAnimationFrame(animate)
  }, [ready, map, state, selectedSurvivorId, points, animationSpeed, paused])

  const togglePitch = () => {
    const instance = mapRef.current
    const next = !is3d
    setIs3d(next)
    overviewRef.current = false
    if (instance) instance.easeTo({ pitch: next ? 52 : 0, bearing: next ? -18 : 0, duration: 700 })
  }

  const showArea = () => {
    if (mapRef.current) fitMapToMantaArea(mapRef.current, area)
    overviewRef.current = true
    setIs3d(false)
  }
  const showGame = () => {
    overviewRef.current = false
    setIs3d(false)
    mapRef.current?.fitBounds(boundsWithin(gameBounds(map, state), area), { padding: 56, maxZoom: 15, pitch: 0, bearing: 0, duration: 0 })
  }

  return (
    <div className="maplibre-stage" aria-label="Mapa cartográfico 3D de Manta">
      <div ref={containerRef} className="maplibre-canvas" />
      {incidentAlert ? <div className="map-incident-alert" role="alert" aria-live="assertive">
        <span className="map-incident-alert-mark" aria-hidden="true">!</span>
        <span><strong>ALERTA VIAL · TURNO {incidentAlert.turno}</strong><small>{incidentAlert.causa}. Vía cerrada; rutas de evacuación actualizadas.</small></span>
      </div> : null}
      <div className="map-view-controls" role="group" aria-label="Vista del mapa">
      <button className="map-view-toggle" type="button" onClick={showArea} disabled={!ready}>Vista urbana</button>
      <button className="map-view-toggle" type="button" onClick={showGame} disabled={!ready}>Ver partida</button>
      <button className="map-view-toggle" type="button" onClick={togglePitch} aria-pressed={is3d} disabled={!ready}>
        {is3d ? 'Cambiar a 2D' : 'Cambiar a 3D'}
      </button>
      </div>
      {mapError ? <div className="map-provider-error" role="status">{mapError}</div> : null}
      {!ready && !mapError ? <div className="map-provider-loading" role="status">Cargando mapa de Manta…</div> : null}
      <span className="map-provider-label">Cartografía OSM · representación de simulación</span>
    </div>
  )
}

/** Encaja el clic a una intersección visible; evita colocar unidades en el océano o entre calles. */
function nearestNodeAtMapClick(mapInstance: MapLibreMap, map: PanelMap, lng: number, lat: number, x: number, y: number): string | null {
  let nearest: PanelMap['nodos'][number] | null = null
  let bestMeters = Number.POSITIVE_INFINITY
  const metersPerDegree = 111_320
  const longitudeScale = Math.cos((lat * Math.PI) / 180)
  const bounds = mapInstance.getBounds()
  for (const node of map.nodos) {
    if (!bounds.contains([node.lng, node.lat])) continue
    const distance = Math.hypot((node.lat - lat) * metersPerDegree, (node.lng - lng) * metersPerDegree * longitudeScale)
    if (distance < bestMeters) { bestMeters = distance; nearest = node }
  }
  if (!nearest) return null
  const projected = mapInstance.project([nearest.lng, nearest.lat])
  return Math.hypot(projected.x - x, projected.y - y) <= 24 ? nearest.id : null
}

/** Frames the fixed urban viewport and prevents zooming out beyond its extent. */
function fitMapToMantaArea(mapInstance: MapLibreMap, area: MapBounds) {
  // Release the old minimum before fitting a resized viewport or larger graph.
  mapInstance.setMinZoom(0)
  mapInstance.fitBounds(area, { padding: 0, maxZoom: 13, pitch: 0, bearing: 0, duration: 0 })
  mapInstance.setMinZoom(mapInstance.getZoom())
}

function addMapLayers(map: MapLibreMap, data: FeatureCollection, actors: FeatureCollection, streets: FeatureCollection, area: MapBounds) {
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
  map.addSource('navira-streets', { type: 'geojson', data: streets as never, promoteId: 'segmentoId' })
  map.addSource('navira-simulation', { type: 'geojson', data: data as never })
  map.addSource('navira-actors', { type: 'geojson', data: actors as never })
  map.addLayer({
    id: 'navira-streets', source: 'navira-streets', type: 'line',
    paint: {
      'line-color': '#85b9d2',
      'line-width': ['interpolate', ['linear'], ['zoom'], 11, 1.2, 16, 3.2],
      'line-opacity': ['case', ['get', 'blocked'], 0.95, 0.28],
    },
  })
  map.addLayer({
    id: 'navira-blocked-streets', source: 'navira-simulation', type: 'line',
    filter: ['==', ['get', 'kind'], 'blocked-street'],
    paint: { 'line-color': '#f05e62', 'line-width': ['interpolate', ['linear'], ['zoom'], 11, 1.8, 16, 4], 'line-opacity': 0.98 },
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
    id: 'navira-incident-halo', source: 'navira-simulation', type: 'circle',
    filter: ['==', ['get', 'kind'], 'road-incident'],
    paint: { 'circle-radius': 20, 'circle-color': '#ffc83d', 'circle-opacity': 0.24, 'circle-stroke-color': '#ffd84a', 'circle-stroke-width': 2 },
  })
  map.addLayer({
    id: 'navira-incident-markers', source: 'navira-simulation', type: 'circle',
    filter: ['==', ['get', 'kind'], 'road-incident'],
    paint: { 'circle-radius': 9, 'circle-color': '#ffd43b', 'circle-stroke-color': '#fff8db', 'circle-stroke-width': 2 },
  })
  map.addLayer({
    id: 'navira-incident-glyphs', source: 'navira-simulation', type: 'symbol',
    filter: ['==', ['get', 'kind'], 'road-incident'],
    layout: { 'text-field': ['get', 'glyph'], 'text-size': 13, 'text-font': ['Open Sans Bold'], 'text-allow-overlap': true, 'text-ignore-placement': true },
    paint: { 'text-color': '#2b2412', 'text-halo-color': '#fff2bf', 'text-halo-width': 0.6 },
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
    filter: ['in', ['get', 'kind'], ['literal', ['survivor', 'zombie', 'runner', 'horde']]],
    paint: {
      'circle-radius': ['match', ['get', 'kind'], 'survivor', 11, 'horde', 13, 12],
      'circle-color': ['match', ['get', 'kind'], 'survivor', '#18c6e4', 'horde', '#ff8b43', 'runner', '#a855f7', '#ed4c58'],
      'circle-stroke-color': '#f4f7fc', 'circle-stroke-width': 2,
    },
  })
  map.addLayer({
    id: 'navira-actor-glyphs', source: 'navira-actors', type: 'symbol',
    filter: ['in', ['get', 'kind'], ['literal', ['survivor', 'zombie', 'runner', 'horde']]],
    layout: { 'text-field': ['get', 'glyph'], 'text-size': 10, 'text-font': ['Open Sans Bold'], 'text-allow-overlap': true, 'text-ignore-placement': true },
    paint: { 'text-color': '#ffffff', 'text-halo-color': '#152238', 'text-halo-width': 0.7 },
  })
  map.addLayer({
    id: 'navira-refuge-labels', source: 'navira-simulation', type: 'symbol',
    filter: ['==', ['get', 'kind'], 'refuge'],
    layout: { 'text-field': ['get', 'label'], 'text-offset': [0, 1.25], 'text-size': 11, 'text-allow-overlap': false },
    paint: { 'text-color': '#e8fff2', 'text-halo-color': '#142034', 'text-halo-width': 1.4 },
  })

  // This visual mask clips the basemap to the selected camera window only;
  // snapshots and the playable graph continue to cover the full Manta fixture.
  map.addSource('navira-outside-manta-mask', { type: 'geojson', data: outsideBoundsMask(area) as never })
  map.addLayer({
    id: 'navira-outside-manta-mask',
    source: 'navira-outside-manta-mask',
    type: 'fill',
    paint: { 'fill-color': '#111827', 'fill-opacity': 0.98 },
  })
}

/** Make the coastline readable against the dark basemap without changing its geography. */
function highlightWater(map: MapLibreMap) {
  for (const layer of map.getStyle().layers) {
    const sourceLayer = 'source-layer' in layer ? layer['source-layer'] : undefined
    const waterLayer = layer.id.toLowerCase().includes('water') || sourceLayer?.toLowerCase() === 'water'
    const paint = layer.paint
    if (!waterLayer || !paint) continue
    if (layer.type === 'fill' && 'fill-color' in paint) {
      map.setPaintProperty(layer.id, 'fill-color', '#17496b')
    } else if (layer.type === 'line' && 'line-color' in paint) {
      map.setPaintProperty(layer.id, 'line-color', '#327b9e')
    } else if (layer.type === 'symbol' && 'text-color' in paint) {
      map.setPaintProperty(layer.id, 'text-color', '#b9d8e8')
      map.setPaintProperty(layer.id, 'text-halo-color', '#173247')
    }
  }
}
