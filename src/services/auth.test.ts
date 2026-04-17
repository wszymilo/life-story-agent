import { describe, it, expect, vi, beforeEach } from 'vitest'
import { signInWithMagicLink, signOut } from './auth'
import { mockSupabase } from '../test/mocks'

describe('auth service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('signInWithMagicLink', () => {
    it('returns success when magic link sends successfully', async () => {
      const result = await signInWithMagicLink('test@example.com')
      expect(result.success).toBe(true)
      expect(result.error).toBeUndefined()
    })

    it('returns error when API returns error', async () => {
      mockSupabase.auth.signInWithOtp.mockResolvedValueOnce({
        data: null,
        error: { message: 'Invalid email' },
      })

      const result = await signInWithMagicLink('invalid@example.com')
      expect(result.success).toBe(false)
      expect(result.error).toBe('Invalid email')
    })
  })

  describe('signOut', () => {
    it('returns success when sign out works', async () => {
      const result = await signOut()
      expect(result.success).toBe(true)
    })
  })
})