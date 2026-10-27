export interface PanelMap {
  version: string
  nodos: Array<{ id: string; lat: number; lng: number }>
  calles: Array<{ id: string; segmentoId: string; origen: string; destino: string; distanciaM: number; tipo: string }>
  refugios: Array<{ id: string; nodo: string }>
}

export interface PanelState {
  estado: 'sin_partida' | 'activa'
  runId?: string
  modo?: 'simulador' | 'juego'
  turno?: number
  fase?: string
  decisionRestanteMs?: number | null
  mapVersion?: string
  snapshotVersion?: number
  zombies?: Array<{ id: string; tipo: string; nodo: string }>
  movimientosZombies?: Array<{ id: string; trayecto: string[] }>
  sobrevivientes?: Array<{ id: string; nodo: string; estado: string; control: string }>
  rutasPrevistas?: Array<{ sobrevivienteId: string; trayecto: string[] }>
  aristasBloqueadas?: string[]
  segmentosBloqueados?: string[]
  nodosHorda?: string[]
  eventosCiudad?: Array<{ id: string; turno: number; causa: string }>
  metricas?: { sobrevivientesActivos: number; mordidos: number; evacuados: number; zombiesVisibles: number }
}

export interface PanelSnapshot {
  map: PanelMap | null
  state: PanelState
}

export async function loadPanelSnapshot(signal?: AbortSignal): Promise<PanelSnapshot> {
  const stateResponse = await fetch('/panel/estado', { signal, headers: { Accept: 'application/json' } })
  if (!stateResponse.ok) {
    throw new Error('No se pudo obtener el estado del panel.')
  }
  const state = parsePanelState(await stateResponse.json())
  if (state.estado === 'sin_partida') return { map: null, state }

  const mapResponse = await fetch('/panel/mapa', { signal, headers: { Accept: 'application/json' } })
  if (!mapResponse.ok) {
    throw new Error('No se pudo obtener una proyección activa del panel.')
  }

  const map = parsePanelMap(await mapResponse.json())
  if (state.mapVersion !== map.version) {
    throw new Error('La versión del mapa no coincide con el snapshot recibido.')
  }
  return { map, state }
}

export async function loadPanelMap(expectedVersion: string, signal?: AbortSignal): Promise<PanelMap> {
  const response = await fetch('/panel/mapa', { signal, headers: { Accept: 'application/json' } })
  if (!response.ok) throw new Error('No se pudo obtener una proyección activa del panel.')
  const map = parsePanelMap(await response.json())
  if (map.version !== expectedVersion) throw new Error('La versión del mapa no coincide con el snapshot recibido.')
  return map
}

function parsePanelMap(value: unknown): PanelMap {
  if (!isRecord(value) || typeof value.version !== 'string' || !Array.isArray(value.nodos) || !Array.isArray(value.calles) || !Array.isArray(value.refugios)) {
    throw new Error('El servicio devolvió un mapa con un formato no válido.')
  }
  const nodos = value.nodos.map((item) => {
    if (!isRecord(item) || typeof item.id !== 'string' || typeof item.lat !== 'number' || !Number.isFinite(item.lat) || typeof item.lng !== 'number' || !Number.isFinite(item.lng)) {
      throw new Error('El servicio devolvió un nodo con un formato no válido.')
    }
    return { id: item.id, lat: item.lat, lng: item.lng }
  })
  const nodosConocidos = new Set(nodos.map(({ id }) => id))
  const calles = value.calles.map((item) => {
    if (!isRecord(item) || typeof item.id !== 'string' || typeof item.segmentoId !== 'string' || typeof item.origen !== 'string' || typeof item.destino !== 'string' || !nodosConocidos.has(item.origen) || !nodosConocidos.has(item.destino) || typeof item.distanciaM !== 'number' || !Number.isFinite(item.distanciaM) || typeof item.tipo !== 'string') {
      throw new Error('El servicio devolvió una calle con un formato no válido.')
    }
    return { id: item.id, segmentoId: item.segmentoId, origen: item.origen, destino: item.destino, distanciaM: item.distanciaM, tipo: item.tipo }
  })
  const refugios = value.refugios.map((item) => {
    if (!isRecord(item) || typeof item.id !== 'string' || typeof item.nodo !== 'string' || !nodosConocidos.has(item.nodo)) {
      throw new Error('El servicio devolvió un refugio con un formato no válido.')
    }
    return { id: item.id, nodo: item.nodo }
  })
  return { version: value.version, nodos, calles, refugios }
}

