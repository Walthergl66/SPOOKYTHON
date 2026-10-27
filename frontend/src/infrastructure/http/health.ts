/** Sondeo de disponibilidad de la API; un fallo de red cuenta como no disponible. */
export function checkHealth(): Promise<boolean> {
  return fetch('/salud', { headers: { Accept: 'application/json' }, cache: 'no-store' })
    .then((response) => response.ok)
    .catch(() => false)
}
