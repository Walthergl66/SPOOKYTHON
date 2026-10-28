import { OPERATOR_TOOLS, type OperatorTool } from '../../domain/operator'

interface OperatorControlsProps {
  tool: OperatorTool
  onToolChange: (tool: OperatorTool) => void
  disabled: boolean
  busy: boolean
  canRun: boolean
  runState: 'sin_partida' | 'activa' | 'pausada' | 'finalizada' | 'error' | undefined
  onStart: () => void
  onPause: () => void
  onContinue: () => void
  error: string | null
  notice: string | null
}

export function OperatorControls({ tool, onToolChange, disabled, busy, canRun, runState, onStart, onPause, onContinue, error, notice }: OperatorControlsProps) {
  return <section className="operator-controls" aria-labelledby="operator-title">
    <div className="panel-section-heading"><span className="panel-overline">MODO DE OPERADOR</span><h2 id="operator-title">Intervén en el mundo</h2></div>
    <p className="operator-help">El mundo avanza solo. Elige una herramienta y haz clic en una intersección o calle para colocarla.</p>
    {runState === 'activa' ? <button className="sim-action sim-pause" type="button" onClick={onPause} disabled={busy}>Pausar mundo</button>
      : runState === 'pausada' ? <button className="sim-action sim-start" type="button" onClick={onContinue} disabled={busy}>Continuar mundo</button>
        : <button className="sim-action sim-start" type="button" onClick={onStart} disabled={busy || !canRun}>{busy ? 'Preparando mundo…' : 'Iniciar mundo operador'}</button>}
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
