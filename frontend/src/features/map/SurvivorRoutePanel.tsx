import type { PanelMap, PanelState } from '../../domain/panel'
import { getSurvivorRouteDetails } from './survivorRoute'

interface SurvivorRoutePanelProps {
  state: PanelState
  map: PanelMap
  selectedSurvivorId: string | undefined
  onSelectSurvivor: (survivorId: string) => void
  routeLoading?: boolean
  routeError?: string | null
}

/** Presents the selected inhabitant and the route in the current server snapshot. */
export function SurvivorRoutePanel({ state, map, selectedSurvivorId, onSelectSurvivor, routeLoading = false, routeError = null }: SurvivorRoutePanelProps) {
  const survivors = state.sobrevivientes ?? []
  const details = getSurvivorRouteDetails(state, map, selectedSurvivorId)
  const survivor = details?.survivor
  const path = details?.path ?? []

  return (
    <section className="survivor-route-panel" aria-label="Información del habitante seleccionado y su ruta" aria-live="polite">
      {survivor ? <>
        <div className="survivor-route-heading">
          <div><span className="panel-overline">HABITANTE SELECCIONADO</span><h3>{survivor.id}</h3></div>
          <span className={`survivor-state is-${survivor.estado}`}>{survivor.estado.replaceAll('_', ' ')}</span>
        </div>
        <div className="survivor-route-facts">
          <div><span>Control</span><strong>{survivor.control === 'humano' ? 'Jugador' : 'Automático'}</strong></div>
          <div><span>Nodo actual</span><strong>{survivor.nodo}</strong></div>
          <div><span>Siguiente paso</span><strong>{details?.nextNode ?? (details?.destination ? 'En refugio' : 'Sin ruta')}</strong></div>
          <div><span>Destino</span><strong>{details?.destination ?? 'Sin ruta disponible'}</strong></div>
        </div>
        {path.length > 0 ? <div className="survivor-route-path">
          <span>Ruta recomendada · {Math.max(0, path.length - 1)} pasos</span>
          <p>{compactPath(path).map((node, index) => <span key={`${node}-${index}`}>{index > 0 ? <b aria-hidden="true">›</b> : null}{node}</span>)}</p>
          {path.length > 6 ? <details>
            <summary>Ver recorrido completo ({path.length} nodos)</summary>
            <ol>{path.map((node, index) => <li key={`${node}-${index}`}>{node}</li>)}</ol>
          </details> : null}
        </div> : <p className="survivor-route-empty" role={routeError ? 'alert' : routeLoading ? 'status' : undefined}>{routeLoading ? 'Calculando ruta recomendada…' : routeError ?? (survivor.estado === 'activo' ? 'El servidor no ofrece una ruta para este snapshot.' : 'Este habitante ya no tiene una ruta activa.')}</p>}
      </> : <div className="survivor-route-hint"><span className="panel-overline">SEGUIMIENTO DE HABITANTES</span><strong>Selecciona un habitante en el mapa</strong><span>Verás su estado, posición y ruta recomendada actual.</span></div>}

      <details className="survivor-list-fallback">
        <summary>Elegir habitante de la lista</summary>
        <div>{survivors.map((item) => <button
          key={item.id}
          type="button"
          className={item.id === selectedSurvivorId ? 'is-selected' : ''}
          onClick={() => onSelectSurvivor(item.id)}
        >
          <span>{item.id}</span><small>{item.estado.replaceAll('_', ' ')}</small>
        </button>)}</div>
      </details>
    </section>
  )
}

function compactPath(path: string[]): string[] {
  return path.length > 6 ? [...path.slice(0, 5), '…', path[path.length - 1]] : path
}
