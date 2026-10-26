import { useEffect, useRef, useState } from 'react'
import { CityMap } from '../features/map/CityMap'
import { GameControls } from '../features/game/GameControls'
import { ModeCard, type NaviraMode } from '../features/mode/ModeCard'
import { loadPanelMap, loadPanelSnapshot, type PanelSnapshot, type PanelState } from '../shared/api/panel'
import { subscribePanel, type PanelConnection, type PanelCursor } from '../shared/realtime/panel'
import { BrandMark } from '../shared/ui/BrandMark'

const modeCopy: Record<NaviraMode, { eyebrow: string; title: string; body: string }> = {
  simulator: {
    eyebrow: 'OBSERVACIÓN AUTOMÁTICA',
    title: 'Mira cómo cambia la ciudad.',
    body: 'Sigue las decisiones, las rutas y el avance de una evacuación simulada, turno a turno.',
  },
  game: {
    eyebrow: 'EXPERIENCIA HUMANA',
    title: 'Encuentra tu camino a salvo.',
    body: 'Aparece en un punto de Manta y decide cómo llevar a tu personaje hasta un refugio.',
  },
}

export function App() {
  const [mode, setMode] = useState<NaviraMode>('simulator')
  const [selectedSurvivorId, setSelectedSurvivorId] = useState<string | undefined>()
  const [snapshot, setSnapshot] = useState<PanelSnapshot | null>(null)
  const [panelError, setPanelError] = useState<string | null>(null)
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)
  const [refreshCount, setRefreshCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [connection, setConnection] = useState<PanelConnection>('connecting')
  const cursorRef = useRef<PanelCursor | null>(null)
  const mapRef = useRef<PanelSnapshot['map']>(null)
  const copy = modeCopy[mode]

  const applyPanelState = (nextState: PanelState, cursor: PanelCursor, emittedAt: string, nextMap?: PanelSnapshot['map']) => {
    const previous = cursorRef.current
    if (previous?.runId === cursor.runId && cursor.sequence < previous.sequence) return
    if (previous?.runId === cursor.runId && cursor.sequence === previous.sequence) {
      if (nextState.estado === 'activa' && nextMap && nextMap.version === nextState.mapVersion) {
        mapRef.current = nextMap
        setSnapshot((current) => current?.state.estado === 'activa' && current.state.runId === nextState.runId
          ? { map: nextMap, state: current.state }
          : current)
      }
      setPanelError(null)
      setLoading(false)
      setUpdatedAt(formatTime(emittedAt))
      return
    }
    cursorRef.current = cursor

    if (nextState.estado === 'sin_partida') {
      mapRef.current = null
      setSnapshot({ map: null, state: nextState })
    } else {
      const matchingMap: PanelSnapshot['map'] = nextMap && nextMap.version === nextState.mapVersion
        ? nextMap
        : mapRef.current?.version === nextState.mapVersion ? mapRef.current : null
      mapRef.current = matchingMap
      setSnapshot({ map: matchingMap, state: nextState })
      if (!matchingMap) {
        const mapVersion = nextState.mapVersion
        const runId = nextState.runId
        if (!mapVersion || !runId) return
        loadPanelMap(mapVersion)
          .then((loadedMap) => {
            const currentCursor = cursorRef.current
            if (!currentCursor || currentCursor.runId !== runId || currentCursor.sequence < (nextState.snapshotVersion ?? 0)) return
            mapRef.current = loadedMap
            setSnapshot((current) => current?.state.estado === 'activa' && current.state.mapVersion === loadedMap.version
              ? { map: loadedMap, state: current.state }
              : current)
          })
          .catch((error: unknown) => setPanelError(error instanceof Error ? error.message : 'No se pudo cargar el mapa de la partida.'))
      }
    }
    setPanelError(null)
    setLoading(false)
    setUpdatedAt(formatTime(emittedAt))
  }

  useEffect(() => {
    if (refreshCount === 0) return
    const controller = new AbortController()
    setLoading(true)
    loadPanelSnapshot(controller.signal)
      .then((nextSnapshot) => {
        const { state: nextState, map: nextMap } = nextSnapshot
        const cursor = nextState.estado === 'activa'
          ? { runId: nextState.runId ?? null, sequence: nextState.snapshotVersion ?? 0 }
          : { runId: null, sequence: 0 }
        applyPanelState(nextState, cursor, new Date().toISOString(), nextMap)
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setPanelError(error instanceof Error ? error.message : 'El panel no está disponible.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [refreshCount])

  useEffect(() => subscribePanel((nextState, cursor, emittedAt) => {
    applyPanelState(nextState, cursor, emittedAt)
  }, setConnection), [])

  useEffect(() => {
    mapRef.current = snapshot?.map ?? null
  }, [snapshot?.map])

  const state = snapshot?.state ?? null
  const map = snapshot?.map ?? null
  const active = state?.estado === 'activa'
  const cityName = map?.version.includes('manta') ? 'Manta · Manabí' : map ? 'Mapa del escenario' : 'Manta · Manabí'
  const mapLabel = map?.version.startsWith('navira-demo') ? 'MUNDO SINTÉTICO' : map ? 'MAPA DE SIMULACIÓN' : 'VISTA DE CIUDAD'
  const statusLabel = active ? `TURNO ${state.turno} · ${(state.fase ?? 'desconocida').replaceAll('_', ' ')}` : state?.estado === 'sin_partida' ? 'SIN PARTIDA ACTIVA' : loading ? 'CARGANDO PROYECCIÓN' : 'DATOS NO DISPONIBLES'
  const survivors = (active ? state.sobrevivientes : undefined)?.filter(({ estado: survivorState }) => survivorState === 'activo') ?? []
  const selectedRouteOwner = survivors.some(({ id }) => id === selectedSurvivorId) ? selectedSurvivorId : survivors[0]?.id

  return (
    <main className="app-shell">
      <a className="skip-link" href="#main-content">Saltar al contenido</a>
      <header className="topbar">
        <a className="brand" href="#main-content" aria-label="Navira, inicio">
          <BrandMark />
          <span className="brand-name">navira</span>
        </a>
        <div className="topbar-context">
          <span className={`context-pulse${active ? '' : ' is-idle'}`} aria-hidden="true" />
          <span>{active && map && !map.version.includes('manta') ? 'ESCENARIO DE PRUEBA' : 'MANTA, ECUADOR'}</span>
          <span className="context-divider" aria-hidden="true" />
          <span className="context-label">PLATAFORMA DE EVACUACIÓN</span>
        </div>
        <div className="topbar-version">BETA <span>·</span> 0.1</div>
      </header>

      <section className="welcome-grid" id="main-content" tabIndex={-1} aria-labelledby="welcome-title">
        <div className="welcome-copy">
          <div className="section-kicker"><span>01</span> CENTRO DE CONTROL</div>
          <h1 id="welcome-title">Una ciudad.<br /><em>Dos formas</em> de vivirla.</h1>
          <p className="intro-copy">
            Explora un mundo de evacuación que cambia en cada turno. Observa la simulación o toma el control como sobreviviente.
          </p>

          <div className="mode-heading">
            <span>ELIGE TU EXPERIENCIA</span>
            <span className="heading-rule" aria-hidden="true" />
          </div>
          <div className="mode-list" role="group" aria-label="Modo de Navira">
            <ModeCard mode="simulator" selected={mode === 'simulator'} onSelect={setMode} />
            <ModeCard mode="game" selected={mode === 'game'} onSelect={setMode} />
          </div>
          <p className="mode-note">Vista previa de modos · la selección todavía no inicia una partida.</p>

          <div className="mode-preview" aria-live="polite">
            <div className="preview-index">{mode === 'simulator' ? 'A' : 'B'}</div>
            <div>
              <div className="preview-eyebrow">{copy.eyebrow}</div>
              <h2>{copy.title}</h2>
              <p>{copy.body}</p>
            </div>
          </div>
        </div>

        <aside className="city-panel" aria-label="Estado del mapa de Manta">
          <div className="panel-topline">
            <div><span className="panel-overline">{mapLabel}</span><h2>{cityName}{active ? <span className="actual-mode"> · {state.modo === 'simulador' ? 'SIMULADOR' : 'JUEGO'}</span> : null}</h2></div>
            <button className="refresh-button" type="button" onClick={() => setRefreshCount((count) => count + 1)} disabled={loading} aria-label="Actualizar estado del panel">
              <span aria-hidden="true">↻</span> ACTUALIZAR
            </button>
          </div>

          <div className="map-stage" aria-label="Mapa de la partida">
            {map && state?.estado === 'activa' ? <CityMap map={map} state={state} selectedSurvivorId={selectedRouteOwner} /> : <MapPlaceholder />}
            <div className={`map-status${panelError ? ' is-error' : ''}`} aria-live="polite">
              <span className={`status-dot is-${connection}`} />
              <span>{panelError ? 'SERVICIO DEL PANEL SIN CONEXIÓN' : `${statusLabel} · ${connectionLabel(connection)}`}</span>
            </div>
            <div className="map-coordinate">{map?.version ?? 'SIN VERSIÓN DE MAPA'}</div>
          </div>

          {active && state.metricas ? (
            <div className="map-metrics" aria-label="Métricas de la instantánea">
              <Metric label="ACTIVOS" value={state.metricas.sobrevivientesActivos} />
              <Metric label="EVACUADOS" value={state.metricas.evacuados} />
              <Metric label="MORDIDOS" value={state.metricas.mordidos} />
              <Metric label="ZOMBIES VISIBLES" value={state.metricas.zombiesVisibles} />
            </div>
          ) : null}

          {active && survivors.length > 0 ? (
            <div className="route-selector">
              <label htmlFor="survivor-route">RUTA PREVISTA</label>
              <select id="survivor-route" value={selectedRouteOwner ?? ''} onChange={(event) => setSelectedSurvivorId(event.target.value)}>
                {survivors.map((survivor) => <option key={survivor.id} value={survivor.id}>{survivor.id}</option>)}
              </select>
              <span>No confirma movimiento ni garantiza seguridad.</span>
            </div>
          ) : null}

          <GameControls
            modeSelected={mode === 'game'}
            state={state}
            map={map}
            connection={connection}
            onJoined={setSelectedSurvivorId}
          />

          <div className="map-legend" aria-label="Leyenda del mapa">
            <span><i className="legend-refuge" /> Refugio</span>
            <span><i className="legend-survivor" /> Sobreviviente</span>
            <span><i className="legend-zombie" /> Zombie visible</span>
            <span><i className="legend-route" /> Ruta prevista</span>
            <span><i className="legend-trail" /> Trayecto confirmado</span>
            <span><i className="legend-closure" /> Cierre</span>
          </div>

          <div className="city-panel-footer">
            <span>{panelError ? panelError : state?.estado === 'sin_partida' ? 'Esperando una partida para mostrar el mapa.' : updatedAt ? `Último snapshot ${updatedAt} · hora del servidor` : 'Esperando el primer snapshot confirmado del servidor.'}</span>
            <span className="north-mark">NO ES UNA GUÍA DE EMERGENCIA</span>
          </div>
        </aside>
      </section>

      <footer className="app-footer">
        <span>NAVIRA <span className="footer-separator">/</span> EVACUACIÓN DINÁMICA</span>
        <span>SIMULACIÓN DE HACKATHON <span className="footer-separator">·</span> SIN GARANTÍA DE SEGURIDAD REAL</span>
      </footer>
    </main>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>
}

function MapPlaceholder() {
  return (
    <div className="map-placeholder" role="img" aria-label="No hay un mapa de partida activo">
      <span className="placeholder-orbit" aria-hidden="true"><span /><span /><span /></span>
      <strong>El mapa aparecerá aquí.</strong>
      <span>Sin datos cartográficos de una partida activa.</span>
    </div>
  )
}

function formatTime(value: string) {
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return 'hora no disponible'
  return new Intl.DateTimeFormat('es-EC', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(date)
}

function connectionLabel(connection: PanelConnection) {
  switch (connection) {
    case 'live': return 'EN VIVO'
    case 'reconnecting': return 'RECONECTANDO'
    case 'stale': return 'DATOS DESACTUALIZADOS'
    default: return 'CONECTANDO'
  }
}
