/** Factores de velocidad que ofrece el panel; el backend acepta exactamente estos valores. */
export type SimulatorSpeed = 1 | 2 | 4
export const SIMULATOR_SPEEDS: readonly SimulatorSpeed[] = [1, 2, 4]

export type SimulatorStatus = {
  habilitado: true
  estado: 'sin_partida' | 'activa' | 'pausada' | 'finalizada' | 'error'
  runId: string | null
  turno: number | null
  escenario: string | null
  sobrevivientesIniciales: number | null
  intensidad: 'baja' | 'media' | 'alta' | null
  eventosCiudad: boolean | null
  velocidad: SimulatorSpeed
  error: string | null
}

export type SimulatorSetup = {
  escenario: 'libre' | 'caminantes' | 'mixto' | 'horda'
  sobrevivientes: number
  intensidad: 'baja' | 'media' | 'alta'
  eventosCiudad: boolean
  semilla?: number
}

export type CandidatoNodo = { id: string; lat: number; lng: number }
export type CandidatoCalle = { origen: string; destino: string }
export type RefugioAsignado = { id: string; nodo: string }
/** Refugios a enviar: solo al iniciar o reiniciar y con todos los slots colocados; si no, undefined (mapa por defecto). */
export function refugiosParaEnviar(action: SimulatorAction, slots: (string | null)[], ids: readonly string[]): RefugioAsignado[] | undefined {
  if ((action !== 'iniciar' && action !== 'reiniciar') || slots.length !== ids.length || !slots.every((nodo) => nodo !== null)) return undefined
  return ids.map((id, i) => ({ id, nodo: slots[i] as string }))
}

export type SimulatorCandidatos = { version: string; nodos: CandidatoNodo[]; calles: CandidatoCalle[]; refugios: RefugioAsignado[] }

/** El backend no expone el control local de demo (HTTP 404). */
export class SimulatorUnavailableError extends Error {}

export type SimulatorAction = 'iniciar' | 'pausar' | 'reanudar' | 'reiniciar'

export function parseSimulatorStatus(value: unknown): SimulatorStatus {
  if (!isRecord(value) || value.habilitado !== true ||
    !['sin_partida', 'activa', 'pausada', 'finalizada', 'error'].includes(String(value.estado)) ||
    !(typeof value.runId === 'string' || value.runId === null) ||
    !(typeof value.turno === 'number' || value.turno === null) ||
    !(typeof value.escenario === 'string' || value.escenario === null) ||
    !(typeof value.sobrevivientesIniciales === 'number' || value.sobrevivientesIniciales === null) ||
    !(value.intensidad === 'baja' || value.intensidad === 'media' || value.intensidad === 'alta' || value.intensidad === null) ||
    !(typeof value.eventosCiudad === 'boolean' || value.eventosCiudad === null) ||
    !(value.velocidad === 1 || value.velocidad === 2 || value.velocidad === 4) ||
    !(typeof value.error === 'string' || value.error === null)) {
    throw new Error('El backend devolvió un estado de simulador incompleto.')
  }
  return {
    habilitado: true,
    estado: value.estado as SimulatorStatus['estado'],
    runId: value.runId,
    turno: value.turno,
    escenario: value.escenario,
    sobrevivientesIniciales: value.sobrevivientesIniciales,
    intensidad: value.intensidad,
    eventosCiudad: value.eventosCiudad,
    velocidad: value.velocidad,
    error: value.error,
  }
}

export function parseSimulatorCandidatos(value: unknown): SimulatorCandidatos {
  const invalid = () => new Error('El backend devolvió candidatos de refugio incompletos.')
  if (!isRecord(value) || typeof value.version !== 'string' || !Array.isArray(value.nodos) || !Array.isArray(value.calles) || !Array.isArray(value.refugios)) throw invalid()
  const nodos = value.nodos.map((n): CandidatoNodo => {
    if (!isRecord(n) || typeof n.id !== 'string' || !Number.isFinite(n.lat) || !Number.isFinite(n.lng)) throw invalid()
    return { id: n.id, lat: n.lat as number, lng: n.lng as number }
  })
  const calles = value.calles.map((c): CandidatoCalle => {
    if (!isRecord(c) || typeof c.origen !== 'string' || typeof c.destino !== 'string') throw invalid()
    return { origen: c.origen, destino: c.destino }
  })
  const refugios = value.refugios.map((r): RefugioAsignado => {
    if (!isRecord(r) || typeof r.id !== 'string' || typeof r.nodo !== 'string') throw invalid()
    return { id: r.id, nodo: r.nodo }
  })
  return { version: value.version, nodos, calles, refugios }
}

/** Nodo más cercano al punto dentro de `maxMetros` (equirectangular, suficiente a escala urbana) o null. */
export function nodoMasCercano(punto: { lat: number; lng: number }, nodos: CandidatoNodo[], maxMetros = 150): CandidatoNodo | null {
  const mPorGrado = 111_320
  const cosLat = Math.cos((punto.lat * Math.PI) / 180)
  let mejor: CandidatoNodo | null = null
  let mejorDist = maxMetros
  for (const nodo of nodos) {
    const d = Math.hypot((nodo.lat - punto.lat) * mPorGrado, (nodo.lng - punto.lng) * mPorGrado * cosLat)
    if (d <= mejorDist) { mejor = nodo; mejorDist = d }
  }
  return mejor
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
