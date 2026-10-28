import type { GameOrderInput, GameOrderReceipt, PlayerSession } from '../domain/game'
import type { PanelConnection, PanelCursor, PanelMap, PanelRoute, PanelSnapshot, PanelState } from '../domain/panel'
import type { RefugioAsignado, SimulatorAction, SimulatorCandidatos, SimulatorSetup, SimulatorSpeed, SimulatorStatus } from '../domain/simulator'

export interface PanelPort {
  loadSnapshot(signal?: AbortSignal): Promise<PanelSnapshot>
  loadMap(version: string, signal?: AbortSignal): Promise<PanelMap>
  loadRoute(survivorId: string, signal?: AbortSignal): Promise<PanelRoute>
  /** Devuelve la función que cierra la suscripción. */
  subscribe(
    onSnapshot: (state: PanelState, cursor: PanelCursor, emittedAt: string) => void,
    onConnection: (state: PanelConnection) => void,
  ): () => void
}

export interface SimulatorPort {
  getStatus(signal?: AbortSignal): Promise<SimulatorStatus>
  getCandidates(signal?: AbortSignal): Promise<SimulatorCandidatos>
  control(action: SimulatorAction, setup?: SimulatorSetup, refugios?: RefugioAsignado[]): Promise<SimulatorStatus>
  setSpeed(velocidad: SimulatorSpeed): Promise<SimulatorStatus>
}

export interface GamePort {
  join(): Promise<PlayerSession>
  restore(signal?: AbortSignal): Promise<PlayerSession>
  sendOrder(order: GameOrderInput): Promise<GameOrderReceipt>
}
