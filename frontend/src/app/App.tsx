import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { GameControls } from '../features/game/GameControls'
import { ModeCard, type NaviraMode } from '../features/mode/ModeCard'
import { RefugeDialog } from '../features/map/RefugeDialog'
import type { PanelConnection } from '../domain/panel'
import { SIMULATOR_SPEEDS, type SimulatorSetup } from '../domain/simulator'
import type { GamePort, PanelPort, SimulatorPort } from '../application/ports'
import { usePanel } from '../application/usePanel'
import { REFUGE_SLOTS, useSimulator } from '../application/useSimulator'
import { useGameSession } from '../application/useGameSession'
import { joinGame, restoreGameSession, sendGameOrder } from '../infrastructure/http/game'
import { loadPanelMap, loadPanelSnapshot } from '../infrastructure/http/panel'
import { controlSimulator, getSimulatorCandidates, getSimulatorStatus, setSimulatorSpeed, startChallengeRound } from '../infrastructure/http/simulator'
import { subscribePanel } from '../infrastructure/realtime/panel'
import { checkHealth } from '../infrastructure/http/health'
import { BrandMark } from '../shared/ui/BrandMark'

// Puertos de módulo: identidad estable entre renders, que los efectos de los hooks usan como dependencia.
const panelPort: PanelPort = { loadSnapshot: loadPanelSnapshot, loadMap: loadPanelMap, subscribe: subscribePanel }
const simulatorPort: SimulatorPort = { getStatus: getSimulatorStatus, getCandidates: getSimulatorCandidates, control: controlSimulator, setSpeed: setSimulatorSpeed }
const gamePort: GamePort = { join: joinGame, restore: restoreGameSession, sendOrder: sendGameOrder }

const RefugePicker = lazy(() => import('../features/map/RefugePicker').then(({ RefugePicker: Component }) => ({ default: Component })))
const CityMap = lazy(() => import('../features/map/CityMap').then(({ CityMap: Component }) => ({ default: Component })))
const SurvivorRoutePanel = lazy(() => import('../features/map/SurvivorRoutePanel').then(({ SurvivorRoutePanel: Component }) => ({ default: Component })))

