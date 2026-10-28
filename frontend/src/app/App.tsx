import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import { GameControls } from '../features/game/GameControls'
import { ModeCard, type NaviraMode } from '../features/mode/ModeCard'
import { RefugeDialog } from '../features/map/RefugeDialog'
import type { PanelConnection, PanelRoute } from '../domain/panel'
import type { SimulatorSetup } from '../domain/simulator'
import type { GamePort, PanelPort, SimulatorPort } from '../application/ports'
import { usePanel } from '../application/usePanel'
import { REFUGE_SLOTS, useSimulator } from '../application/useSimulator'
import { useGameSession } from '../application/useGameSession'
import { joinGame, restoreGameSession, sendGameOrder } from '../infrastructure/http/game'
import { loadPanelMap, loadPanelRoute, loadPanelSnapshot } from '../infrastructure/http/panel'
import { controlSimulator, getSimulatorCandidates, getSimulatorStatus, restartChallengeRound, setSimulatorSpeed, startChallengeRound } from '../infrastructure/http/simulator'
import { subscribePanel } from '../infrastructure/realtime/panel'
import { checkHealth } from '../infrastructure/http/health'
import { BrandMark } from '../shared/ui/BrandMark'

// Puertos de módulo: identidad estable entre renders, que los efectos de los hooks usan como dependencia.
const panelPort: PanelPort = { loadSnapshot: loadPanelSnapshot, loadMap: loadPanelMap, loadRoute: loadPanelRoute, subscribe: subscribePanel }
const simulatorPort: SimulatorPort = { getStatus: getSimulatorStatus, getCandidates: getSimulatorCandidates, control: controlSimulator, setSpeed: setSimulatorSpeed }
const gamePort: GamePort = { join: joinGame, restore: restoreGameSession, sendOrder: sendGameOrder }

const RefugePicker = lazy(() => import('../features/map/RefugePicker').then(({ RefugePicker: Component }) => ({ default: Component })))
const CityMap = lazy(() => import('../features/map/CityMap').then(({ CityMap: Component }) => ({ default: Component })))
const SurvivorRoutePanel = lazy(() => import('../features/map/SurvivorRoutePanel').then(({ SurvivorRoutePanel: Component }) => ({ default: Component })))

