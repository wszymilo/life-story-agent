import { vi } from 'vitest'

export const mockSupabase = {
  auth: {
    signInWithOtp: vi.fn().mockResolvedValue({ data: {}, error: null }),
    signOut: vi.fn().mockResolvedValue({ data: {}, error: null }),
    getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
    onAuthStateChange: vi.fn().mockImplementation((callback) => {
      callback('SIGNED_OUT', null)
      return { data: { subscription: { unsubscribe: vi.fn() } } }
    }),
  },
}

vi.mock('@supabase/supabase-js', () => ({
  createClient: vi.fn(() => mockSupabase),
}))