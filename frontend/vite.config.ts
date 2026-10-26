import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const backend = loadEnv(mode, '.', 'NAVIRA_').NAVIRA_API_TARGET || 'http://127.0.0.1:8000'
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/salud': backend,
        '/panel': backend,
        '/juego': backend,
        '/demo': backend,
        '/ws': { target: backend.replace(/^http/, 'ws'), ws: true },
      },
    },
  }
})
