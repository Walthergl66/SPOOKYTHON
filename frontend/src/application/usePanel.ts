import { useCallback, useEffect, useRef, useState } from 'react'
import { classifyCursor, nextPanelLog, pickMap, type PanelConnection, type PanelCursor, type PanelLog, type PanelSnapshot, type PanelState } from '../domain/panel'
import type { PanelPort } from './ports'

/** Mantiene la última proyección válida del servidor: carga HTTP inicial/manual y snapshots por WebSocket. */
export function usePanel(port: PanelPort) {
  const [snapshot, setSnapshot] = useState<PanelSnapshot | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)
  // Cargar el snapshot HTTP al abrir recupera mapa + estado; WebSocket mantiene los siguientes cambios.
  const [refreshCount, setRefreshCount] = useState(1)
  const [loading, setLoading] = useState(true)
  const [connection, setConnection] = useState<PanelConnection>('connecting')
  const [eventLog, setEventLog] = useState<PanelLog[]>([])
  const cursorRef = useRef<PanelCursor | null>(null)
  const mapRef = useRef<PanelSnapshot['map']>(null)

  const applyPanelState = useCallback((nextState: PanelState, cursor: PanelCursor, emittedAt: string, nextMap?: PanelSnapshot['map']) => {
    const kind = classifyCursor(cursorRef.current, cursor)
    if (kind === 'stale') return
    if (kind === 'same') {
      if (nextState.estado === 'activa' && nextMap && nextMap.version === nextState.mapVersion) {
        mapRef.current = nextMap
        setSnapshot((current) => current?.state.estado === 'activa' && current.state.runId === nextState.runId
          ? { map: nextMap, state: current.state }
          : current)
      }
      setError(null)
      setLoading(false)
      setUpdatedAt(emittedAt)
      return
    }
    cursorRef.current = cursor

    if (nextState.estado === 'sin_partida') {
      // El snapshot queda vacío, pero la geometría inmutable puede reutilizarse
      // cuando el usuario inicie otra partida con la misma versión de mapa.
      setSnapshot({ map: null, state: nextState })
      setEventLog([])
    } else {
      const matchingMap = pickMap(nextMap, mapRef.current, nextState.mapVersion)
      mapRef.current = matchingMap
      setSnapshot({ map: matchingMap, state: nextState })
      setEventLog((current) => nextPanelLog(current, nextState))
      if (!matchingMap) {
        const mapVersion = nextState.mapVersion
        const runId = nextState.runId
        if (!mapVersion || !runId) return
        port.loadMap(mapVersion)
          .then((loadedMap) => {
            const currentCursor = cursorRef.current
            if (!currentCursor || currentCursor.runId !== runId || currentCursor.sequence < (nextState.snapshotVersion ?? 0)) return
            mapRef.current = loadedMap
            setSnapshot((current) => current?.state.estado === 'activa' && current.state.mapVersion === loadedMap.version
              ? { map: loadedMap, state: current.state }
              : current)
          })
          .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'No se pudo cargar el mapa de la partida.'))
      }
    }
    setError(null)
    setLoading(false)
    setUpdatedAt(emittedAt)
  }, [port])

  const refresh = useCallback(() => setRefreshCount((count) => count + 1), [])

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    port.loadSnapshot(controller.signal)
      .then((nextSnapshot) => {
        const { state: nextState, map: nextMap } = nextSnapshot
        const cursor = nextState.estado === 'activa'
          ? { runId: nextState.runId ?? null, sequence: nextState.snapshotVersion ?? 0 }
          : { runId: null, sequence: 0 }
        applyPanelState(nextState, cursor, new Date().toISOString(), nextMap)
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === 'AbortError') return
        setError(reason instanceof Error ? reason.message : 'El panel no está disponible.')
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [refreshCount, applyPanelState, port])

  // La limpieza cierra el socket y sus temporizadores; StrictMode monta y desmonta el efecto una vez.
  useEffect(() => port.subscribe((nextState, cursor, emittedAt) => {
    applyPanelState(nextState, cursor, emittedAt)
  }, setConnection), [applyPanelState, port])

  useEffect(() => { if (snapshot?.map) mapRef.current = snapshot.map }, [snapshot?.map])

  return { snapshot, connection, loading, error, updatedAt, eventLog, refresh }
}
