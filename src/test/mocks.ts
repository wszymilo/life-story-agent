import { vi } from 'vitest'
import en from '../i18n/locales/en.json'

const mockSession = {
  access_token: 'mock-token-123',
  refresh_token: 'mock-refresh-token',
  expires_in: 3600,
  expires_at: Date.now() + 3600000,
}

export const mockSupabase = {
  auth: {
    signInWithOtp: vi.fn().mockResolvedValue({ data: {}, error: null }),
    signOut: vi.fn().mockResolvedValue({ data: {}, error: null }),
    getSession: vi.fn().mockResolvedValue({ data: { session: mockSession }, error: null }),
    onAuthStateChange: vi.fn().mockImplementation((callback) => {
      callback('SIGNED_OUT', null)
      return { data: { subscription: { unsubscribe: vi.fn() } } }
    }),
  },
}

function getTranslation(key: string, options?: Record<string, unknown>): string {
  const keys = key.split('.')
  let value: unknown = en
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = (value as Record<string, unknown>)[k]
    } else {
      return key
    }
  }
  if (typeof value === 'string') {
    if (options) {
      return value.replace(/\{\{(\w+)\}\}/g, (_, varName) => String(options[varName] ?? `{{${varName}}}`))
    }
    return value
  }
  return key
}

vi.mock('@supabase/supabase-js', () => ({
  createClient: vi.fn(() => mockSupabase),
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: getTranslation,
    i18n: {
      language: 'en',
      changeLanguage: vi.fn(),
      t: getTranslation,
    },
  }),
  initReactI18next: {
    type: '3rdParty',
    init: vi.fn(),
  },
}))