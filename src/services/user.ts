import { supabase } from '../lib/supabase'

const DEBUG = import.meta.env.DEV

function log(level: 'debug' | 'info' | 'warn' | 'error', ...args: unknown[]) {
  if (DEBUG) {
    console[level]('[user service]', ...args)
  }
}

export interface UserProfile {
  id: string
  email: string
  name: string | null
  birth_date: string | null
  country_of_origin: string | null
  created_at: string
  relatives: []
}

export interface UserUpdate {
  name?: string
  birth_date?: string
  country_of_origin?: string
}

async function getAuthHeader(): Promise<HeadersInit> {
  const { data: { session } } = await supabase.auth.getSession()

  const token = session?.access_token
  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
    log('debug', 'Auth: token present')
  } else {
    log('debug', 'Auth: no token')
  }
  return headers
}

export async function getUserProfile(): Promise<UserProfile> {
  log('debug', 'Fetching user profile')
  const authHeaders = await getAuthHeader()
  const response = await fetch('/api/users/me', {
    headers: {
      ...authHeaders,
    },
    credentials: 'include',
  })
  if (!response.ok) {
    log('error', 'Profile fetch failed:', response.status, response.statusText)
    throw new Error('Failed to fetch user profile')
  }
  const data = await response.json()
  log('debug', 'Profile fetched for user:', data.id)
  return data
}

export async function updateUserProfile(data: UserUpdate): Promise<UserProfile> {
  log('debug', 'Updating user profile:', data)
  const authHeaders = await getAuthHeader()
  const response = await fetch('/api/users/me', {
    method: 'PUT',
    headers: {
      ...authHeaders,
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    log('error', 'Profile update failed:', response.status, response.statusText)
    throw new Error('Failed to update user profile')
  }
  const result = await response.json()
  log('debug', 'Profile updated for user:', result.id)
  return result
}

export function isProfileComplete(user: UserProfile): boolean {
  return !!(user.name && user.birth_date && user.country_of_origin)
}