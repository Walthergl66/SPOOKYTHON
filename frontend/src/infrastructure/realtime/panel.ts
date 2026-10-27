import { parsePanelState, type PanelState, type PanelConnection, type PanelCursor } from '../../domain/panel'

interface PanelSnapshotEvent {
  schemaVersion: 1
  tipo: 'panel.snapshot'
  runId: string | null
  secuencia: number
  emitidoEn: string
  datos: PanelState
}

interface PanelHeartbeatEvent {
  schemaVersion: 1
  tipo: 'panel.latido'
  runId: string | null
  secuencia: number
  emitidoEn: string
}

const heartbeatTimeoutMs = 7_000
const maximumReconnectDelayMs = 8_000

/** Mantiene un canal de snapshots completos; no aplica deltas ni permite órdenes. */
export function subscribePanel(
  onSnapshot: (state: PanelState, cursor: PanelCursor, emittedAt: string) => void,
  onConnection: (state: PanelConnection) => void,
): () => void {
  let stopped = false
  let socket: WebSocket | null = null
  let retryTimer: number | undefined
  let staleTimer: number | undefined
  let reconnectAttempt = 0
  let lastMessageAt = 0
  let hasConnected = false

  const connect = () => {
    if (stopped) return
    onConnection(hasConnected ? 'reconnecting' : 'connecting')
    const scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    socket = new WebSocket(`${scheme}//${window.location.host}/ws/panel`)

    socket.onopen = () => {
      hasConnected = true
      reconnectAttempt = 0
      lastMessageAt = Date.now()
      onConnection('live')
      window.clearInterval(staleTimer)
      staleTimer = window.setInterval(() => {
        if (!stopped && Date.now() - lastMessageAt > heartbeatTimeoutMs) onConnection('stale')
      }, 1_000)
    }

    socket.onmessage = (message) => {
      try {
        const evento = parseEvent(JSON.parse(String(message.data)))
        if (evento.tipo === 'panel.latido') {
          lastMessageAt = Date.now()
          onConnection('live')
          return
        }
        const state = parsePanelState(evento.datos)
        if (state.estado === 'activa' && (state.runId !== evento.runId || state.snapshotVersion !== evento.secuencia)) {
          throw new Error('El cursor no coincide con el snapshot del panel.')
        }
        if (state.estado === 'sin_partida' && (evento.runId !== null || evento.secuencia !== 0)) {
          throw new Error('El cursor de sin_partida no es válido.')
        }
        lastMessageAt = Date.now()
        onConnection('live')
        onSnapshot(state, { runId: evento.runId, sequence: evento.secuencia }, evento.emitidoEn)
      } catch {
        // Un mensaje mal formado no reemplaza la última proyección válida.
      }
    }

    socket.onclose = () => {
      if (stopped) return
      onConnection('reconnecting')
      window.clearInterval(staleTimer)
      const delay = Math.min(500 * (2 ** reconnectAttempt), maximumReconnectDelayMs)
      reconnectAttempt += 1
      retryTimer = window.setTimeout(connect, delay)
    }
    socket.onerror = () => socket?.close()
  }

  connect()
  return () => {
    stopped = true
    window.clearTimeout(retryTimer)
    window.clearInterval(staleTimer)
    socket?.close()
  }
}

function parseEvent(value: unknown): PanelSnapshotEvent | PanelHeartbeatEvent {
  if (!isRecord(value) || value.schemaVersion !== 1 || typeof value.emitidoEn !== 'string' || !Number.isInteger(value.secuencia) || Number(value.secuencia) < 0 || (value.runId !== null && typeof value.runId !== 'string')) {
    throw new Error('Evento del panel inválido.')
  }
  if (value.tipo === 'panel.snapshot') {
    return {
      schemaVersion: 1,
      tipo: value.tipo,
      runId: value.runId,
      secuencia: value.secuencia as number,
      emitidoEn: value.emitidoEn,
      datos: value.datos as PanelState,
    }
  }
  if (value.tipo === 'panel.latido') {
    return {
      schemaVersion: 1,
      tipo: value.tipo,
      runId: value.runId,
      secuencia: value.secuencia as number,
      emitidoEn: value.emitidoEn,
    }
  }
  throw new Error('Tipo de evento del panel desconocido.')
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
