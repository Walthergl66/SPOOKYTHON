import type { PanelMap, PanelState } from '../../shared/api/panel'

interface CityMapProps {
  map: PanelMap
  state: PanelState
  selectedSurvivorId: string | undefined
}

export function CityMap({ map, state, selectedSurvivorId }: CityMapProps) {
  const longitudes = map.nodos.map((node) => node.lng)
  const latitudes = map.nodos.map((node) => node.lat)
  const minLng = Math.min(...longitudes)
  const maxLng = Math.max(...longitudes)
  const minLat = Math.min(...latitudes)
  const maxLat = Math.max(...latitudes)
  const sizeLng = maxLng - minLng || 1
  const sizeLat = maxLat - minLat || 1
  const pointById = new Map(map.nodos.map((node) => [node.id, {
    x: 42 + ((node.lng - minLng) / sizeLng) * 916,
    y: 42 + ((maxLat - node.lat) / sizeLat) * 616,
  }]))
  const blockedEdges = new Set(state.aristasBloqueadas ?? [])
  const blockedSegments = new Set(state.segmentosBloqueados ?? [])
  const blockedNodes = new Set(state.nodosHorda ?? [])
  const refugeByNode = new Map(map.refugios.map((refuge) => [refuge.nodo, refuge]))
  const streetsBySegment = new Map<string, typeof map.calles>()
  for (const street of map.calles) {
    const segment = streetsBySegment.get(street.segmentoId) ?? []
    segment.push(street)
    streetsBySegment.set(street.segmentoId, segment)
  }

  return (
    <svg className="live-map" viewBox="0 0 1000 700" role="img" aria-labelledby="live-map-title live-map-description">
      <title id="live-map-title">Grafo observable de la partida, mapa {map.version}</title>
      <desc id="live-map-description">Las calles muestran conexiones, los refugios se marcan en verde, los zombies visibles en ámbar y los sobrevivientes en celeste. Las hordas se representan con un halo.</desc>
      <g className="live-streets">
        {[...streetsBySegment.entries()].map(([segmentId, streets]) => {
          const street = streets[0]
          if (!street) return null
          const origin = pointById.get(street.origen)
          const destination = pointById.get(street.destino)
          if (!origin || !destination) return null
          const segmentClosed = blockedSegments.has(segmentId)
          const directionClosures = streets.filter(({ id }) => blockedEdges.has(id)).length
          const allDirectionsClosed = segmentClosed || directionClosures === streets.length
          const someDirectionClosed = !allDirectionsClosed && directionClosures > 0
          return <line key={segmentId} x1={origin.x} y1={origin.y} x2={destination.x} y2={destination.y} className={`street${allDirectionsClosed ? ' is-closed' : ''}${someDirectionClosed ? ' is-direction-closed' : ''}`} />
        })}
      </g>
      <g className="live-intersections" aria-hidden="true">
        {map.nodos.map((node) => {
          const point = pointById.get(node.id)
          return point ? <circle key={node.id} cx={point.x} cy={point.y} r="2" /> : null
        })}
      </g>
      {(state.rutasPrevistas ?? []).filter((route) => route.sobrevivienteId === selectedSurvivorId).map((route) => {
        const points = route.trayecto.map((nodeId) => pointById.get(nodeId)).filter((point) => point !== undefined)
        if (points.length < 2) return null
        return <polyline key={`route-${route.sobrevivienteId}`} className="survivor-route" points={points.map(({ x, y }) => `${x},${y}`).join(' ')}><title>Ruta prevista según el snapshot actual; no garantiza seguridad</title></polyline>
      })}
      {(state.movimientosZombies ?? []).map((movement) => {
        const points = movement.trayecto.map((nodeId) => pointById.get(nodeId)).filter((point) => point !== undefined)
        if (points.length < 2) return null
        return <polyline key={`movement-${movement.id}`} className="zombie-trail" points={points.map(({ x, y }) => `${x},${y}`).join(' ')}><title>Trayecto confirmado de un zombie visible</title></polyline>
      })}
      {[...refugeByNode.entries()].map(([nodeId, refuge]) => {
        const point = pointById.get(nodeId)
        return point ? <g key={refuge.id} className="live-refuge" transform={`translate(${point.x} ${point.y})`}><circle r="11"/><path d="M-5 0h10M0-5v10"/><title>Refugio {refuge.id}</title></g> : null
      })}
      {map.nodos.filter(({ id }) => blockedNodes.has(id)).map((node) => {
        const point = pointById.get(node.id)
        const hordeNode = state.zombies?.some((zombie) => zombie.tipo === 'horda' && zombie.nodo === node.id)
        return point && !hordeNode ? <circle key={`horde-area-${node.id}`} className="horde-neighbor" cx={point.x} cy={point.y} r="5"><title>Nodo bloqueado por vecindad de horda</title></circle> : null
      })}
      {(state.zombies ?? []).filter(({ tipo }) => tipo === 'horda').map((zombie) => {
        const point = pointById.get(zombie.nodo)
        return point ? <circle key={`horde-${zombie.id}`} className="live-horde" cx={point.x} cy={point.y} r="20"><title>Centro y área de horda visible</title></circle> : null
      })}
      {[...(state.zombies ?? [])].map((zombie) => {
        const point = pointById.get(zombie.nodo)
        return point ? <circle key={zombie.id} className="live-zombie" cx={point.x} cy={point.y} r="6"><title>{`Zombie visible: ${zombie.tipo}`}</title></circle> : null
      })}
      {[...(state.sobrevivientes ?? [])].filter(({ estado }) => estado === 'activo').map((survivor) => {
        const point = pointById.get(survivor.nodo)
        return point ? <g key={survivor.id} className="live-survivor" transform={`translate(${point.x} ${point.y})`}><circle r="7"/><circle className="survivor-core" r="2.5"/><title>Sobreviviente activo</title></g> : null
      })}
      <text className="map-north" x="952" y="39">N ↑</text>
      <text className="map-scale" x="38" y="680">{map.nodos.length} NODOS · {map.refugios.length} REFUGIOS</text>
    </svg>
  )
}
