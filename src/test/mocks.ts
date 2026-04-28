import { vi } from 'vitest'
import en from '../i18n/locales/en.json'

const storage: Record<string, string> = {}
Object.defineProperty(globalThis, 'localStorage', {
  value: {
    getItem: (key: string) => storage[key] ?? null,
    setItem: (key: string, value: string) => { storage[key] = value },
    removeItem: (key: string) => { delete storage[key] },
    clear: () => { Object.keys(storage).forEach(k => delete storage[k]) },
  },
  writable: true,
})

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

vi.mock('../lib/firebase', () => ({
  auth: {
    currentUser: null,
    onAuthStateChanged: vi.fn((callback: (user: null) => void) => {
      callback(null)
      return vi.fn()
    }),
  },
  googleProvider: {},
  isEmailLink: vi.fn(() => false),
  sendEmailLink: vi.fn().mockResolvedValue(undefined),
  handleEmailLink: vi.fn().mockRejectedValue(new Error('Email link not mocked')),
  signInWithGoogle: vi.fn().mockRejectedValue(new Error('Google sign-in not mocked')),
  signOut: vi.fn().mockResolvedValue(undefined),
  onAuthChange: vi.fn((callback: (user: null) => void) => {
    callback(null)
    return vi.fn()
  }),
  getIdToken: vi.fn().mockResolvedValue('mock-firebase-token'),
  getCurrentUser: vi.fn(() => null),
  User: {},
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