import { useEffect, useMemo, useRef, useState } from 'react'
import {
  activeGameState, buildGameOrder, classifyGameError, createActionId, findPlayer, legalMoves, radioSuggestion as suggestFor, remainingMs as remainingUntil,
  type GameMove, type GameOrderInput, type GameOrderReceipt, type GamePlayer, type PlayerSession,
} from '../domain/game'
import type { PanelMap, PanelState } from '../domain/panel'
import type { GamePort } from './ports'

export type Activity =
  | { kind: 'idle' }
  | { kind: 'recovering' }
  | { kind: 'recovered'; session: PlayerSession }
  | { kind: 'recovery-error'; message: string }
  | { kind: 'session-expired' }
  | { kind: 'joining' }
  | { kind: 'sending' }
  | { kind: 'accepted'; receipt: GameOrderReceipt }
  | { kind: 'error'; message: string; canRetry: boolean }

export interface GameSessionView {
  gameState: PanelState | null
  /** Hay una partida activa (de cualquier modo); distingue "simulador activo" de "sin partida". */
  activeRun: boolean
  session: PlayerSession | null
  player: GamePlayer | undefined
  choices: GameMove[]
  suggestion: { nextNode: string; move: GameMove } | null
  remainingMs: number | null
  turnOpen: boolean
  deadlineClosed: boolean
  busy: boolean
  activity: Activity
  enterGame: () => Promise<void>
  submit: (destination: string) => Promise<void>
  retry: () => Promise<void>
  retryRecovery: () => void
}

interface Options {
  modeSelected: boolean
  state: PanelState | null
  map: PanelMap | null
  /** Debe ser estable entre renders: es dependencia del efecto de recuperación. */
  onJoined: (playerId: string) => void
}

export function useGameSession(port: GamePort, { modeSelected, state, map, onJoined }: Options): GameSessionView {
  const [session, setSession] = useState<PlayerSession | null>(null)
  const [activity, setActivity] = useState<Activity>({ kind: 'idle' })
  const pendingOrder = useRef<GameOrderInput | null>(null)
  const [remainingMs, setRemainingMs] = useState<number | null>(null)
  const [recoveryAttempt, setRecoveryAttempt] = useState(0)

  const gameState = activeGameState(state)
  const player = findPlayer(gameState, session)
  const choices = useMemo(() => legalMoves(gameState, map, player), [gameState, map, player])
  const suggestion = useMemo(() => suggestFor(gameState, player, choices), [gameState, player, choices])

  useEffect(() => {
    const serverRemaining = gameState?.decisionRestanteMs
    if (!modeSelected || serverRemaining === undefined || serverRemaining === null || gameState?.fase !== 'decisiones') {
      setRemainingMs(null)
      return
    }
    const deadlineLocal = performance.now() + serverRemaining
    const refresh = () => setRemainingMs(remainingUntil(deadlineLocal, performance.now()))
    refresh()
    const timer = window.setInterval(refresh, 100)
    return () => window.clearInterval(timer)
  }, [modeSelected, gameState?.decisionRestanteMs, gameState?.fase, gameState?.runId, gameState?.turno, gameState?.snapshotVersion])

  useEffect(() => {
    if (!modeSelected || !gameState) {
      // Sin partida de juego no hay nada que reintentar ni recuperar.
      pendingOrder.current = null
      setActivity((current) => (current.kind === 'idle' ? current : { kind: 'idle' }))
      return
    }
    setSession((current) => (current && current.runId !== gameState.runId ? null : current))
    const controller = new AbortController()
    setActivity({ kind: 'recovering' })
    port.restore(controller.signal)
      .then((restored) => {
        if (controller.signal.aborted) return
        setSession(restored)
        onJoined(restored.playerId)
        setActivity({ kind: 'recovered', session: restored })
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        const kind = classifyGameError(error)
        if (kind === 'missing') {
          setSession(null)
          setActivity({ kind: 'idle' })
          return
        }
        if (kind === 'expired') {
          setSession(null)
          setActivity({ kind: 'session-expired' })
          return
        }
        setActivity({
          kind: 'recovery-error',
          message: error instanceof Error ? error.message : 'No se pudo consultar la sesión guardada.',
        })
      })
    return () => controller.abort()
  }, [port, modeSelected, gameState?.runId, recoveryAttempt, onJoined])

  const turnOpen = gameState?.fase === 'decisiones'
  const deadlineClosed = remainingMs === 0
  const busy = activity.kind === 'recovering' || activity.kind === 'joining' || activity.kind === 'sending'

  const enterGame = async () => {
    setActivity({ kind: 'joining' })
    try {
      const joined = await port.join()
      setSession(joined)
      onJoined(joined.playerId)
      setActivity({ kind: 'idle' })
    } catch (error) {
      if (classifyGameError(error) === 'expired') {
        setSession(null)
        setActivity({ kind: 'session-expired' })
        return
      }
      setActivity({
        kind: 'error',
        message: error instanceof Error ? error.message : 'No se pudo entrar a la partida.',
        canRetry: false,
      })
    }
  }

  const send = async (destination: string, retry: boolean) => {
    if (!gameState || !turnOpen || deadlineClosed || !session || !player) return
    const order = retry && pendingOrder.current ? pendingOrder.current : buildGameOrder(gameState, session.playerId, destination, createActionId())
    if (!order) return
    pendingOrder.current = order
    setActivity({ kind: 'sending' })
    try {
      const receipt = await port.sendOrder(order)
      pendingOrder.current = null
      setActivity({ kind: 'accepted', receipt })
    } catch (error) {
      const kind = classifyGameError(error)
      if (kind === 'expired') {
        pendingOrder.current = null
        setSession(null)
        setActivity({ kind: 'session-expired' })
        return
      }
      const canRetry = kind === 'transient'
      if (!canRetry) pendingOrder.current = null
      setActivity({
        kind: 'error',
        message: error instanceof Error ? error.message : 'No se pudo enviar la orden.',
        canRetry,
      })
    }
  }

  return {
    gameState, activeRun: state?.estado === 'activa', session, player, choices, suggestion, remainingMs, turnOpen, deadlineClosed, busy, activity, enterGame,
    submit: (destination) => send(destination, false),
    retry: () => send(pendingOrder.current?.siguienteNodo ?? '', true),
    retryRecovery: () => setRecoveryAttempt((attempt) => attempt + 1),
  }
}
