import { fetchAuthSession } from 'aws-amplify/auth'

export async function getAuthHeader(): Promise<HeadersInit> {
  const headers: HeadersInit = {}
  try {
    const session = await fetchAuthSession()
    const token = session.tokens?.idToken?.toString()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  } catch {
    // No active session - return empty headers
  }
  return headers
}

function normalizeUrl(url: string): string {
  return url.replace(/\/+$/, '')
}

export async function fetchApi(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const authHeaders = await getAuthHeader()
  return fetch(normalizeUrl(url), {
    ...options,
    headers: { ...authHeaders, ...options.headers },
    credentials: 'include',
  })
}

export async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetchApi(url, options)
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const detail = data.detail
    let message: string
    if (Array.isArray(detail)) {
      message = detail.map((e: { msg?: string } | string) => {
        if (typeof e === 'string') return e
        return e.msg || String(e)
      }).join('; ')
    } else if (typeof detail === 'string') {
      message = detail
    } else {
      message = `Request failed: ${response.status}`
    }
    throw new Error(message)
  }
  return response.json()
}