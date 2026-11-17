const STORAGE_KEY = 'scrobbles:access-key'

let currentKey = ''
const unauthorizedListeners = new Set<() => void>()

export function getAccessKey(): string {
  return currentKey
}

export function setAccessKey(key: string): void {
  currentKey = key
}

export function readStoredAccessKey(): string {
  try {
    return (
      localStorage.getItem(STORAGE_KEY) ??
      sessionStorage.getItem(STORAGE_KEY) ??
      ''
    )
  } catch {
    return ''
  }
}

export function persistAccessKey(key: string, remember: boolean): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
    sessionStorage.removeItem(STORAGE_KEY)
    ;(remember ? localStorage : sessionStorage).setItem(STORAGE_KEY, key)
  } catch {
    // Sin almacenamiento: la llave vive solo en memoria.
  }
  currentKey = key
}

export function clearStoredAccessKey(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // Nada que limpiar.
  }
  currentKey = ''
}

export function subscribeUnauthorized(listener: () => void): () => void {
  unauthorizedListeners.add(listener)
  return () => {
    unauthorizedListeners.delete(listener)
  }
}

export function notifyUnauthorized(): void {
  for (const listener of unauthorizedListeners) listener()
}
