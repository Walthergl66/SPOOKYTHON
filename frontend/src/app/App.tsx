import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { GameControls } from '../features/game/GameControls'
import { ModeCard, type NaviraMode } from '../features/mode/ModeCard'
import { loadPanelMap, loadPanelSnapshot, type PanelSnapshot, type PanelState } from '../shared/api/panel'
import { controlSimulator, getSimulatorStatus, SimulatorApiError, type SimulatorSetup, type SimulatorStatus } from '../shared/api/simulator'
import { subscribePanel, type PanelConnection, type PanelCursor } from '../shared/realtime/panel'
import { BrandMark } from '../shared/ui/BrandMark'

const CityMap = lazy(() => import('../features/map/CityMap').then(({ CityMap: Component }) => ({ default: Component })))

type PanelLog = { id: string; label: string; detail: string }

export function App() {
  const [mode, setMode] = useState<NaviraMode>('simulator')
  const [selectedSurvivorId, setSelectedSurvivorId] = useState<string | undefined>()
  const [snapshot, setSnapshot] = useState<PanelSnapshot | null>(null)
  const [panelError, setPanelError] = useState<string | null>(null)
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)
  // Cargar el snapshot HTTP al abrir recupera mapa + estado; WebSocket mantiene los siguientes cambios.
  const [refreshCount, setRefreshCount] = useState(1)
  const [loading, setLoading] = useState(true)
  const [connection, setConnection] = useState<PanelConnection>('connecting')
  const [simulator, setSimulator] = useState<SimulatorStatus | null>(null)
  const [simulatorUnavailable, setSimulatorUnavailable] = useState(false)
  const [simulatorMessage, setSimulatorMessage] = useState<string | null>(null)
  const [simulatorBusy, setSimulatorBusy] = useState(false)
  const [scenario, setScenario] = useState<SimulatorSetup['escenario']>('mixto')
  const [population, setPopulation] = useState(20)
  const [health, setHealth] = useState<'checking' | 'online' | 'offline'>('checking')
  const [eventLog, setEventLog] = useState<PanelLog[]>([])
  const cursorRef = useRef<PanelCursor | null>(null)
  const mapRef = useRef<PanelSnapshot['map']>(null)

  const applyPanelState = useCallback((nextState: PanelState, cursor: PanelCursor, emittedAt: string, nextMap?: PanelSnapshot['map']) => {
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
      setEventLog([])
    } else {
      const matchingMap: PanelSnapshot['map'] = nextMap && nextMap.version === nextState.mapVersion
        ? nextMap
        : mapRef.current?.version === nextState.mapVersion ? mapRef.current : null
      mapRef.current = matchingMap
      setSnapshot({ map: matchingMap, state: nextState })
      const logId = `${nextState.runId}:${nextState.snapshotVersion}`
      const phase = (nextState.fase ?? 'fase desconocida').replaceAll('_', ' ')
      setEventLog((current) => [
        { id: logId, label: `Turno ${nextState.turno} · ${phase}`, detail: `${nextState.metricas?.sobrevivientesActivos ?? 0} personas activas · ${nextState.zombies?.length ?? 0} amenazas visibles` },
        ...current.filter((item) => item.id !== logId),
      ].slice(0, 5))
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
  }, [])

  const refreshPanel = useCallback(() => setRefreshCount((count) => count + 1), [])

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
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [refreshCount, applyPanelState])

  useEffect(() => subscribePanel((nextState, cursor, emittedAt) => {
    applyPanelState(nextState, cursor, emittedAt)
  }, setConnection), [applyPanelState])

  useEffect(() => { mapRef.current = snapshot?.map ?? null }, [snapshot?.map])

  useEffect(() => {
    const controller = new AbortController()
    const refreshControl = () => getSimulatorStatus(controller.signal)
      .then((status) => {
        setSimulator(status)
        setSimulatorUnavailable(false)
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        if (error instanceof SimulatorApiError && error.status === 404) setSimulatorUnavailable(true)
      })
    void refreshControl()
    const timer = window.setInterval(() => void refreshControl(), 1800)
    return () => { controller.abort(); window.clearInterval(timer) }
  }, [])

  useEffect(() => {
    const refreshHealth = () => fetch('/salud', { headers: { Accept: 'application/json' }, cache: 'no-store' })
      .then((response) => setHealth(response.ok ? 'online' : 'offline'))
      .catch(() => setHealth('offline'))
    void refreshHealth()
    const timer = window.setInterval(refreshHealth, 5000)
    return () => window.clearInterval(timer)
  }, [])

  const runControl = async (action: 'iniciar' | 'pausar' | 'reanudar' | 'reiniciar') => {
    setSimulatorBusy(true)
    setSimulatorMessage(null)
    try {
      const status = await controlSimulator(action, action === 'iniciar' || action === 'reiniciar' ? { escenario: scenario, sobrevivientes: population } : undefined)
      setSimulator(status)
      setSimulatorUnavailable(false)
      refreshPanel()
    } catch (error) {
      setSimulatorMessage(error instanceof Error ? error.message : 'No se pudo controlar el simulador.')
      if (error instanceof SimulatorApiError && error.status === 404) setSimulatorUnavailable(true)
    } finally {
      setSimulatorBusy(false)
    }
  }

  const state = snapshot?.state ?? null
  const map = snapshot?.map ?? null
  const active = state?.estado === 'activa'
  const cityName = map?.version.includes('manta') ? 'Manta, Manabí' : map ? 'Mapa sintético de prueba' : 'Manta, Ecuador'
  const statusLabel = active ? `Turno ${state.turno} · ${(state.fase ?? 'fase desconocida').replaceAll('_', ' ')}` : state?.estado === 'sin_partida' ? 'Sin partida activa' : loading ? 'Conectando con el panel' : 'Datos no disponibles'
  const survivors = (active ? state.sobrevivientes : undefined)?.filter(({ estado: survivorState }) => survivorState === 'activo') ?? []
  const selectedRouteOwner = survivors.some(({ id }) => id === selectedSurvivorId) ? selectedSurvivorId : survivors[0]?.id
  const simulatorIsRunning = simulator?.estado === 'activa'

  return (
    <main className="app-shell dashboard-shell">
      <a className="skip-link" href="#main-content">Saltar al contenido</a>
      <header className="topbar dashboard-topbar">
        <a className="brand" href="#main-content" aria-label="Navira, inicio"><BrandMark /><span className="brand-name">navira</span></a>
        <div className="topbar-context"><span className={`context-pulse${simulatorIsRunning ? '' : ' is-idle'}`} aria-hidden="true" /><strong>{simulatorIsRunning ? 'SIMULACIÓN EN VIVO' : 'CENTRO DE SIMULACIÓN'}</strong><span className="context-divider" aria-hidden="true" /><span>{cityName}</span></div>
        <nav className="mode-tabs" aria-label="Modo de Navira" role="group">
          <ModeCard mode="simulator" selected={mode === 'simulator'} onSelect={setMode} />
          <ModeCard mode="game" selected={mode === 'game'} onSelect={setMode} />
        </nav>
      </header>

      <section className="dashboard-grid" id="main-content" tabIndex={-1} aria-label="Panel de Navira">
        <aside className="sim-control-panel" aria-labelledby="simulation-control-title">
          <div className="panel-section-heading"><span className="panel-overline">OPERACIÓN LOCAL</span><h1 id="simulation-control-title">Control de simulación</h1></div>
          <div className="control-status" role="status"><span className={`context-pulse${simulatorIsRunning ? '' : ' is-idle'}`} aria-hidden="true" /><span>{simulator?.estado === 'activa' ? 'En curso' : simulator?.estado === 'pausada' ? 'Pausada' : simulator?.estado === 'finalizada' ? 'Finalizada' : simulator?.estado === 'error' ? 'Detenida por error' : 'Lista para iniciar'}</span></div>

          <div className="sim-action-row">
            {simulatorIsRunning ? <button className="sim-action sim-pause" type="button" onClick={() => void runControl('pausar')} disabled={simulatorBusy}>Pausar</button>
              : simulator?.estado === 'pausada' ? <button className="sim-action sim-start" type="button" onClick={() => void runControl('reanudar')} disabled={simulatorBusy}>Continuar</button>
                : <button className="sim-action sim-start" type="button" onClick={() => void runControl('iniciar')} disabled={simulatorBusy || simulatorUnavailable}>{simulatorBusy ? 'Iniciando…' : 'Iniciar simulación'}</button>}
            <button className="sim-action sim-reset" type="button" onClick={() => void runControl(simulator?.runId ? 'reiniciar' : 'iniciar')} disabled={simulatorBusy || simulatorUnavailable}>{simulator?.runId ? 'Reiniciar' : 'Nueva partida'}</button>
          </div>

          <label className="setup-field">Escenario
            <select value={scenario} onChange={(event) => setScenario(event.target.value as SimulatorSetup['escenario'])} disabled={simulatorIsRunning || simulatorBusy}>
              <option value="libre">Sin amenazas</option><option value="caminantes">Caminantes</option><option value="mixto">Mixto</option><option value="horda">Horda</option>
            </select>
          </label>
          <label className="setup-field">Sobrevivientes iniciales
            <select value={population} onChange={(event) => setPopulation(Number(event.target.value))} disabled={simulatorIsRunning || simulatorBusy}>
              <option value={20}>20</option><option value={80}>80</option><option value={200}>200</option>
            </select>
          </label>

          {simulatorUnavailable ? <div className="control-notice" role="status"><strong>Control local deshabilitado</strong><span>Inicia el backend con <code>NAVIRA_LOCAL_DEMO_CONTROL=1</code> para operar una demo desde esta pantalla.</span></div> : null}
          {simulatorMessage ? <div className="control-notice is-error" role="alert"><strong>No se pudo completar la acción</strong><span>{simulatorMessage}</span></div> : null}
          {simulator?.error ? <div className="control-notice is-error" role="alert"><strong>El reloj se detuvo</strong><span>{simulator.error}</span></div> : null}

          <div className="run-details"><span>Modo de vista</span><strong>{mode === 'simulator' ? 'Simulador automático' : 'Juego humano'}</strong><span>Turno observado</span><strong>{state?.turno ?? '—'}</strong><span>Conexión del panel</span><strong>{connectionLabel(connection)}</strong></div>
          {mode === 'game' ? <GameControls modeSelected state={state} map={map} connection={connection} onJoined={setSelectedSurvivorId} /> : null}
        </aside>

        <section className="city-panel dashboard-map-panel" aria-label="Mapa y estado de Manta">
          <div className="panel-topline">
            <div><span className="panel-overline">{map ? map.version.startsWith('navira-demo') ? 'MUNDO SINTÉTICO' : 'MAPA DE SIMULACIÓN' : 'MAPA EN ESPERA'}</span><h2>{cityName}{active ? <span className="actual-mode"> · {state.modo}</span> : null}</h2></div>
            <button className="refresh-button" type="button" onClick={refreshPanel} disabled={loading}><span aria-hidden="true">↻</span> Actualizar</button>
          </div>
          <div className="map-stage" aria-label="Mapa de la partida">
            {map && state?.estado === 'activa' ? <Suspense fallback={<MapPlaceholder />}><CityMap map={map} state={state} selectedSurvivorId={selectedRouteOwner} /></Suspense> : <MapPlaceholder />}
            <div className={`map-status${panelError ? ' is-error' : ''}`} aria-live="polite"><span className={`status-dot is-${connection}`} /><span>{panelError ?? `${statusLabel} · ${connectionLabel(connection)}`}</span></div>
            <div className="map-coordinate">{map?.version ?? (simulatorUnavailable ? 'BACKEND SIN CONTROL LOCAL' : 'AÚN SIN SNAPSHOT')}</div>
          </div>
          {active && survivors.length > 0 ? <div className="route-selector"><label htmlFor="survivor-route">Ruta observada</label><select id="survivor-route" value={selectedRouteOwner ?? ''} onChange={(event) => setSelectedSurvivorId(event.target.value)}>{survivors.map((survivor) => <option key={survivor.id} value={survivor.id}>{survivor.id}</option>)}</select><span>Ruta calculada desde el snapshot actual; no garantiza seguridad.</span></div> : null}
          <div className="map-legend" aria-label="Leyenda del mapa"><span><i className="legend-refuge" /> Refugio</span><span><i className="legend-survivor" /> Sobreviviente</span><span><i className="legend-zombie" /> Zombie visible</span><span><i className="legend-route" /> Ruta prevista</span><span><i className="legend-trail" /> Movimiento confirmado</span><span><i className="legend-closure" /> Calle cerrada</span></div>
          <div className="city-panel-footer"><span>{panelError ? 'Revisa la conexión del backend.' : updatedAt ? `Snapshot del servidor actualizado a las ${updatedAt}.` : 'El mapa se carga cuando el servidor publica una partida.'}</span><span className="north-mark">DEMO · NO ES GUÍA DE EMERGENCIA</span></div>
        </section>

        <aside className="stats-column" aria-label="Estadísticas de la partida">
          <section className="stats-panel">
            <div className="panel-section-heading"><span className="panel-overline">DATOS CONFIRMADOS</span><h2>Estado en tiempo real</h2></div>
            <div className="stats-grid">
              <Metric label="Activos" value={state?.metricas?.sobrevivientesActivos} />
              <Metric label="Evacuados" value={state?.metricas?.evacuados} />
              <Metric label="Mordidos" value={state?.metricas?.mordidos} />
              <Metric label="Amenazas visibles" value={state?.metricas?.zombiesVisibles} />
              <Metric label="Rutas previstas" value={state?.rutasPrevistas?.length} />
              <Metric label="Turno" value={state?.turno} />
            </div>
          </section>
          <section className="stats-panel refuge-panel">
            <div className="panel-section-heading"><span className="panel-overline">DESTINOS DEL MAPA</span><h2>Refugios representados</h2></div>
            {map?.refugios.length ? <ul className="refuge-list">{map.refugios.map((refuge) => <li key={refuge.id}><span className="refuge-mark" aria-hidden="true">⌂</span><span><strong>{refuge.id}</strong><small>Nodo {refuge.nodo}</small></span></li>)}</ul> : <p className="empty-note">Se mostrarán al iniciar una partida.</p>}
          </section>
          <section className="stats-panel event-panel">
            <div className="panel-section-heading"><span className="panel-overline">SECUENCIA DEL PANEL</span><h2>Últimas actualizaciones</h2></div>
            {eventLog.length ? <ol className="event-list">{eventLog.map((event) => <li key={event.id}><strong>{event.label}</strong><span>{event.detail}</span></li>)}</ol> : <p className="empty-note">El registro aparecerá con los primeros snapshots confirmados.</p>}
          </section>
        </aside>
      </section>

      <footer className="system-strip" aria-label="Estado técnico">
        <div><span className={`status-dot is-${health === 'online' ? 'live' : health === 'offline' ? 'stale' : 'connecting'}`} /><span>API</span><strong>{health === 'online' ? 'Disponible' : health === 'offline' ? 'Sin conexión' : 'Comprobando'}</strong></div>
        <div><span className={`status-dot is-${connection}`} /><span>Panel vivo</span><strong>{connectionLabel(connection)}</strong></div>
        <div><span className={`status-dot is-${simulatorIsRunning ? 'live' : 'idle'}`} /><span>Simulador</span><strong>{simulator?.estado ?? (simulatorUnavailable ? 'Control no habilitado' : 'Sin partida')}</strong></div>
        <div className="system-disclaimer">Fixture parcial de Manta · no acredita seguridad ante sismos · no usar para emergencias reales</div>
      </footer>
    </main>
  )
}

function Metric({ label, value }: { label: string; value?: number }) {
  return <div className="metric"><span>{label}</span><strong>{value ?? '—'}</strong></div>
}

function MapPlaceholder() {
  return <div className="map-placeholder" role="img" aria-label="No hay un mapa de partida activo"><span className="placeholder-orbit" aria-hidden="true"><span /><span /><span /></span><strong>Inicia una simulación para cargar el mapa.</strong><span>El panel mostrará únicamente el estado publicado por el servidor.</span></div>
}

function formatTime(value: string) {
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return 'hora no disponible'
  return new Intl.DateTimeFormat('es-EC', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(date)
}

function connectionLabel(connection: PanelConnection) {
  switch (connection) {
    case 'live': return 'En vivo'
    case 'reconnecting': return 'Reconectando'
    case 'stale': return 'Datos desactualizados'
    default: return 'Conectando'
  }
}
