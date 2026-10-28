export const OPERATOR_TOOLS = [
  { id: 'habitante', label: 'Habitante', icon: '●' },
  { id: 'caminante', label: 'Caminante', icon: 'Z' },
  { id: 'corredor', label: 'Corredor', icon: '≫' },
  { id: 'horda', label: 'Horda', icon: '◉' },
  { id: 'dormido', label: 'Dormido', icon: '◌' },
  { id: 'refugio', label: 'Refugio', icon: '⌂' },
  { id: 'incidente', label: 'Incidente', icon: '!' },
] as const

export type OperatorTool = typeof OPERATOR_TOOLS[number]['id']
export type OperatorPlacement = { tipo: OperatorTool; nodo?: string; segmentoId?: string }

