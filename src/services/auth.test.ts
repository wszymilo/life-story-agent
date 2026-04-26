import { describe, it, expect, vi, beforeEach } from 'vitest'
import { signInWithPassword } from './auth'
import * as authModule from 'aws-amplify/auth'

vi.mock('aws-amplify/auth')

describe('auth service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('signInWithPassword', () => {
    it('returns success when sign in succeeds', async () => {
      vi.mocked(authModule.signIn).mockResolvedValue({ isSignedIn: true } as any)

      const result = await signInWithPassword('test@example.com', 'password123')
      expect(result.success).toBe(true)
      expect(result.error).toBeUndefined()
    })

    it('returns error when sign in fails', async () => {
      vi.mocked(authModule.signIn).mockRejectedValue(new Error('Invalid password'))

      const result = await signInWithPassword('test@example.com', 'wrongpassword')
      expect(result.success).toBe(false)
      expect(result.error).toBe('Invalid password')
    })
  })
})