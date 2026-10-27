import type { GameOrderInput, GameOrderReceipt, PlayerSession } from '../domain/game'
import type { PanelConnection, PanelCursor, PanelMap, PanelSnapshot, PanelState } from '../domain/panel'
import type { SimulatorAction, SimulatorSetup, SimulatorStatus } from '../domain/simulator'

export interface PanelPort {
  loadSnapshot(signal?: AbortSignal): Promise<PanelSnapshot>
  loadMap(version: string, signal?: AbortSignal): Promise<PanelMap>
  /** Devuelve la función que cierra la suscripción. */
  subscribe(
    onSnapshot: (state: PanelState, cursor: PanelCursor, emittedAt: string) => void,
    onConnection: (state: PanelConnection) => void,
  ): () => void
}

export interface SimulatorPort {
  getStatus(signal?: AbortSignal): Promise<SimulatorStatus>
  control(action: SimulatorAction, setup?: SimulatorSetup): Promise<SimulatorStatus>
}

export interface GamePort {
  join(): Promise<PlayerSession>
  restore(signal?: AbortSignal): Promise<PlayerSession>
  sendOrder(order: GameOrderInput): Promise<GameOrderReceipt>
}