export function parsePanelState(value: unknown): PanelState {
  if (!isRecord(value) || (value.estado !== 'sin_partida' && value.estado !== 'activa')) {
    throw new Error('El servicio devolvió un estado del panel no válido.')
  }
  if (value.estado === 'sin_partida') return { estado: 'sin_partida' }

  if (typeof value.runId !== 'string' || (value.modo !== 'simulador' && value.modo !== 'juego') || typeof value.turno !== 'number' || typeof value.fase !== 'string' || typeof value.mapVersion !== 'string' || typeof value.snapshotVersion !== 'number' || !Array.isArray(value.zombies) || !Array.isArray(value.movimientosZombies) || !Array.isArray(value.sobrevivientes) || !Array.isArray(value.rutasPrevistas) || !Array.isArray(value.aristasBloqueadas) || !Array.isArray(value.segmentosBloqueados) || !Array.isArray(value.nodosHorda) || !isRecord(value.metricas)) {
    throw new Error('El servicio devolvió un snapshot incompleto para el panel.')
  }
  if (value.decisionRestanteMs !== undefined && value.decisionRestanteMs !== null && (typeof value.decisionRestanteMs !== 'number' || !Number.isInteger(value.decisionRestanteMs) || value.decisionRestanteMs < 0)) {
    throw new Error('El servicio devolvió el plazo de decisiones con un formato no válido.')
  }
  const { metricas } = value
  if (typeof metricas.sobrevivientesActivos !== 'number' || typeof metricas.mordidos !== 'number' || typeof metricas.evacuados !== 'number' || typeof metricas.zombiesVisibles !== 'number') {
    throw new Error('El servicio devolvió métricas con un formato no válido.')
  }
  const zombies = value.zombies.map((item) => {
    if (!isRecord(item) || typeof item.id !== 'string' || typeof item.tipo !== 'string' || typeof item.nodo !== 'string') throw new Error('El servicio devolvió un zombie con un formato no válido.')
    return { id: item.id, tipo: item.tipo, nodo: item.nodo }
  })
  const sobrevivientes = value.sobrevivientes.map((item) => {
    if (!isRecord(item) || typeof item.id !== 'string' || typeof item.nodo !== 'string' || typeof item.estado !== 'string' || typeof item.control !== 'string') throw new Error('El servicio devolvió un sobreviviente con un formato no válido.')
    return { id: item.id, nodo: item.nodo, estado: item.estado, control: item.control }
  })
  const movimientosZombies = value.movimientosZombies.map((item) => {
    if (!isRecord(item) || typeof item.id !== 'string' || !Array.isArray(item.trayecto) || !item.trayecto.every((node) => typeof node === 'string')) throw new Error('El servicio devolvió un movimiento zombie con un formato no válido.')
    return { id: item.id, trayecto: item.trayecto as string[] }
  })
  const rutasPrevistas = value.rutasPrevistas.map((item) => {
    if (!isRecord(item) || typeof item.sobrevivienteId !== 'string' || !Array.isArray(item.trayecto) || !item.trayecto.every((node: unknown) => typeof node === 'string')) throw new Error('El servicio devolvió una ruta prevista con un formato no válido.')
    return { sobrevivienteId: item.sobrevivienteId, trayecto: item.trayecto as string[] }
  })
  for (const key of ['aristasBloqueadas', 'segmentosBloqueados', 'nodosHorda'] as const) {
    const ids = value[key]
    if (!Array.isArray(ids) || !ids.every((id: unknown) => typeof id === 'string')) throw new Error(`El servicio devolvió ${key} con un formato no válido.`)
  }
  if (!Array.isArray(value.eventosCiudad) || !value.eventosCiudad.every((item) =>
    isRecord(item) && typeof item.id === 'string' && Number.isInteger(item.turno) && typeof item.causa === 'string')) {
    throw new Error('El servicio devolvió eventos de ciudad con un formato no válido.')
  }
  return {
    estado: 'activa',
    runId: value.runId,
    modo: value.modo,
    turno: value.turno,
    fase: value.fase,
    decisionRestanteMs: value.decisionRestanteMs as number | null | undefined,
    mapVersion: value.mapVersion,
    snapshotVersion: value.snapshotVersion,
    zombies,
    movimientosZombies,
    sobrevivientes,
    rutasPrevistas,
    aristasBloqueadas: value.aristasBloqueadas as string[],
    segmentosBloqueados: value.segmentosBloqueados as string[],
    nodosHorda: value.nodosHorda as string[],
    eventosCiudad: value.eventosCiudad as Array<{ id: string; turno: number; causa: string }>,
    metricas: {
      sobrevivientesActivos: metricas.sobrevivientesActivos,
      mordidos: metricas.mordidos,
      evacuados: metricas.evacuados,
      zombiesVisibles: metricas.zombiesVisibles,
    },
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
