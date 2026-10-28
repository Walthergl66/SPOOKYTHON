import { OPERATOR_TOOLS, type OperatorTool } from '../../domain/operator'

interface OperatorControlsProps {
  tool: OperatorTool
  onToolChange: (tool: OperatorTool) => void
  disabled: boolean
  busy: boolean
  canRun: boolean
  canStartNew: boolean
  hasRun: boolean
  runState: 'sin_partida' | 'activa' | 'pausada' | 'finalizada' | 'error' | undefined
  onStart: () => void
  onPause: () => void
  onContinue: () => void
  error: string | null
  notice: string | null
}

export function OperatorControls({ tool, onToolChange, disabled, busy, canRun, canStartNew, hasRun, runState, onStart, onPause, onContinue, error, notice }: OperatorControlsProps) {
  return <section className="operator-controls" aria-labelledby="operator-title">
    <div className="panel-section-heading"><span className="panel-overline">MODO DE OPERADOR</span><h2 id="operator-title">Intervén en el mundo</h2></div>
    <p className="operator-help">Cada mundo nuevo empieza vacío: coloca refugios, habitantes y amenazas donde quieras. El reloj avanza mientras eliges herramientas y haces clic en una intersección o calle.</p>
    {runState === 'activa' ? <button className="sim-action sim-pause" type="button" onClick={onPause} disabled={busy}>Pausar mundo</button>
      : runState === 'pausada' ? <button className="sim-action sim-start" type="button" onClick={onContinue} disabled={busy}>Continuar mundo</button>
        : <button className="sim-action sim-start" type="button" onClick={onStart} disabled={busy || !canRun}>{busy ? 'Preparando mundo…' : 'Iniciar nueva partida'}</button>}
    {hasRun ? <button className="sim-action sim-reset operator-new-game" type="button" onClick={onStart} disabled={busy || !canStartNew}>{busy ? 'Preparando partida…' : 'Iniciar nueva partida'}</button> : null}
    {runState !== 'activa' ? <p className="operator-paused-note">Para colocar elementos, el mundo debe estar en ejecución.</p> : null}
    <div className="operator-tool-grid" role="group" aria-label="Herramientas de operador">
      {OPERATOR_TOOLS.map((item) => <button key={item.id} type="button" className={`operator-tool${tool === item.id ? ' is-selected' : ''}`} aria-pressed={tool === item.id} onClick={() => onToolChange(item.id)} disabled={disabled}>
        <span aria-hidden="true">{item.icon}</span><span>{item.label}</span>
      </button>)}
    </div>
    <p className="operator-tool-hint">{tool === 'incidente' ? 'Haz clic directamente sobre una calle.' : 'Haz clic cerca de una intersección del mapa.'}</p>
    {notice ? <div className="control-notice" role="status">{notice}</div> : null}
    {error ? <div className="control-notice is-error" role="alert">{error}</div> : null}
  </section>
}
