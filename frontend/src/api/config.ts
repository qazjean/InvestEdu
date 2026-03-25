const DEFAULT_DEV_API_BASE_URL = 'http://localhost:8000'

function normalizeBaseUrl(rawUrl: string): string {
  return rawUrl.trim().replace(/\/+$/, '')
}

function resolveApiBaseUrl(): string {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL

  if (configuredUrl && typeof configuredUrl === 'string' && configuredUrl.trim().length > 0) {
    return normalizeBaseUrl(configuredUrl)
  }

  if (import.meta.env.DEV) {
    return DEFAULT_DEV_API_BASE_URL
  }

  // Для production отдаём пустую строку, чтобы использовать относительные /api через reverse proxy.
  return ''
}

export const API_BASE_URL = resolveApiBaseUrl()
