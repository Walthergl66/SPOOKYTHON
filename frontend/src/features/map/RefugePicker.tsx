import { useEffect, useRef, useState } from 'react'
import { Map as MapLibreMap, setWorkerUrl } from 'maplibre-gl'
import type { GeoJSONSource } from 'maplibre-gl'
import mapWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'
import { nodoMasCercano, type CandidatoNodo, type SimulatorCandidatos } from '../../domain/simulator'

interface RefugePickerProps {
  candidates: SimulatorCandidatos
  refugeIds: readonly string[]
  slots: (string | null)[]
  placing: number | null
  onPick: (nodo: string) => boolean
  onPlace: (index: number | null) => void
  onClear: (index: number) => void
  onReset: () => void
  /** Texto del motivo si el selector está bloqueado (partida en curso); null si se puede editar. */
  lockedReason?: string | null
}

// Mismo estilo base que el mapa de simulación (CityMap) para que las calles se vean igual.
const STYLE_URL = import.meta.env.VITE_NAVIRA_MAP_STYLE || 'https://tiles.openfreemap.org/styles/dark'

setWorkerUrl(mapWorkerUrl)

/** Caja [[oeste, sur], [este, norte]] que cubren los nodos; null si no hay nodos. */
function limitesDeNodos(nodos: CandidatoNodo[]): [[number, number], [number, number]] | null {
  if (nodos.length === 0) return null
  const lngs = nodos.map((n) => n.lng), lats = nodos.map((n) => n.lat)
  return [[Math.min(...lngs), Math.min(...lats)], [Math.max(...lngs), Math.max(...lats)]]
}

