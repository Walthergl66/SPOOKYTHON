import type { PanelState } from '../../domain/panel'

interface SurvivorRoutePanelProps {
  state: PanelState
  selectedSurvivorId: string | undefined
}

/** Shows only the fictional identity of the inhabitant selected on the map. */
export function SurvivorRoutePanel({ state, selectedSurvivorId }: SurvivorRoutePanelProps) {
  const survivor = state.sobrevivientes?.find((item) => item.id === selectedSurvivorId)
  const profile = survivor?.perfilNarrativo

  if (!profile) return null

  return (
    <section className="survivor-route-panel" aria-label="Datos ficticios del habitante seleccionado" aria-live="polite">
      <article className="survivor-narrative-profile" aria-label="Perfil ficticio">
        <span className="panel-overline">DATOS FICTICIOS</span>
        <div><strong>{profile.nombre}</strong><span>{profile.edad} años · {profile.ocupacion}</span></div>
        <p>{profile.descripcion}</p>
      </article>
    </section>
  )
}
