import { useEffect, useState } from 'react'
import { SimulatorUnavailableError, refugiosParaEnviar, type SimulatorAction, type SimulatorCandidatos, type SimulatorSetup, type SimulatorSpeed, type SimulatorStatus } from '../domain/simulator'
import type { SimulatorPort } from './ports'

const pollIntervalMs = 1800
export const REFUGE_SLOTS = ['R-01', 'R-02', 'R-03', 'R-04'] as const
type Slots = (string | null)[]
const emptySlots = (): Slots => REFUGE_SLOTS.map(() => null)

/** Estado y control del simulador local; `onChanged` avisa tras una orden aceptada (p. ej. refrescar el panel). */
export function useSimulator(port: SimulatorPort, onChanged: () => void) {
  const [status, setStatus] = useState<SimulatorStatus | null>(null)
  const [unavailable, setUnavailable] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [setup, setSetup] = useState<SimulatorSetup>({ escenario: 'mixto', sobrevivientes: 20, intensidad: 'media' })

  const [candidates, setCandidates] = useState<SimulatorCandidatos | null>(null)
  const [slots, setSlots] = useState<Slots>(emptySlots)
  const [placing, setPlacing] = useState<number | null>(null)

  // Los candidatos son estáticos por mapa: una sola carga. Un fallo (p. ej. 404) simplemente oculta el selector.
  useEffect(() => {
    const controller = new AbortController()
    port.getCandidates(controller.signal).then(setCandidates).catch(() => undefined)
    return () => controller.abort()
  }, [port])

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
      const refugios = refugiosParaEnviar(action, slots, REFUGE_SLOTS)
      const next = await port.control(action, action === 'iniciar' || action === 'reiniciar' ? setup : undefined, refugios)
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

  /** Cambia la velocidad en caliente; el backend la conserva también para la siguiente partida. */
  const changeSpeed = async (velocidad: SimulatorSpeed) => {
    try {
      setStatus(await port.setSpeed(velocidad))
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo cambiar la velocidad.')
    }
  }

  /** Sincroniza de inmediato operaciones de Reto externas al puerto de demo libre. */
  const acceptStatus = (next: SimulatorStatus) => {
    setStatus(next)
    setUnavailable(false)
    setMessage(null)
  }

  /** Asigna el nodo a la ranura en modo "colocar" o a la primera libre. Devuelve false si no hay ranura o el nodo ya está usado. */
  const pickNode = (nodo: string): boolean => {
    const target = placing ?? slots.indexOf(null)
    if (target < 0 || slots.some((s, i) => s === nodo && i !== target)) return false
    setSlots(slots.map((s, i) => (i === target ? nodo : s)))
    setPlacing(null)
    return true
  }
  const clearSlot = (index: number) => { setSlots(slots.map((s, i) => (i === index ? null : s))); setPlacing(null) }
  const resetRefuges = () => { setSlots(emptySlots()); setPlacing(null) }

  return { status, unavailable, message, busy, setup, setSetup, run, changeSpeed, acceptStatus, candidates, slots, placing, setPlacing, pickNode, clearSlot, resetRefuges }
}
