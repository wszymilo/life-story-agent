import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getUserProfile, updateUserProfile, isProfileComplete } from './user'
import { createFetchMock, createErrorResponse, mockFetch } from '../test/fetch-mock'

vi.stubGlobal('fetch', mockFetch)

vi.mock('../lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'mock-token' } },
      }),
    },
  },
}))

describe('user service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockClear()
  })

  describe('getUserProfile', () => {
    it('fetches user profile successfully', async () => {
      const mockProfile = {
        id: 'user-1',
        email: 'test@example.com',
        name: 'John Doe',
        birth_date: '1950-01-01',
        country_of_origin: 'Poland',
        created_at: new Date().toISOString(),
        relatives: [],
      }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockProfile) }))

      const result = await getUserProfile()

      expect(result.name).toBe('John Doe')
      expect(result.email).toBe('test@example.com')
    })

    it('throws on 401 error', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Unauthorized', 401))

      await expect(getUserProfile()).rejects.toThrow()
    })
  })

  describe('updateUserProfile', () => {
    it('updates user profile successfully', async () => {
      const mockProfile = {
        id: 'user-1',
        email: 'test@example.com',
        name: 'Jane Doe',
        birth_date: '1955-05-05',
        country_of_origin: 'Poland',
        created_at: new Date().toISOString(),
        relatives: [],
      }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockProfile) }))

      const result = await updateUserProfile({ name: 'Jane Doe', birth_date: '1955-05-05' })

      expect(result.name).toBe('Jane Doe')
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/users/me',
        expect.objectContaining({ method: 'PUT' })
      )
    })

    it('throws on validation error', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Invalid data', 422))

      await expect(updateUserProfile({ name: '' })).rejects.toThrow()
    })
  })

  describe('isProfileComplete', () => {
    it('returns true when all fields present', () => {
      const profile = {
        id: 'user-1',
        email: 'test@example.com',
        name: 'John',
        birth_date: '1950-01-01',
        country_of_origin: 'Poland',
        created_at: '',
        relatives: [] as unknown as [],
      }

      expect(isProfileComplete(profile)).toBe(true)
    })

    it('returns false when name missing', () => {
      const profile = {
        id: 'user-1',
        email: 'test@example.com',
        name: null,
        birth_date: '1950-01-01',
        country_of_origin: 'Poland',
        created_at: '',
        relatives: [] as unknown as [],
      }

      expect(isProfileComplete(profile)).toBe(false)
    })

    it('returns false when birth_date missing', () => {
      const profile = {
        id: 'user-1',
        email: 'test@example.com',
        name: 'John',
        birth_date: null,
        country_of_origin: 'Poland',
        created_at: '',
        relatives: [] as unknown as [],
      }

      expect(isProfileComplete(profile)).toBe(false)
    })

    it('returns false when country missing', () => {
      const profile = {
        id: 'user-1',
        email: 'test@example.com',
        name: 'John',
        birth_date: '1950-01-01',
        country_of_origin: null,
        created_at: '',
        relatives: [] as unknown as [],
      }

      expect(isProfileComplete(profile)).toBe(false)
    })
  })
})