export function App() {
  const [mode, setMode] = useState<NaviraMode>('simulator')
  const [selectedSurvivorId, setSelectedSurvivorId] = useState<string | undefined>()
  const [challengeRound, setChallengeRound] = useState<1 | 2 | 3>(1)
  const [challengeBusy, setChallengeBusy] = useState(false)
  const [challengeError, setChallengeError] = useState<string | null>(null)
  const [health, setHealth] = useState<'checking' | 'online' | 'offline'>('checking')
  const panel = usePanel(panelPort)
  const { snapshot, connection, loading, error: panelError, eventLog, refresh: refreshPanel } = panel
  const { status: simulator, unavailable: simulatorUnavailable, message: simulatorMessage, busy: simulatorBusy, setup, setSetup, run: runControl, candidates, slots, placing, setPlacing, pickNode, clearSlot, resetRefuges, changeSpeed } = useSimulator(simulatorPort, refreshPanel)

  const game = useGameSession(gamePort, { modeSelected: mode === 'game', state: snapshot?.state ?? null, map: snapshot?.map ?? null, onJoined: setSelectedSurvivorId })

  const [refugeDialogOpen, setRefugeDialogOpen] = useState(false)
  // El selector se ofrece al cargar la página, salvo con una partida activa en curso.
  const openedOnLoad = useRef(false)
  useEffect(() => {
    if (mode === 'challenge') {
      openedOnLoad.current = true
      setRefugeDialogOpen(false)
      return
    }
    if (openedOnLoad.current || candidates === null || simulator === null) return
    openedOnLoad.current = true
    if (simulator.estado !== 'activa') setRefugeDialogOpen(true)
  }, [candidates, simulator, mode])

  useEffect(() => {
    const refreshHealth = () => checkHealth().then((ok) => setHealth(ok ? 'online' : 'offline'))
    void refreshHealth()
    const timer = window.setInterval(refreshHealth, 5000)
    return () => window.clearInterval(timer)
  }, [])

  const state = snapshot?.state ?? null
  const map = snapshot?.map ?? null
  const active = state?.estado === 'activa'
  const cityName = map?.version.includes('manta') ? 'Manta, Manabí' : map ? 'Mapa sintético de prueba' : 'Manta, Ecuador'
  const statusLabel = active ? `Turno ${state.turno} · ${(state.fase ?? 'fase desconocida').replaceAll('_', ' ')}` : state?.estado === 'sin_partida' ? 'Sin partida activa' : loading ? 'Conectando con el panel' : 'Datos no disponibles'
  const allSurvivors = active ? state.sobrevivientes ?? [] : []
  const selectedRouteOwner = allSurvivors.some(({ id }) => id === selectedSurvivorId) ? selectedSurvivorId : undefined
  const simulatorIsRunning = simulator?.estado === 'activa'
  const showPicker = candidates !== null && !simulatorUnavailable
  const pickerLockedReason = simulatorBusy ? 'Se está actualizando la simulación. Espera un momento.' : null
  const placedRefuges = slots.filter((slot) => slot !== null).length
  const confirmRefuges = async () => {
    // Con la partida en curso no se reinicia desde el modal: la selección queda para la siguiente.
    if (!simulatorIsRunning) await runControl(simulator?.runId ? 'reiniciar' : 'iniciar')
    setRefugeDialogOpen(false)
  }
  const startChallenge = async () => {
    setChallengeBusy(true)
    setChallengeError(null)
    try {
      await startChallengeRound(challengeRound)
      await refreshPanel()
    } catch (error) {
      setChallengeError(error instanceof Error ? error.message : 'No se pudo iniciar la ronda del reto.')
    } finally {
      setChallengeBusy(false)
    }
  }

  return (
    <main className="app-shell dashboard-shell">
      <a className="skip-link" href="#main-content">Saltar al contenido</a>
      <header className="topbar dashboard-topbar">
        <a className="brand" href="#main-content" aria-label="Navira, inicio"><BrandMark /><span className="brand-name">navira</span></a>
        <div className="topbar-context"><span className={`context-pulse${simulatorIsRunning ? '' : ' is-idle'}`} aria-hidden="true" /><strong>{simulatorIsRunning ? 'SIMULACIÓN EN VIVO' : 'CENTRO DE SIMULACIÓN'}</strong><span className="context-divider" aria-hidden="true" /><span>{cityName}</span></div>
        <nav className="mode-tabs" aria-label="Modo de Navira" role="group">
          <ModeCard mode="simulator" selected={mode === 'simulator'} onSelect={setMode} />
          <ModeCard mode="challenge" selected={mode === 'challenge'} onSelect={setMode} />
          <ModeCard mode="game" selected={mode === 'game'} onSelect={setMode} />
        </nav>
      </header>

      <section className="dashboard-grid" id="main-content" tabIndex={-1} aria-label="Panel de Navira">
        <aside className="sim-control-panel" aria-labelledby="simulation-control-title">
          <div className="panel-section-heading"><span className="panel-overline">OPERACIÓN LOCAL</span><h1 id="simulation-control-title">Control de simulación</h1></div>
          <div className="control-status" role="status"><span className={`context-pulse${simulatorIsRunning ? '' : ' is-idle'}`} aria-hidden="true" /><span>{simulator?.estado === 'activa' ? 'En curso' : simulator?.estado === 'pausada' ? 'Pausada' : simulator?.estado === 'finalizada' ? 'Finalizada' : simulator?.estado === 'error' ? 'Detenida por error' : 'Lista para iniciar'}</span></div>

          {mode === 'challenge' ? <section className="challenge-setup" aria-labelledby="challenge-title">
            <div className="panel-section-heading"><span className="panel-overline">PRUEBA DE FUEGO · TRACK A</span><h2 id="challenge-title">Selecciona una ronda</h2></div>
            <div className="challenge-rounds" role="group" aria-label="Rondas del reto">
              {([
                { id: 1 as const, name: 'Anochecer', details: '20 sobrevivientes · solo caminantes' },
                { id: 2 as const, name: 'Medianoche', details: '80 sobrevivientes · caminantes, corredores y hordas · 1 puente' },
                { id: 3 as const, name: 'Apocalipsis', details: '200 sobrevivientes · todos los tipos · 2 calles bloqueadas' },
              ]).map((round) => <button key={round.id} type="button" className={`challenge-round${challengeRound === round.id ? ' is-selected' : ''}`} aria-pressed={challengeRound === round.id} onClick={() => setChallengeRound(round.id)} disabled={simulatorIsRunning || challengeBusy}>
                <strong>R{round.id} · {round.name}</strong><span>{round.details}</span>
              </button>)}
            </div>
            <p className="challenge-note">Densidad media provisional. Puente, calles y turnos de evento se sortearán de forma reproducible; el reto no define esos parámetros. Cada ronda se inicia por separado.</p>
            <button className="sim-action sim-start challenge-start" type="button" onClick={() => void startChallenge()} disabled={simulatorBusy || challengeBusy || simulatorIsRunning || simulator?.estado === 'pausada' || simulatorUnavailable}>
              {challengeBusy ? 'Preparando…' : `Iniciar R${challengeRound} · ${challengeRound === 1 ? 'Anochecer' : challengeRound === 2 ? 'Medianoche' : 'Apocalipsis'}`}
            </button>
            {challengeError ? <div className="control-notice is-error" role="alert">{challengeError}</div> : null}
          </section> : <>
          <div className="sim-action-row">
            {simulatorIsRunning ? <button className="sim-action sim-pause" type="button" onClick={() => void runControl('pausar')} disabled={simulatorBusy}>Pausar</button>
              : simulator?.estado === 'pausada' ? <button className="sim-action sim-start" type="button" onClick={() => void runControl('reanudar')} disabled={simulatorBusy}>Continuar</button>
                : <button className="sim-action sim-start" type="button" onClick={() => setRefugeDialogOpen(true)} disabled={simulatorBusy || simulatorUnavailable}>{simulatorBusy ? 'Iniciando…' : 'Iniciar simulación'}</button>}
            <button className="sim-action sim-reset" type="button" onClick={() => simulatorIsRunning ? void runControl('reiniciar') : setRefugeDialogOpen(true)} disabled={simulatorBusy || simulatorUnavailable}>{simulator?.runId ? 'Reiniciar' : 'Nueva partida'}</button>
          </div>

          <div className="speed-row" role="group" aria-label="Velocidad de la simulación">
            <span>Velocidad</span>
            {SIMULATOR_SPEEDS.map((speed) => (
              <button key={speed} className="speed-button" type="button" aria-pressed={simulator?.velocidad === speed} onClick={() => void changeSpeed(speed)} disabled={simulatorBusy || simulatorUnavailable}>{speed}×</button>
            ))}
          </div>

          <label className="setup-field">Escenario
            <select value={setup.escenario} onChange={(event) => setSetup({ ...setup, escenario: event.target.value as SimulatorSetup['escenario'] })} disabled={simulatorIsRunning || simulatorBusy}>
              <option value="libre">Sin amenazas</option><option value="caminantes">Caminantes</option><option value="mixto">Mixto</option><option value="horda">Horda</option>
            </select>
          </label>
          <label className="setup-field">Sobrevivientes iniciales
            <select value={setup.sobrevivientes} onChange={(event) => setSetup({ ...setup, sobrevivientes: Number(event.target.value) })} disabled={simulatorIsRunning || simulatorBusy}>
              <option value={20}>20</option><option value={80}>80</option><option value={200}>200</option>
            </select>
          </label>
          <label className="setup-field">Intensidad sintética de amenazas
            <select value={setup.intensidad} onChange={(event) => setSetup({ ...setup, intensidad: event.target.value as SimulatorSetup['intensidad'] })} disabled={simulatorIsRunning || simulatorBusy}>
              <option value="baja">Baja · 0,2% de nodos elegibles</option><option value="media">Media · 0,5% de nodos elegibles</option><option value="alta">Alta · 0,9% de nodos elegibles</option>
            </select>
          </label>
          </>}
          {mode !== 'challenge' && showPicker ? <div className="refuge-summary"><span role="status">Refugios: {placedRefuges}/{REFUGE_SLOTS.length}</span><button className="sim-action" type="button" onClick={() => setRefugeDialogOpen(true)}>Elegir en el mapa</button></div> : null}

          {simulatorUnavailable ? <div className="control-notice" role="status"><strong>Control local deshabilitado</strong><span>Inicia el backend con <code>NAVIRA_LOCAL_DEMO_CONTROL=1</code> para operar una demo desde esta pantalla.</span></div> : null}
          {simulatorMessage ? <div className="control-notice is-error" role="alert"><strong>No se pudo completar la acción</strong><span>{simulatorMessage}</span></div> : null}
          {simulator?.error ? <div className="control-notice is-error" role="alert"><strong>El reloj se detuvo</strong><span>{simulator.error}</span></div> : null}

          <div className="run-details"><span>Modo de vista</span><strong>{mode === 'challenge' ? `Reto · ronda ${challengeRound}` : mode === 'simulator' ? 'Simulador · demo libre' : 'Juego humano'}</strong><span>Turno observado</span><strong>{state?.turno ?? '—'}</strong><span>Conexión del panel</span><strong>{connectionLabel(connection)}</strong></div>
          {mode === 'game' ? <GameControls modeSelected connection={connection} game={game} /> : null}
          {active && allSurvivors.length > 0 && map ? <Suspense fallback={<div className="survivor-route-loading" role="status">Cargando información del habitante…</div>}><SurvivorRoutePanel state={state} map={map} selectedSurvivorId={selectedRouteOwner} onSelectSurvivor={setSelectedSurvivorId} /></Suspense> : null}
        </aside>

        <section className="city-panel dashboard-map-panel" aria-label="Mapa y estado de Manta">
          <div className="panel-topline">
            <div><span className="panel-overline">{map ? map.version.startsWith('navira-demo') ? 'MUNDO SINTÉTICO' : 'MAPA DE SIMULACIÓN' : 'MAPA EN ESPERA'}</span><h2>{cityName}{active ? <span className="actual-mode"> · {state.modo}</span> : null}</h2></div>
            <button className="refresh-button" type="button" onClick={refreshPanel} disabled={loading}><span aria-hidden="true">↻</span> Actualizar</button>
          </div>
          <div className="map-stage" aria-label="Mapa de la partida">
            {map && state?.estado === 'activa' ? <Suspense fallback={<MapPlaceholder />}><CityMap map={map} state={state} selectedSurvivorId={selectedRouteOwner} onSelectSurvivor={setSelectedSurvivorId} animationSpeed={simulator?.velocidad ?? 4} /></Suspense> : <MapPlaceholder />}
            <div className={`map-status${panelError ? ' is-error' : ''}`} aria-live="polite"><span className={`status-dot is-${connection}`} /><span>{panelError ?? `${statusLabel} · ${connectionLabel(connection)}`}</span></div>
            <div className="map-coordinate">{map?.version ?? (simulatorUnavailable ? 'BACKEND SIN CONTROL LOCAL' : 'AÚN SIN SNAPSHOT')}</div>
          </div>
          <div className="map-legend" aria-label="Leyenda del mapa"><span><i className="legend-refuge" /> Refugio</span><span><i className="legend-survivor" /> Sobreviviente</span><span><i className="legend-zombie" /> Zombie visible</span><span><i className="legend-route" /> Ruta prevista</span><span><i className="legend-trail" /> Movimiento confirmado</span><span><i className="legend-closure" /> Calle cerrada</span></div>
        </section>

        <aside className="stats-column" aria-label="Estadísticas de la partida">
          <section className="stats-panel">
            <div className="panel-section-heading"><span className="panel-overline">DATOS CONFIRMADOS</span><h2>Estado en tiempo real</h2></div>
            <div className="stats-grid">
              <Metric label="Activos" value={state?.metricas?.sobrevivientesActivos} />
              <Metric label="Evacuados" value={state?.metricas?.evacuados} />
              <Metric label="Mordidos acumulados" value={state?.metricas?.mordidos} />
              <Metric label="Mordidos última resolución" value={state?.metricas?.mordidosUltimoTurno} />
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

      <RefugeDialog
        open={refugeDialogOpen}
        title="Elige los refugios de la partida"
        onClose={() => setRefugeDialogOpen(false)}
        footer={<>
          <button className="sim-action sim-start" type="button" onClick={() => void confirmRefuges()} disabled={simulatorBusy || simulatorUnavailable}>{simulatorIsRunning ? 'Usar en la siguiente partida' : simulator?.runId ? 'Reiniciar con estos refugios' : 'Iniciar con estos refugios'}</button>
          <button className="sim-action" type="button" onClick={() => setRefugeDialogOpen(false)}>Cerrar</button>
        </>}
      >
        {simulatorIsRunning ? <p className="refuge-dialog-hint">La partida en curso no cambia. Los refugios elegidos se usarán al reiniciar.</p> : null}
        {candidates ? <Suspense fallback={null}><RefugePicker candidates={candidates} refugeIds={REFUGE_SLOTS} slots={slots} placing={placing} onPick={pickNode} onPlace={setPlacing} onClear={clearSlot} onReset={resetRefuges} lockedReason={pickerLockedReason} /></Suspense> : <p className="empty-note">No hay mapa de refugios disponible con este backend.</p>}
      </RefugeDialog>

      <footer className="system-strip" aria-label="Estado técnico">
        <div><span className={`status-dot is-${health === 'online' ? 'live' : health === 'offline' ? 'stale' : 'connecting'}`} /><span>API</span><strong>{health === 'online' ? 'Disponible' : health === 'offline' ? 'Sin conexión' : 'Comprobando'}</strong></div>
        <div><span className={`status-dot is-${connection}`} /><span>Panel vivo</span><strong>{connectionLabel(connection)}</strong></div>
        <div><span className={`status-dot is-${simulatorIsRunning ? 'live' : 'idle'}`} /><span>Simulador</span><strong>{simulator?.estado ?? (simulatorUnavailable ? 'Control no habilitado' : 'Sin partida')}</strong></div>
      </footer>
    </main>
  )
}

function Metric({ label, value }: { label: string; value?: number | null }) {
  return <div className="metric"><span>{label}</span><strong>{value ?? '—'}</strong></div>
}

function MapPlaceholder() {
  return <div className="map-placeholder" role="img" aria-label="No hay un mapa de partida activo"><span className="placeholder-orbit" aria-hidden="true"><span /><span /><span /></span><strong>Inicia una simulación para cargar el mapa.</strong><span>El panel mostrará únicamente el estado publicado por el servidor.</span></div>
}

function connectionLabel(connection: PanelConnection) {
  switch (connection) {
    case 'live': return 'En vivo'
    case 'reconnecting': return 'Reconectando'
    case 'stale': return 'Datos desactualizados'
    default: return 'Conectando'
  }
}