export function App() {
  const [mode, setMode] = useState<NaviraMode>('challenge')
  const [selectedSurvivorId, setSelectedSurvivorId] = useState<string | undefined>()
  const [selectedRoute, setSelectedRoute] = useState<PanelRoute | null>(null)
  const [selectedRouteLoading, setSelectedRouteLoading] = useState(false)
  const [selectedRouteError, setSelectedRouteError] = useState<string | null>(null)
  const [challengeRound, setChallengeRound] = useState<1 | 2 | 3>(1)
  const [challengeBusy, setChallengeBusy] = useState(false)
  const [challengeError, setChallengeError] = useState<string | null>(null)
  const [health, setHealth] = useState<'checking' | 'online' | 'offline'>('checking')
  const panel = usePanel(panelPort)
  const { snapshot, connection, loading, error: panelError, eventLog, refresh: refreshPanel } = panel
  const { status: simulator, unavailable: simulatorUnavailable, message: simulatorMessage, busy: simulatorBusy, setup, setSetup, run: runControl, candidates, slots, placing, setPlacing, pickNode, clearSlot, resetRefuges, acceptStatus } = useSimulator(simulatorPort, refreshPanel)

  useEffect(() => {
    if (simulator?.rondaReto) setChallengeRound(simulator.rondaReto)
  }, [simulator?.rondaReto])

  const game = useGameSession(gamePort, { modeSelected: mode === 'game', state: snapshot?.state ?? null, map: snapshot?.map ?? null, onJoined: setSelectedSurvivorId })

  const [refugeDialogOpen, setRefugeDialogOpen] = useState(false)
  const [setupStage, setSetupStage] = useState<'refuges' | 'population'>('refuges')

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
  const selectedSurvivor = allSurvivors.find(({ id }) => id === selectedRouteOwner)
  const selectedSnapshotRoute = state?.rutasPrevistas?.find(({ sobrevivienteId }) => sobrevivienteId === selectedRouteOwner)
  const selectedSnapshotRouteKey = selectedSnapshotRoute?.trayecto.join('\u0000')
  useEffect(() => {
    if (!state || !selectedRouteOwner || !selectedSurvivor || selectedSurvivor.estado !== 'activo') {
      setSelectedRouteLoading(false)
      setSelectedRouteError(null)
      return
    }
    if (selectedSnapshotRoute) {
      const route: PanelRoute = {
        runId: state.runId!,
        turno: state.turno!,
        snapshotVersion: state.snapshotVersion!,
        sobrevivienteId: selectedRouteOwner,
        trayecto: selectedSnapshotRoute.trayecto,
      }
      setSelectedRoute((current) => current?.runId === route.runId && current.turno === route.turno && current.sobrevivienteId === route.sobrevivienteId && current.trayecto.join('\u0000') === route.trayecto.join('\u0000') ? current : route)
      setSelectedRouteLoading(false)
      setSelectedRouteError(null)
      return
    }
    // Solo el modo automático solicita una ruta fuera de la fase de decisiones.
    // El resultado se reutiliza durante ese turno; no se recalcula para toda la cohorte.
    if (state.modo !== 'simulador') return
    if (selectedRoute && selectedRoute.runId === state.runId && selectedRoute.turno === state.turno && selectedRoute.sobrevivienteId === selectedRouteOwner) return

    const controller = new AbortController()
    setSelectedRouteLoading(true)
    setSelectedRouteError(null)
    void panelPort.loadRoute(selectedRouteOwner, controller.signal).then((route) => {
      if (route.runId !== state.runId || route.turno !== state.turno || route.sobrevivienteId !== selectedRouteOwner) return
      setSelectedRoute(route)
    }).catch((error: unknown) => {
      if (!controller.signal.aborted) setSelectedRouteError(error instanceof Error ? error.message : 'No se pudo calcular la ruta recomendada.')
    }).finally(() => {
      if (!controller.signal.aborted) setSelectedRouteLoading(false)
    })
    return () => controller.abort()
  }, [state?.runId, state?.turno, state?.modo, selectedRouteOwner, selectedSurvivor?.estado, selectedSnapshotRouteKey, selectedRoute])
  const stateWithSelectedRoute = useMemo(() => {
    if (!state || selectedSurvivor?.estado !== 'activo' || selectedSnapshotRoute || !selectedRoute || selectedRoute.runId !== state.runId || selectedRoute.turno !== state.turno || selectedRoute.sobrevivienteId !== selectedRouteOwner) return state
    return { ...state, rutasPrevistas: [...(state.rutasPrevistas ?? []), { sobrevivienteId: selectedRoute.sobrevivienteId, trayecto: selectedRoute.trayecto }] }
  }, [state, selectedSnapshotRoute, selectedRoute, selectedRouteOwner, selectedSurvivor?.estado])
  const simulatorIsRunning = simulator?.estado === 'activa'
  const pickerLockedReason = simulatorBusy ? 'Se está actualizando la simulación. Espera un momento.' : null
  const placedRefuges = slots.filter((slot) => slot !== null).length
  const confirmRefuges = () => setSetupStage('population')
  const startConfiguredSimulation = async () => {
    const configuredSetup: SimulatorSetup = { ...setup, zombies: setup.zombies ?? 42 }
    await runControl(simulator?.runId ? 'reiniciar' : 'iniciar', configuredSetup)
    setRefugeDialogOpen(false)
  }
  const startChallenge = async () => {
    setChallengeBusy(true)
    setChallengeError(null)
    try {
      acceptStatus(await startChallengeRound(challengeRound))
      await refreshPanel()
    } catch (error) {
      setChallengeError(error instanceof Error ? error.message : 'No se pudo iniciar la ronda del reto.')
    } finally {
      setChallengeBusy(false)
    }
  }
  const restartChallenge = async () => {
    setChallengeBusy(true)
    setChallengeError(null)
    try {
      acceptStatus(await restartChallengeRound())
      await refreshPanel()
    } catch (error) {
      setChallengeError(error instanceof Error ? error.message : 'No se pudo reiniciar la ronda del reto.')
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
          <ModeCard mode="challenge" selected={mode === 'challenge'} onSelect={setMode} />
          <ModeCard mode="simulator" selected={mode === 'simulator'} onSelect={setMode} />
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
            <button className={`sim-action ${simulatorIsRunning ? 'sim-pause' : 'sim-start'} challenge-start`} type="button" onClick={() => simulatorIsRunning && simulator?.rondaReto ? void runControl('pausar') : simulator?.estado === 'pausada' && simulator?.rondaReto ? void runControl('reanudar') : void startChallenge()} disabled={simulatorBusy || challengeBusy || simulatorUnavailable || (simulatorIsRunning && !simulator?.rondaReto) || (simulator?.estado === 'pausada' && !simulator?.rondaReto)}>
              {challengeBusy ? 'Preparando…' : simulatorIsRunning && simulator?.rondaReto ? `Pausar R${simulator.rondaReto}` : simulator?.estado === 'pausada' && simulator?.rondaReto ? `Continuar R${simulator.rondaReto}` : `Iniciar R${challengeRound} · ${challengeRound === 1 ? 'Anochecer' : challengeRound === 2 ? 'Medianoche' : 'Apocalipsis'}`}
            </button>
            {!challengeBusy && simulator?.rondaReto && simulator.runId && simulator?.estado === 'pausada' ? <button className="sim-action sim-start challenge-start" type="button" onClick={() => void startChallenge()} disabled={simulatorBusy || challengeBusy || simulatorUnavailable}>
              {`Nueva simulación R${challengeRound}`}
            </button> : null}
            {!challengeBusy && simulator?.rondaReto && simulator.runId ? <button className="sim-action sim-reset challenge-start" type="button" onClick={() => void restartChallenge()} disabled={simulatorBusy || challengeBusy || simulatorUnavailable}>
              {`Reiniciar R${simulator.rondaReto}`}
            </button> : null}
            {challengeError ? <div className="control-notice is-error" role="alert">{challengeError}</div> : null}
          </section> : mode === 'simulator' ? <section className="simulator-start-panel" aria-label="Iniciar simulador">
            <div className="sim-action-row">
              {simulatorIsRunning ? <button className="sim-action sim-pause" type="button" onClick={() => void runControl('pausar')} disabled={simulatorBusy}>Pausar</button>
                : simulator?.estado === 'pausada' ? <button className="sim-action sim-start" type="button" onClick={() => void runControl('reanudar')} disabled={simulatorBusy}>Continuar</button>
                  : <button className="sim-action sim-start simulator-primary-start" type="button" onClick={() => { setSetupStage('refuges'); setRefugeDialogOpen(true) }} disabled={simulatorBusy || simulatorUnavailable}>{simulatorBusy ? 'Preparando…' : simulator?.runId ? 'Nueva simulación' : 'Iniciar simulación'}</button>}
              {simulator?.runId && (simulatorIsRunning || simulator?.estado === 'pausada') ? <button className="sim-action sim-reset" type="button" onClick={() => { setSetupStage('refuges'); setRefugeDialogOpen(true) }} disabled={simulatorBusy || simulatorUnavailable}>Nueva simulación</button> : null}
            </div>
            <p className="simulator-fixed-speed">Velocidad fija: <strong>4×</strong></p>
            {simulator?.runId ? <p className="simulator-run-population">Población de esta partida: {simulator.sobrevivientesIniciales ?? '—'} habitantes · {simulator.zombiesIniciales ?? '—'} zombies</p> : null}
          </section> : null}

          {simulatorUnavailable ? <div className="control-notice" role="status"><strong>Control local deshabilitado</strong><span>Inicia el backend con <code>NAVIRA_LOCAL_DEMO_CONTROL=1</code> para operar una demo desde esta pantalla.</span></div> : null}
          {simulatorMessage ? <div className="control-notice is-error" role="alert"><strong>No se pudo completar la acción</strong><span>{simulatorMessage}</span></div> : null}
          {simulator?.error ? <div className="control-notice is-error" role="alert"><strong>El reloj se detuvo</strong><span>{simulator.error}</span></div> : null}

          <div className="run-details"><span>Modo de vista</span><strong>{mode === 'challenge' ? `Reto · ronda ${challengeRound}` : mode === 'simulator' ? 'Simulador · demo libre' : 'Juego humano'}</strong><span>Turno observado</span><strong>{state?.turno ?? '—'}</strong><span>Conexión del panel</span><strong>{connectionLabel(connection)}</strong></div>
          {mode === 'game' ? <GameControls modeSelected connection={connection} game={game} /> : null}
          {active && allSurvivors.length > 0 && map ? <Suspense fallback={<div className="survivor-route-loading" role="status">Cargando información del habitante…</div>}><SurvivorRoutePanel state={stateWithSelectedRoute ?? state} map={map} selectedSurvivorId={selectedRouteOwner} onSelectSurvivor={setSelectedSurvivorId} routeLoading={selectedRouteLoading} routeError={selectedRouteError} /></Suspense> : null}
        </aside>

        <section className="city-panel dashboard-map-panel" aria-label="Mapa y estado de Manta">
          <div className="panel-topline">
            <div><span className="panel-overline">{map ? map.version.startsWith('navira-demo') ? 'MUNDO SINTÉTICO' : 'MAPA DE SIMULACIÓN' : 'MAPA EN ESPERA'}</span><h2>{cityName}{active ? <span className="actual-mode"> · {state.modo}</span> : null}</h2></div>
            <button className="refresh-button" type="button" onClick={refreshPanel} disabled={loading}><span aria-hidden="true">↻</span> Actualizar</button>
          </div>
          <div className="map-stage" aria-label="Mapa de la partida">
            {map && state?.estado === 'activa' ? <Suspense fallback={<MapPlaceholder />}><CityMap map={map} state={stateWithSelectedRoute ?? state} selectedSurvivorId={selectedRouteOwner} onSelectSurvivor={setSelectedSurvivorId} animationSpeed={simulator?.velocidad ?? 4} /></Suspense> : <MapPlaceholder />}
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
        title={setupStage === 'refuges' ? 'Paso 1 de 2 · Elige los puntos seguros' : 'Paso 2 de 2 · Configura la población'}
        onClose={() => { setRefugeDialogOpen(false); setSetupStage('refuges') }}
        footer={<>
          {setupStage === 'refuges' ? <button className="sim-action sim-start" type="button" onClick={confirmRefuges} disabled={!candidates || placedRefuges !== REFUGE_SLOTS.length || simulatorBusy || simulatorUnavailable}>Continuar · {placedRefuges}/{REFUGE_SLOTS.length} puntos seguros</button>
            : <><button className="sim-action" type="button" onClick={() => setSetupStage('refuges')}>Volver a puntos seguros</button><button className="sim-action sim-start" type="button" onClick={() => void startConfiguredSimulation()} disabled={simulatorBusy || simulatorUnavailable || !Number.isInteger(setup.sobrevivientes) || setup.sobrevivientes < 1 || setup.sobrevivientes > 200 || !Number.isInteger(setup.zombies ?? 42) || (setup.zombies ?? 42) < 1 || (setup.zombies ?? 42) > 200}>{simulatorBusy ? 'Preparando…' : 'Iniciar simulación · 4×'}</button></>}
          <button className="sim-action" type="button" onClick={() => setRefugeDialogOpen(false)}>Cerrar</button>
        </>}
      >
        {setupStage === 'refuges' ? <>
          {simulatorIsRunning ? <p className="refuge-dialog-hint">La partida en curso no cambia; esta configuración iniciará un mundo nuevo.</p> : null}
          {candidates ? <Suspense fallback={null}><RefugePicker candidates={candidates} refugeIds={REFUGE_SLOTS} slots={slots} placing={placing} onPick={pickNode} onPlace={setPlacing} onClear={clearSlot} onReset={resetRefuges} lockedReason={pickerLockedReason} /></Suspense> : <p className="empty-note">No hay mapa de refugios disponible con este backend.</p>}
        </> : <div className="simulator-population-step">
          <p>Define cuántos personajes empiezan la partida. Los zombies se distribuyen por el mapa con composición mixta y posiciones aleatorias.</p>
          <label className="setup-field">Cantidad de habitantes
            <input type="number" min={1} max={200} step={1} value={setup.sobrevivientes} onChange={(event) => setSetup({ ...setup, sobrevivientes: Number(event.target.value) })} />
          </label>
          <label className="setup-field">Cantidad de zombies
            <input type="number" min={1} max={200} step={1} value={setup.zombies ?? 42} onChange={(event) => setSetup({ ...setup, zombies: Number(event.target.value) })} />
          </label>
          <p className="simulator-fixed-speed">Velocidad fija de la partida: <strong>4×</strong></p>
        </div>}
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
