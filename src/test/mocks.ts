import { vi } from 'vitest'

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

vi.mock('@supabase/supabase-js', () => ({
  createClient: vi.fn(() => mockSupabase),
}))