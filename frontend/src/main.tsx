import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './app/App'
import './styles.css'

const root = createRoot(document.getElementById('root')!)

async function start() {
  if (import.meta.env.VITE_PUBLIC_DEMO === '1') {
    const response = await fetch('/demo/sesion', { credentials: 'same-origin' })
    if (!response.ok) {
      root.render(<main className="public-demo-unavailable" role="alert">
        <h1>Navira está ocupada</h1>
        <p>{response.status === 429 ? 'En este momento se alcanzó el máximo de partidas simultáneas. Intenta de nuevo en un momento.' : 'No se pudo preparar tu sesión. Comprueba tu conexión e inténtalo de nuevo.'}</p>
        <button type="button" onClick={() => window.location.reload()}>Reintentar</button>
      </main>)
      return
    }
  }

  root.render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}

void start().catch(() => {
  root.render(<main className="public-demo-unavailable" role="alert"><h1>No se pudo iniciar Navira</h1><p>Comprueba tu conexión e inténtalo de nuevo.</p><button type="button" onClick={() => window.location.reload()}>Reintentar</button></main>)
})
