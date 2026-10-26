import { useEffect, useMemo, useRef, useState } from 'react'
import type { PanelMap, PanelState } from '../../shared/api/panel'
import { GameApiError, joinGame, restoreGameSession, sendGameOrder, type GameOrderInput, type GameOrderReceipt, type PlayerSession } from '../../shared/api/game'
import type { PanelConnection } from '../../shared/realtime/panel'

interface GameControlsProps {
  modeSelected: boolean
  state: PanelState | null
  map: PanelMap | null
  connection: PanelConnection
  onJoined: (playerId: string) => void
}

type Activity =
  | { kind: 'idle' }
  | { kind: 'recovering' }
  | { kind: 'recovered'; session: PlayerSession }
  | { kind: 'recovery-error'; message: string }
  | { kind: 'joining' }
  | { kind: 'sending' }
  | { kind: 'accepted'; receipt: GameOrderReceipt }
  | { kind: 'error'; message: string; canRetry: boolean }

export function GameControls({ modeSelected, state, map, connection, onJoined }: GameControlsProps) {
  const [session, setSession] = useState<PlayerSession | null>(null)
  const [activity, setActivity] = useState<Activity>({ kind: 'idle' })
  const pendingOrder = useRef<GameOrderInput | null>(null)
  const [remainingMs, setRemainingMs] = useState<number | null>(null)
  const [recoveryAttempt, setRecoveryAttempt] = useState(0)

  const gameState = state?.estado === 'activa' && state.modo === 'juego' ? state : null
  const player = gameState && session && session.runId === gameState.runId
    ? gameState.sobrevivientes?.find(({ id }) => id === session.playerId)
    : undefined
  const choices = useMemo(() => {
    if (!gameState || !map || !player) return []
    const closedEdges = new Set(gameState.aristasBloqueadas ?? [])
    const closedSegments = new Set(gameState.segmentosBloqueados ?? [])
    const blockedNodes = new Set(gameState.nodosHorda ?? [])
    const zombieNodes = new Set((gameState.zombies ?? []).map(({ nodo }) => nodo))
    const byNode = new Map<string, PanelMap['calles'][number]>()
    for (const street of map.calles) {
      if (street.origen !== player.nodo || closedEdges.has(street.id) || closedSegments.has(street.segmentoId)) continue
      if (blockedNodes.has(street.destino) || byNode.has(street.destino)) continue
      byNode.set(street.destino, street)
    }
    return [...byNode.entries()].map(([node, street]) => ({ node, street, risk: zombieNodes.has(node) }))
  }, [gameState, map, player])
  const radioSuggestion = useMemo(() => {
    if (!gameState || !player || gameState.fase !== 'decisiones') return null
    const route = gameState.rutasPrevistas?.find(({ sobrevivienteId }) => sobrevivienteId === player.id)?.trayecto
    if (!route || route[0] !== player.nodo || route.length < 2) return null
    const nextNode = route[1]
    const move = choices.find(({ node }) => node === nextNode)
    return move ? { nextNode, move } : null
  }, [gameState, player, choices])

  useEffect(() => {
    const serverRemaining = gameState?.decisionRestanteMs
    if (serverRemaining === undefined || serverRemaining === null || gameState?.fase !== 'decisiones') {
      setRemainingMs(null)
      return
    }
    const deadlineLocal = performance.now() + serverRemaining
    const refresh = () => setRemainingMs(Math.max(0, Math.ceil(deadlineLocal - performance.now())))
    refresh()
    const timer = window.setInterval(refresh, 100)
    return () => window.clearInterval(timer)
  }, [gameState?.decisionRestanteMs, gameState?.fase, gameState?.runId, gameState?.turno, gameState?.snapshotVersion])

  useEffect(() => {
    if (!modeSelected || !gameState) return
    const controller = new AbortController()
    setActivity({ kind: 'recovering' })
    restoreGameSession(controller.signal)
      .then((restored) => {
        setSession(restored)
        onJoined(restored.playerId)
        setActivity({ kind: 'recovered', session: restored })
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        if (error instanceof GameApiError && error.status === 403) {
          setActivity({ kind: 'idle' })
          return
        }
        setActivity({
          kind: 'recovery-error',
          message: error instanceof Error ? error.message : 'No se pudo consultar la sesión guardada.',
        })
      })
    return () => controller.abort()
  }, [modeSelected, gameState?.runId, recoveryAttempt, onJoined])

  if (!modeSelected) return null

  const isGame = gameState !== null
  const turnOpen = gameState?.fase === 'decisiones'
  const deadlineClosed = remainingMs === 0
  const panelFresh = connection === 'live'
  const busy = activity.kind === 'recovering' || activity.kind === 'joining' || activity.kind === 'sending'

  const enterGame = async () => {
    setActivity({ kind: 'joining' })
    try {
      const joined = await joinGame()
      setSession(joined)
      onJoined(joined.playerId)
      setActivity({ kind: 'idle' })
    } catch (error) {
      setActivity({
        kind: 'error',
        message: error instanceof Error ? error.message : 'No se pudo entrar a la partida.',
        canRetry: false,
      })
    }
  }

  const submit = async (destination: string, retry = false) => {
    if (!gameState || !turnOpen || deadlineClosed || !session || !player || !gameState.runId || gameState.turno === undefined) return
    const order = retry && pendingOrder.current ? pendingOrder.current : {
      runId: gameState.runId,
      turno: gameState.turno,
      personajeId: session.playerId,
      siguienteNodo: destination,
      accionId: createActionId(),
    }
    pendingOrder.current = order
    setActivity({ kind: 'sending' })
    try {
      const receipt = await sendGameOrder(order)
      pendingOrder.current = null
      setActivity({ kind: 'accepted', receipt })
    } catch (error) {
      const status = error instanceof GameApiError ? error.status : 0
      const canRetry = status === 0 || status >= 500
      if (!canRetry) pendingOrder.current = null
      setActivity({
        kind: 'error',
        message: error instanceof Error ? error.message : 'No se pudo enviar la orden.',
        canRetry,
      })
    }
  }

  return (
    <section className="game-controls" aria-labelledby="game-controls-title">
      <div className="game-controls-heading">
        <div>
          <span className="game-kicker">Modo humano</span>
          <h2 id="game-controls-title">Tu siguiente paso</h2>
        </div>
        {gameState && gameState.turno !== undefined ? <span className="game-turn">Turno {gameState.turno}</span> : null}
      </div>

      {!isGame ? (
        <div className="game-empty" role="status">
          <strong>{state?.estado === 'activa' ? 'La partida activa es un simulador.' : 'No hay una partida de juego activa.'}</strong>
          <span>El servicio todavía debe iniciar y habilitar una partida en modo juego.</span>
        </div>
      ) : !session ? (
        <div className="game-entry">
          <p>Entra con una sesión temporal. El servidor elige tu punto inicial y guarda la cookie fuera de JavaScript.</p>
          <button className="game-primary" type="button" onClick={enterGame} disabled={busy || !panelFresh}>
            {activity.kind === 'recovering' ? 'Comprobando sesión…' : activity.kind === 'joining' ? 'Entrando…' : 'Entrar a la partida'}
          </button>
          {activity.kind === 'recovery-error' ? <button type="button" className="game-retry" onClick={() => setRecoveryAttempt((attempt) => attempt + 1)}>Reintentar recuperación</button> : null}
          {!panelFresh ? <span className="game-hint">Esperando una conexión reciente con el servidor.</span> : null}
        </div>
      ) : session.runId !== gameState?.runId ? (
        <div className="game-empty" role="status">
          <strong>Tu sesión pertenece a otra partida.</strong>
          <span>Este servidor aún no ofrece transferencia ni cierre de sesión para cambiar de partida.</span>
        </div>
      ) : !player ? (
        <div className="game-empty" role="status">
          <strong>Esperando un punto de aparición.</strong>
          <span>El personaje solo entra antes del movimiento zombie de un turno.</span>
        </div>
      ) : player.estado !== 'activo' ? (
        <div className="game-outcome" role="status">
          <strong>{player.estado === 'evacuado' ? 'Llegaste a un refugio.' : 'Tu personaje ya no puede continuar.'}</strong>
          <span>{player.estado === 'evacuado' ? 'La evacuación está confirmada por el servidor.' : 'Consulta el mapa para ver el resultado confirmado.'}</span>
        </div>
      ) : (
        <>
          <div className="game-position"><span>Tu posición</span><strong>{player.nodo}</strong><span>{turnOpen ? 'Elige un vecino o espera.' : 'Los zombies se movieron; espera la siguiente fase de decisiones.'}</span></div>
          {turnOpen && remainingMs !== null ? <p className="game-clock" aria-live="off">{deadlineClosed ? 'Tiempo agotado; esperando la resolución del servidor.' : `Cierre del servidor en ${(remainingMs / 1000).toFixed(1)} s`}</p> : null}
          {turnOpen ? (
            <aside className="game-radio" aria-labelledby="game-radio-title">
              <div>
                <span className="game-kicker">Canal de apoyo</span>
                <h3 id="game-radio-title">Radio Navira</h3>
              </div>
              {radioSuggestion ? (
                <>
                  <p>Sugerencia del servidor para este snapshot: avanzar a <strong>{radioSuggestion.nextNode}</strong> por {radioSuggestion.move.street.tipo}, {Math.round(radioSuggestion.move.street.distanciaM)} m.</p>
                  <button type="button" className="game-radio-action" onClick={() => void submit(radioSuggestion.nextNode)} disabled={deadlineClosed || busy || !panelFresh}>
                    Usar sugerencia
                  </button>
                </>
              ) : <p>El servidor no tiene un siguiente paso disponible en la ruta prevista de este snapshot. Puedes esperar o elegir una calle abierta.</p>}
              <small>Es una sugerencia basada en información visible, no una garantía de seguridad. Tú decides si la envías.</small>
            </aside>
          ) : null}
          <fieldset className="game-moves" disabled={!turnOpen || deadlineClosed || busy || !panelFresh}>
            <legend>Calles disponibles</legend>
            <div className="game-move-list">
              <button type="button" className="game-move game-wait" onClick={() => void submit(player.nodo)}>
                <span><strong>Esperar</strong><small>Conservar la posición este turno</small></span>
                <span aria-hidden="true">↺</span>
              </button>
              {choices.map(({ node, street, risk }) => (
                <button key={node} type="button" className="game-move" onClick={() => void submit(node)}>
                  <span><strong>{node}</strong><small>{street.tipo} · {Math.round(street.distanciaM)} m{risk ? ' · zombie visible' : ''}</small></span>
                  <span aria-hidden="true">{risk ? '!' : '↗'}</span>
                </button>
              ))}
              {choices.length === 0 ? <p className="game-no-moves">No hay calles abiertas disponibles; puedes esperar.</p> : null}
            </div>
          </fieldset>
          {!turnOpen || deadlineClosed ? <p className="game-hint">Las órdenes solo se aceptan hasta el cierre indicado por el servidor.</p> : null}
          {!panelFresh ? <p className="game-hint">La vista está reconectando; los controles se desactivaron hasta recibir un snapshot reciente.</p> : null}
        </>
      )}

      <div className={`game-feedback${activity.kind === 'error' ? ' is-error' : ''}`} aria-live="polite" role="status">
        {activity.kind === 'recovered' ? <><strong>Sesión recuperada</strong><span>{activity.session.lastOrder ? `Última orden recibida: turno ${activity.session.lastOrder.turn}, destino ${activity.session.lastOrder.destination}. La posición actual se toma del snapshot del servidor.` : 'Tu personaje se recuperó desde la cookie y el snapshot actual del servidor.'}</span></> : null}
        {activity.kind === 'recovery-error' ? <><strong>No se pudo recuperar la sesión guardada.</strong><span>{activity.message}</span></> : null}
        {activity.kind === 'accepted' ? <><strong>Orden recibida · #{activity.receipt.secuencia}</strong><span>El movimiento se confirmará cuando el servidor resuelva el turno {activity.receipt.turno}.</span></> : null}
        {activity.kind === 'error' ? <><strong>No se pudo confirmar la orden.</strong><span>{activity.message}</span>{activity.canRetry && pendingOrder.current ? <button type="button" className="game-retry" onClick={() => void submit(pendingOrder.current?.siguienteNodo ?? '', true)}>Reintentar con la misma acción</button> : null}</> : null}
      </div>
    </section>
  )
}

function createActionId() {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const bytes = new Uint8Array(16)
  crypto.getRandomValues(bytes)
  return [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}
