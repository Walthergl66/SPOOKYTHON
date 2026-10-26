import { useState } from 'react'
import { ModeCard, type NaviraMode } from '../features/mode/ModeCard'
import { BrandMark } from '../shared/ui/BrandMark'

const modeCopy: Record<NaviraMode, { eyebrow: string; title: string; body: string }> = {
  simulator: {
    eyebrow: 'OBSERVACIÓN AUTOMÁTICA',
    title: 'Mira cómo cambia la ciudad.',
    body: 'Sigue las decisiones, las rutas y el avance de una evacuación simulada, turno a turno.',
  },
  game: {
    eyebrow: 'EXPERIENCIA HUMANA',
    title: 'Encuentra tu camino a salvo.',
    body: 'Aparece en un punto de Manta y decide cómo llevar a tu personaje hasta un refugio.',
  },
}

export function App() {
  const [mode, setMode] = useState<NaviraMode>('simulator')
  const copy = modeCopy[mode]

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#inicio" aria-label="Navira, inicio">
          <BrandMark />
          <span className="brand-name">navira</span>
        </a>
        <div className="topbar-context">
          <span className="context-pulse" aria-hidden="true" />
          <span>MANTA, ECUADOR</span>
          <span className="context-divider" aria-hidden="true" />
          <span className="context-label">PLATAFORMA DE EVACUACIÓN</span>
        </div>
        <div className="topbar-version">BETA <span>·</span> 0.1</div>
      </header>

      <section className="welcome-grid" id="inicio" aria-labelledby="welcome-title">
        <div className="welcome-copy">
          <div className="section-kicker"><span>01</span> CENTRO DE CONTROL</div>
          <h1 id="welcome-title">Una ciudad.<br /><em>Dos formas</em> de vivirla.</h1>
          <p className="intro-copy">
            Explora un mundo de evacuación que cambia en cada turno. Observa la simulación o toma el control como sobreviviente.
          </p>

          <div className="mode-heading">
            <span>ELIGE TU EXPERIENCIA</span>
            <span className="heading-rule" aria-hidden="true" />
          </div>
          <div className="mode-list" role="group" aria-label="Modo de Navira">
            <ModeCard mode="simulator" selected={mode === 'simulator'} onSelect={setMode} />
            <ModeCard mode="game" selected={mode === 'game'} onSelect={setMode} />
          </div>

          <div className="mode-preview" aria-live="polite">
            <div className="preview-index">{mode === 'simulator' ? 'A' : 'B'}</div>
            <div>
              <div className="preview-eyebrow">{copy.eyebrow}</div>
              <h2>{copy.title}</h2>
              <p>{copy.body}</p>
            </div>
          </div>
        </div>

        <aside className="city-panel" aria-label="Estado del mapa de Manta">
          <div className="panel-topline">
            <div><span className="panel-overline">VISTA DE CIUDAD</span><h2>Manta <span>·</span> Manabí</h2></div>
            <span className="map-chip">MAPA BASE</span>
          </div>

          <div className="map-stage" aria-label="Vista cartográfica en preparación">
            <svg className="coastline" viewBox="0 0 700 720" role="img" aria-labelledby="map-title map-description" preserveAspectRatio="xMidYMid slice">
              <title id="map-title">Silueta costera de Manta</title>
              <desc id="map-description">Ilustración de referencia; el mapa interactivo aparecerá al iniciar una partida.</desc>
              <path className="sea-shape" d="M0 0h250c-27 62-18 104-47 151-20 33 20 74-5 112-23 37-74 45-54 89 14 31 64 60 39 105-22 38-80 47-70 91 7 32 49 82 17 172H0z" />
              <path className="coast-edge" d="M250 0c-27 62-18 104-47 151-20 33 20 74-5 112-23 37-74 45-54 89 14 31 64 60 39 105-22 38-80 47-70 91 7 32 49 82 17 172" />
              <g className="street-lines" fill="none">
                <path d="M235 34 327 76l22 95 82 27 29 104 105 49" />
                <path d="m206 111 112 16 74 69 94 33 70 73 69 20" />
                <path d="m195 218 113-91 29-51 99-42 98 22 71-26" />
                <path d="m190 282 118-155 87 71-62 105 129 2 65 93 73-27" />
                <path d="m159 352 149-225 25 139 105 12 84 79 94-59 49 64" />
                <path d="m190 457 118-330 25 139-35 124 140-42 84 79 94-59 49 64" />
                <path d="m169 551 139-424 60 229 94-167 84 79 94-59 49 64" />
                <path d="m130 650 178-523 60 229 72 93 144-79 84 79 65-59" />
                <path d="m305 690 3-563 60 229 72 93 144-79 84 79 65-59" />
                <path d="M412 700 308 127l165 55 7 124-107 10 62 113 144-79 44 92" />
                <path d="m513 706-40-524 7 124 95 82-95 48 62 113 82-34" />
                <path d="m638 696-63-308-95 48 62 113 82-34 44 93" />
              </g>
              <g className="district-labels" aria-hidden="true">
                <text x="354" y="101">TARQUI</text><text x="491" y="302">MANTA</text><text x="291" y="512">LOS ESTEROS</text><text x="508" y="602">BARBASQUILLO</text>
              </g>
              <g className="map-pin" transform="translate(459 258)"><circle r="19"/><circle className="pin-core" r="5"/><path d="M0 19v34"/></g>
              <g className="map-pin map-pin-secondary" transform="translate(344 479)"><circle r="14"/><circle className="pin-core" r="4"/><path d="M0 14v27"/></g>
              <text className="map-label" x="480" y="252">MANTA</text>
              <g className="compass" transform="translate(633 73)"><circle r="24"/><path d="M0-15 5 4 0 1-5 4z"/><text x="0" y="-31">N</text></g>
            </svg>
            <div className="map-status"><span className="status-dot" /><span>Sin partida activa</span></div>
            <div className="map-coordinate">0°57′ S&nbsp; 80°43′ O</div>
          </div>

          <div className="city-panel-footer">
            <div><span className="footer-mark">⌁</span><span>El mapa interactivo se activará con una partida.</span></div>
            <span className="north-mark">ECUADOR <b>↓</b></span>
          </div>
        </aside>
      </section>

      <footer className="app-footer">
        <span>NAVIRA <span className="footer-separator">/</span> EVACUACIÓN DINÁMICA</span>
        <span>PROTOTIPO DE SIMULACIÓN <span className="footer-separator">·</span> NO ES UNA GUÍA DE EMERGENCIA</span>
      </footer>
    </main>
  )
}
