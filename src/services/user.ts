import { fetchJson } from './api'

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
  preferred_language?: string
  created_at: string
  relatives: []
}

export interface UserUpdate {
  name?: string
  birth_date?: string
  country_of_origin?: string
}

export async function getUserProfile(): Promise<UserProfile> {
  log('debug', 'Fetching user profile')
  const data = await fetchJson<UserProfile>('/api/users/me')
  log('debug', 'Profile fetched for user:', data.id)
  return data
}

export async function updateUserProfile(data: UserUpdate): Promise<UserProfile> {
  log('debug', 'Updating user profile:', data)
  const result = await fetchJson<UserProfile>('/api/users/me', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  log('debug', 'Profile updated for user:', result.id)
  return result
}

export async function updatePreferredLanguage(language: string): Promise<UserProfile> {
  log('debug', 'Updating preferred language:', language)
  const result = await fetchJson<UserProfile>('/api/users/me/language', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preferred_language: language }),
  })
  log('debug', 'Language updated to:', language)
  return result
}

export function isProfileComplete(user: UserProfile): boolean {
  return !!(user.name && user.birth_date && user.country_of_origin)
}
