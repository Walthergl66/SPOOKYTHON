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
  eventosCiudad?: Array<{ id: string; turno: number; causa: string; segmentoId?: string; lat?: number; lng?: number }>
  metricas?: { sobrevivientesActivos: number; mordidos: number; mordidosUltimoTurno: number | null; evacuados: number; zombiesVisibles: number }
}

export interface PanelSnapshot {
  map: PanelMap | null
  state: PanelState
}

export type PanelConnection = 'connecting' | 'live' | 'reconnecting' | 'stale'
export type PanelCursor = { runId: string | null; sequence: number }

export type PanelLog = { id: string; label: string; detail: string }

/** 'stale': secuencia anterior del mismo run; 'same': repetida; 'new': primera o de otro run. */
export function classifyCursor(previous: PanelCursor | null, next: PanelCursor): 'stale' | 'same' | 'new' {
  if (previous?.runId !== next.runId) return 'new'
  if (next.sequence < previous.sequence) return 'stale'
  return next.sequence === previous.sequence ? 'same' : 'new'
}

/** Devuelve el mapa solo si coincide con la versión del estado; si no, el cacheado con esa versión, o null. */
export function pickMap(nextMap: PanelMap | null | undefined, cached: PanelMap | null, version: string | undefined): PanelMap | null {
  return nextMap && nextMap.version === version ? nextMap : cached?.version === version ? cached : null
}

/** Añade al registro los incidentes y el turno del snapshot (más reciente primero), sin duplicados, máximo 5. */
export function nextPanelLog(current: PanelLog[], state: PanelState): PanelLog[] {
  const logId = `${state.runId}:${state.snapshotVersion}`
  const phase = (state.fase ?? 'fase desconocida').replaceAll('_', ' ')
  const incidentes = (state.eventosCiudad ?? []).map((evento) => ({
    id: `${state.runId}:${evento.id}`,
    label: `Incidente vial · Turno ${evento.turno}`,
    detail: `${evento.causa}; el cierre ya fue aplicado.`,
  }))
  return [
    ...incidentes,
    { id: logId, label: `Turno ${state.turno} · ${phase}`, detail: `${state.metricas?.sobrevivientesActivos ?? 0} personas activas · ${state.zombies?.length ?? 0} amenazas visibles` },
    ...current.filter((item) => item.id !== logId && !incidentes.some((evento) => evento.id === item.id)),
  ].slice(0, 5)
}

export function parsePanelMap(value: unknown): PanelMap {
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
  const conteos = [metricas.sobrevivientesActivos, metricas.mordidos, metricas.evacuados, metricas.zombiesVisibles]
  const mordidosUltimoTurno = metricas.mordidosUltimoTurno
  if (!conteos.every((count) => typeof count === 'number' && Number.isInteger(count) && count >= 0)
    || (mordidosUltimoTurno !== undefined && mordidosUltimoTurno !== null
      && (typeof mordidosUltimoTurno !== 'number' || !Number.isInteger(mordidosUltimoTurno) || mordidosUltimoTurno < 0))) {
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
  const eventosCiudadValidos = Array.isArray(value.eventosCiudad) && value.eventosCiudad.every((item) =>
    isRecord(item) && typeof item.id === 'string' && Number.isInteger(item.turno) && typeof item.causa === 'string'
    && ((item.lat === undefined && item.lng === undefined && item.segmentoId === undefined)
      || (typeof item.segmentoId === 'string' && typeof item.lat === 'number' && Number.isFinite(item.lat)
        && typeof item.lng === 'number' && Number.isFinite(item.lng))))
  if (!eventosCiudadValidos) {
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
    eventosCiudad: value.eventosCiudad as Array<{ id: string; turno: number; causa: string; segmentoId?: string; lat?: number; lng?: number }>,
    metricas: {
      sobrevivientesActivos: metricas.sobrevivientesActivos as number,
      mordidos: metricas.mordidos as number,
      mordidosUltimoTurno: typeof mordidosUltimoTurno === 'number' ? mordidosUltimoTurno : null,
      evacuados: metricas.evacuados as number,
      zombiesVisibles: metricas.zombiesVisibles as number,
    },
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
