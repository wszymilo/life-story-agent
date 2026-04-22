import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  createEvent,
  getEvent,
  updateEvent,
  listEvents,
  deleteEvent,
  addRecording,
  retryTranscribe,
  completeEvent,
  AudioRecording,
} from './events'
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

describe('events service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockClear()
  })

  describe('createEvent', () => {
    it('creates event successfully', async () => {
      const mockEvent = { id: 'evt-1', title: 'My Story', status: 'recording' }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockEvent) }))

      const result = await createEvent({ title: 'My Story' })

      expect(result).toEqual(mockEvent)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/events/',
        expect.objectContaining({ method: 'POST' })
      )
    })

    it('throws on network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(createEvent({ title: 'Test' })).rejects.toThrow()
    })
  })

  describe('getEvent', () => {
    it('fetches event by id', async () => {
      const mockEvent = { id: 'evt-1', title: 'Test' }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockEvent) }))

      const result = await getEvent('evt-1')

      expect(result).toEqual(mockEvent)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/events/evt-1/',
        expect.any(Object)
      )
    })

    it('throws when not found', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Not found', 404))

      await expect(getEvent('evt-1')).rejects.toThrow('Not found')
    })
  })

  describe('updateEvent', () => {
    it('updates event successfully', async () => {
      const mockEvent = { id: 'evt-1', title: 'Updated' }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockEvent) }))

      const result = await updateEvent('evt-1', { title: 'Updated' })

      expect(result).toEqual(mockEvent)
    })

    it('throws on validation error', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Invalid', 422))

      await expect(updateEvent('evt-1', { title: '' })).rejects.toThrow('Invalid')
    })
  })

  describe('listEvents', () => {
    it('lists events successfully', async () => {
      const mockEvents = [{ id: 'evt-1' }, { id: 'evt-2' }]
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockEvents) }))

      const result = await listEvents()

      expect(result).toEqual(mockEvents)
    })

    it('throws on error', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Server error', 500))

      await expect(listEvents()).rejects.toThrow('Server error')
    })
  })

  describe('deleteEvent', () => {
    it('deletes event successfully', async () => {
      mockFetch.mockResolvedValueOnce(createFetchMock({ status: 204 }))

      await deleteEvent('evt-1')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/events/evt-1/',
        expect.objectContaining({ method: 'DELETE' })
      )
    })

    it('throws on error', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Not found', 404))

      await expect(deleteEvent('evt-1')).rejects.toThrow('Failed to delete event')
    })
  })

  describe('addRecording', () => {
    it('adds recording successfully', async () => {
      const mockRecording: AudioRecording = {
        id: 'rec-1',
        event_id: 'evt-1',
        sequence_order: 1,
        audio_url: 'https://example.com/audio.webm',
        transcript: 'My story text',
        recording_type: 'initial_story',
        duration_seconds: 60,
        created_at: new Date().toISOString(),
      }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockRecording) }))

      const audioBlob = new Blob(['audio'], { type: 'audio/webm' })
      const result = await addRecording('evt-1', audioBlob, 'initial_story', 60)

      expect(result).toEqual(mockRecording)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/events/evt-1/recordings/',
        expect.objectContaining({ method: 'POST' })
      )
    })

    it('throws with audioUrl when transcription fails but audio saved', async () => {
      const errorResponse = {
        ok: false,
        status: 422,
        statusText: 'Unprocessable Entity',
        json: () =>
          Promise.resolve({
            detail: 'Transcription failed but audio saved',
            audio_url: 'https://example.com/audio.webm',
            id: 'rec-1',
          }),
      }
      mockFetch.mockResolvedValueOnce(errorResponse as any)

      const audioBlob = new Blob(['audio'], { type: 'audio/webm' })
      await expect(addRecording('evt-1', audioBlob)).rejects.toThrow('Transcription failed but audio saved')
    })
  })

  describe('retryTranscribe', () => {
    it('retries transcription successfully', async () => {
      const mockRecording: AudioRecording = {
        id: 'rec-1',
        event_id: 'evt-1',
        sequence_order: 1,
        audio_url: 'https://example.com/audio.webm',
        transcript: 'Transcribed text',
        recording_type: 'initial_story',
        duration_seconds: 60,
        created_at: new Date().toISOString(),
      }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockRecording) }))

      const result = await retryTranscribe('rec-1')

      expect(result.transcript).toBe('Transcribed text')
    })

    it('throws on failure', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Transcription failed', 500))

      await expect(retryTranscribe('rec-1')).rejects.toThrow()
    })
  })

  describe('completeEvent', () => {
    it('completes event successfully', async () => {
      const completedEvent = { id: 'evt-1', title: 'My Story', summary: 'Summary text', status: 'completed' }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(completedEvent) }))

      const result = await completeEvent('evt-1')

      expect(result).toEqual(completedEvent)
      expect(result.status).toBe('completed')
    })

    it('throws on error', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Not found', 404))

      await expect(completeEvent('evt-1')).rejects.toThrow()
    })
  })
})