/** Selector de refugios: el mapa es decorativo; el estado accesible está en el texto y los chips. */
export function RefugePicker({ candidates, refugeIds, slots, placing, onPick, onPlace, onClear, onReset, lockedReason = null }: RefugePickerProps) {
  const disabled = lockedReason !== null
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const [ready, setReady] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const latest = useRef({ candidates, onPick, placing, slots, disabled })
  latest.current = { candidates, onPick, placing, slots, disabled }

  useEffect(() => { if (disabled && placing !== null) onPlace(null) }, [disabled, placing, onPlace])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    let instance: MapLibreMap
    try {
      instance = new MapLibreMap({ container, style: STYLE_URL, center: [-80.72, -0.954], zoom: 12, renderWorldCopies: false, attributionControl: { compact: true } })
    } catch { setNotice('Este dispositivo no pudo inicializar el mapa WebGL.'); return }
    mapRef.current = instance
    instance.once('load', () => {
      const { nodos, calles } = latest.current.candidates
      const byId = new Map(nodos.map((n) => [n.id, n]))
      const lines = calles.flatMap((c) => {
        const a = byId.get(c.origen), b = byId.get(c.destino)
        return a && b ? [{ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [[a.lng, a.lat], [b.lng, b.lat]] } }] : []
      })
      const points = nodos.map((n) => ({ type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: [n.lng, n.lat] } }))
      instance.addSource('picker-streets', { type: 'geojson', data: { type: 'FeatureCollection', features: lines } as never })
      instance.addSource('picker-nodes', { type: 'geojson', data: { type: 'FeatureCollection', features: points } as never })
      instance.addSource('picker-refuges', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } as never })
      // Trazo igual al de CityMap: calles finas y tenues que se marcan al acercar el zoom.
      instance.addLayer({ id: 'picker-streets', source: 'picker-streets', type: 'line', paint: { 'line-color': '#85b9d2', 'line-opacity': 0.28, 'line-width': ['interpolate', ['linear'], ['zoom'], 11, 1.2, 16, 3.2] } })
      instance.addLayer({ id: 'picker-nodes', source: 'picker-nodes', type: 'circle', paint: { 'circle-radius': 2, 'circle-color': '#b0e2d2', 'circle-opacity': 0.6 } })
      instance.addLayer({ id: 'picker-refuges', source: 'picker-refuges', type: 'circle', paint: { 'circle-radius': 9, 'circle-color': '#47cf91', 'circle-stroke-color': '#f4f7fc', 'circle-stroke-width': 1.5 } })
      instance.addLayer({ id: 'picker-refuge-labels', source: 'picker-refuges', type: 'symbol', layout: { 'text-field': ['get', 'label'], 'text-size': 10, 'text-font': ['Open Sans Bold'], 'text-allow-overlap': true }, paint: { 'text-color': '#0b1a14' } })
      const bounds = limitesDeNodos(nodos)
      if (bounds) instance.fitBounds(bounds, { padding: 16, duration: 0 })
      setReady(true)
    })
    instance.on('click', (event) => {
      const { candidates: data, onPick: pick, disabled: locked } = latest.current
      if (locked) return
      const nodo = nodoMasCercano({ lat: event.lngLat.lat, lng: event.lngLat.lng }, data.nodos)
      if (!nodo) setNotice('Haz clic más cerca de una intersección')
      else if (!pick(nodo.id)) setNotice('Ese nodo ya es un refugio o no queda ranura libre; elige un chip para reemplazar.')
      else setNotice(null)
    })
    return () => { mapRef.current = null; instance.remove() }
  }, [])

  useEffect(() => {
    const source = mapRef.current?.getSource('picker-refuges') as GeoJSONSource | undefined
    if (!ready || !source) return
    const byId = new Map(candidates.nodos.map((n) => [n.id, n]))
    const features = slots.flatMap((nodo, i) => {
      const n = nodo ? byId.get(nodo) : undefined
      return n ? [{ type: 'Feature', properties: { label: String(i + 1) }, geometry: { type: 'Point', coordinates: [n.lng, n.lat] } }] : []
    })
    source.setData({ type: 'FeatureCollection', features } as never)
  }, [ready, slots, candidates])

  const placed = slots.filter((s) => s !== null).length
  return (
    <div className="refuge-picker">
      <div className="refuge-picker-head"><strong>Refugios de la partida</strong><span role="status">{placed}/{refugeIds.length} colocados{placed < refugeIds.length ? ` · faltan ${refugeIds.length - placed}` : ''}</span></div>
      <div ref={containerRef} className="refuge-picker-map" aria-hidden="true" />
      <ul className="refuge-chips">
        {refugeIds.map((id, i) => (
          <li key={id}>
            <button type="button" className={`refuge-chip${placing === i ? ' is-placing' : ''}`} aria-pressed={placing === i} disabled={disabled} onClick={() => onPlace(placing === i ? null : i)} aria-label={`${id}: ${slots[i] ?? 'pendiente'}. ${placing === i ? 'Cancelar reemplazo' : 'Colocar con el siguiente clic'}`}>
              <b aria-hidden="true">{slots[i] ? '⌂' : '○'}</b> {id} · {slots[i] ?? 'pendiente'}
            </button>
            {slots[i] ? <button type="button" className="refuge-chip-clear" onClick={() => onClear(i)} disabled={disabled} aria-label={`Quitar ${id}`}>×</button> : null}
          </li>
        ))}
      </ul>
      <p className="refuge-picker-hint">{placing !== null ? `Colocando ${refugeIds[placing]}: haz clic en el mapa.` : placed === refugeIds.length ? 'Listo. Elige un chip para reemplazar un refugio.' : 'Haz clic en una intersección para colocar el siguiente refugio.'}{placed > 0 && placed < refugeIds.length ? ' Con menos de 4 se usan los refugios del mapa.' : ''}</p>
      {lockedReason ? <p className="refuge-picker-notice">{lockedReason}</p> : null}
      {notice ? <p className="refuge-picker-notice" role="status">{notice}</p> : null}
      <button type="button" className="refuge-reset" onClick={() => { onReset(); setNotice(null) }} disabled={disabled || placed === 0}>Restablecer</button>
    </div>
  )
}
