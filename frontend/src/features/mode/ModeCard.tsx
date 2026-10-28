export type NaviraMode = 'simulator' | 'challenge' | 'game'

interface ModeCardProps {
  mode: NaviraMode
  selected: boolean
  onSelect: (mode: NaviraMode) => void
}

const details: Record<NaviraMode, { number: string; title: string; subtitle: string; icon: string }> = {
  simulator: { number: 'B', title: 'Simulador', subtitle: 'Observa la ciudad en movimiento', icon: '◉' },
  challenge: { number: 'A', title: 'Reto', subtitle: 'Prueba de fuego del hackathon', icon: '◈' },
  game: { number: 'C', title: 'Jugar', subtitle: 'Opera el mundo en vivo', icon: '↗' },
}

export function ModeCard({ mode, selected, onSelect }: ModeCardProps) {
  const detail = details[mode]

  return (
    <button
      className={`mode-card${selected ? ' is-selected' : ''}`}
      type="button"
      aria-pressed={selected}
      onClick={() => onSelect(mode)}
    >
      <span className="mode-index">{detail.number}</span>
      <span className="mode-card-content">
        <span className="mode-title">{detail.title}</span>
        <span className="mode-subtitle">{detail.subtitle}</span>
      </span>
      <span className="mode-icon" aria-hidden="true">{detail.icon}</span>
    </button>
  )
}
