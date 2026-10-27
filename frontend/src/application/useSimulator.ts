import { useEffect, useState } from 'react'
import { SimulatorUnavailableError, type SimulatorAction, type SimulatorSetup, type SimulatorStatus } from '../domain/simulator'
import type { SimulatorPort } from './ports'

const pollIntervalMs = 1800

/** Estado y control del simulador local; `onChanged` avisa tras una orden aceptada (p. ej. refrescar el panel). */
export function useSimulator(port: SimulatorPort, onChanged: () => void) {
  const [status, setStatus] = useState<SimulatorStatus | null>(null)
  const [unavailable, setUnavailable] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [setup, setSetup] = useState<SimulatorSetup>({ escenario: 'mixto', sobrevivientes: 20, intensidad: 'media', eventosCiudad: true })

  useEffect(() => {
    const controller = new AbortController()
    const refreshControl = () => port.getStatus(controller.signal)
      .then((next) => {
        setStatus(next)
        setUnavailable(false)
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        if (error instanceof SimulatorUnavailableError) setUnavailable(true)
      })
    void refreshControl()
    const timer = window.setInterval(() => void refreshControl(), pollIntervalMs)
    return () => { controller.abort(); window.clearInterval(timer) }
  }, [port])

  const run = async (action: SimulatorAction) => {
    setBusy(true)
    setMessage(null)
    try {
      const next = await port.control(action, action === 'iniciar' || action === 'reiniciar' ? setup : undefined)
      setStatus(next)
      setUnavailable(false)
      onChanged()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo controlar el simulador.')
      if (error instanceof SimulatorUnavailableError) setUnavailable(true)
    } finally {
      setBusy(false)
    }
  }

  return { status, unavailable, message, busy, setup, setSetup, run }
}
