import type { PanelConnection } from '../../domain/panel'
import type { GameSessionView } from '../../application/useGameSession'

export type { GameSessionView }

interface GameControlsProps {
  modeSelected: boolean
  connection: PanelConnection
  game: GameSessionView
}

export function GameControls({ modeSelected, connection, game }: GameControlsProps) {
  if (!modeSelected) return null

  const { gameState, session, player, choices, suggestion: radioSuggestion, remainingMs: remaining, turnOpen, deadlineClosed, busy, activity, enterGame, submit, retry, retryRecovery } = game
  const isGame = gameState !== null
  const panelFresh = connection === 'live'

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
          <strong>{game.activeRun ? 'La partida activa es un simulador.' : 'No hay una partida de juego activa.'}</strong>
          <span>El servicio todavía debe iniciar y habilitar una partida en modo juego.</span>
        </div>
      ) : !session ? (
        <div className="game-entry">
          <p aria-live="polite">{activity.kind === 'session-expired' ? 'La sesión venció por inactividad. Esta partida conserva el cupo y personaje anteriores; espera la próxima partida para volver a entrar.' : 'Entra con una sesión temporal. El servidor elige tu punto inicial y guarda la cookie fuera de JavaScript.'}</p>
          <button className="game-primary" type="button" onClick={enterGame} disabled={busy || !panelFresh || activity.kind === 'session-expired'}>
            {activity.kind === 'recovering' ? 'Comprobando sesión…' : activity.kind === 'joining' ? 'Entrando…' : activity.kind === 'session-expired' ? 'Sesión vencida' : 'Entrar a la partida'}
          </button>
          {activity.kind === 'recovery-error' ? <button type="button" className="game-retry" onClick={retryRecovery}>Reintentar recuperación</button> : null}
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
          {turnOpen && remaining !== null ? <>
            <p className="game-clock" aria-live="off">{deadlineClosed ? 'Tiempo agotado; esperando la resolución del servidor.' : `Cierre del servidor en ${(remaining / 1000).toFixed(1)} s`}</p>
            <span className="sr-only" aria-live="polite">{deadlineClosed ? 'La ventana de decisiones terminó.' : remaining <= 500 ? 'Queda menos de medio segundo para enviar una orden.' : ''}</span>
          </> : null}
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
        {activity.kind === 'error' ? <><strong>No se pudo confirmar la orden.</strong><span>{activity.message}</span>{activity.canRetry ? <button type="button" className="game-retry" onClick={() => void retry()}>Reintentar con la misma acción</button> : null}</> : null}
      </div>
    </section>
  )
}
