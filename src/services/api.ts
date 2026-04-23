import { supabase } from '../lib/supabase'

export async function getAuthHeader(): Promise<HeadersInit> {
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token
  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
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
      message = detail.map((e: any) => e.msg || String(e)).join('; ')
    } else if (typeof detail === 'string') {
      message = detail
    } else {
      message = `Request failed: ${response.status}`
    }
    throw new Error(message)
  }
  return response.json()
}