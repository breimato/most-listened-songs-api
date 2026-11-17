let apiBaseUrl = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

export function getApiBaseUrl(): string {
  return apiBaseUrl
}

export async function loadRuntimeConfig(): Promise<void> {
  try {
    const runtimeConfigUrl = `${import.meta.env.BASE_URL}runtime-config.json`
    const response = await fetch(runtimeConfigUrl, { cache: 'no-store' })
    if (!response.ok) {
      return
    }
    const runtimeConfig = (await response.json()) as { apiUrl?: string }
    if (runtimeConfig.apiUrl && runtimeConfig.apiUrl.trim()) {
      apiBaseUrl = runtimeConfig.apiUrl.trim().replace(/\/$/, '')
    }
  } catch {
    // Keep build-time VITE_API_URL / same-origin fallback.
  }
}
