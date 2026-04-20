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

export async function fetchApi(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const authHeaders = await getAuthHeader()
  return fetch(url, {
    ...options,
    headers: { ...authHeaders, ...options.headers },
    credentials: 'include',
  })
}