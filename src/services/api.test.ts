import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getAuthHeader, fetchApi } from './api'
import { createFetchMock, createErrorResponse, mockFetch } from '../test/fetch-mock'

vi.stubGlobal('fetch', mockFetch)

describe('api service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockClear()
    localStorage.removeItem('firebase_token')
  })

  describe('getAuthHeader', () => {
    it('returns token in Authorization header', async () => {
      localStorage.setItem('firebase_token', 'mock-token')

      const headers = await getAuthHeader()

      expect(headers).toHaveProperty('Authorization', 'Bearer mock-token')
    })

    it('returns empty object when no token', async () => {
      const headers = await getAuthHeader()

      expect(headers).toEqual({})
    })
  })

  describe('fetchApi', () => {
    it('merges auth headers with options', async () => {
      localStorage.setItem('firebase_token', 'mock-token')
      mockFetch.mockResolvedValueOnce(createFetchMock())

      await fetchApi('/api/test', { method: 'POST' })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer mock-token',
          }),
          credentials: 'include',
        })
      )
    })

    it('returns error response without throwing', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Server error', 500))

      const response = await fetchApi('/api/test')

      expect(response.ok).toBe(false)
      expect(response.status).toBe(500)
    })
  })
})