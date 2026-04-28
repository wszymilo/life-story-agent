import { describe, it, expect, vi, beforeEach } from 'vitest'
import { sendMagicLink, signInWithGoogleAuth } from './auth'
import * as firebaseModule from '../lib/firebase'

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

describe('auth service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('sendMagicLink', () => {
    it('returns success when magic link sends successfully', async () => {
      vi.mocked(firebaseModule.sendEmailLink).mockResolvedValue(undefined)

      const result = await sendMagicLink('test@example.com')
      expect(result.success).toBe(true)
      expect(result.error).toBeUndefined()
    })

    it('returns error when sending fails', async () => {
      vi.mocked(firebaseModule.sendEmailLink).mockRejectedValue(new Error('Network error'))

      const result = await sendMagicLink('test@example.com')
      expect(result.success).toBe(false)
      expect(result.error).toBe('Network error')
    })
  })

  describe('signInWithGoogleAuth', () => {
    it('returns success with token when Google sign-in succeeds', async () => {
      const mockUser = { uid: '123', email: 'test@example.com' }
      vi.mocked(firebaseModule.signInWithGoogle).mockResolvedValue(mockUser as any)
      vi.mocked(firebaseModule.getIdToken).mockResolvedValue('firebase-token')

      const result = await signInWithGoogleAuth()
      expect(result.success).toBe(true)
      expect(result.token).toBe('firebase-token')
    })

    it('returns error when Google sign-in fails', async () => {
      vi.mocked(firebaseModule.signInWithGoogle).mockRejectedValue(new Error('Popup closed'))

      const result = await signInWithGoogleAuth()
      expect(result.success).toBe(false)
      expect(result.error).toBe('Popup closed')
    })
  })
})