import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  analyzeEvent,
  generateFollowUp,
  getEventWithQuestions,
  generateTTS,
} from './interview'
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

describe('interview service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockClear()
  })

  describe('analyzeEvent', () => {
    it('analyzes event successfully', async () => {
      const mockAnalysis = {
        extracted_time: '1990',
        extracted_place: 'Warsaw',
        people: ['John'],
        key_events: ['Started school'],
        themes: ['education'],
        summary: 'Summary text',
      }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockAnalysis) }))

      const result = await analyzeEvent('evt-1', 'Test transcript content')

      expect(result).toEqual(mockAnalysis)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/events/evt-1/analyze',
        expect.objectContaining({ method: 'POST' })
      )
    })

    it('throws on error', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Analysis failed', 500))

      await expect(analyzeEvent('evt-1', 'Test transcript content')).rejects.toThrow()
    })
  })

  describe('generateFollowUp', () => {
    it('generates follow-up question', async () => {
      const mockQuestion = {
        id: 'q-1',
        event_id: 'evt-1',
        question_text: 'What happened next?',
        was_answered: false,
        sequence_order: 1,
        created_at: new Date().toISOString(),
      }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockQuestion) }))

      const result = await generateFollowUp('evt-1', 'Test transcript')

      expect(result.question_text).toBe('What happened next?')
    })

    it('throws on error', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Failed to generate', 500))

      await expect(generateFollowUp('evt-1', 'Test transcript')).rejects.toThrow()
    })
  })

  describe('getEventWithQuestions', () => {
    it('fetches event with questions', async () => {
      const mockEvent = {
        id: 'evt-1',
        title: 'My Story',
        time_anchor: '1990',
        time_anchor_date: null,
        place: 'Warsaw',
        status: 'recording',
        summary: null,
        created_at: new Date().toISOString(),
        follow_up_questions: [
          {
            id: 'q-1',
            event_id: 'evt-1',
            question_text: 'Tell me more',
            was_answered: false,
            sequence_order: 1,
            created_at: new Date().toISOString(),
          },
        ],
      }
      mockFetch.mockResolvedValueOnce(createFetchMock({ json: () => Promise.resolve(mockEvent) }))

      const result = await getEventWithQuestions('evt-1')

      expect(result.id).toBe('evt-1')
      expect(result.follow_up_questions).toHaveLength(1)
    })

    it('throws on error', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('Not found', 404))

      await expect(getEventWithQuestions('evt-1')).rejects.toThrow()
    })
  })

  describe('generateTTS', () => {
    it('generates TTS audio', async () => {
      const audioBlob = new Blob(['audio'], { type: 'audio/mp3' })
      mockFetch.mockResolvedValueOnce(
        createFetchMock({
          json: () => Promise.resolve({}),
          blob: () => Promise.resolve(audioBlob),
        })
      )

      const result = await generateTTS('Hello world')

      expect(result.audio_url).toContain('blob:')
    })

    it('throws on error', async () => {
      mockFetch.mockResolvedValueOnce(createErrorResponse('TTS failed', 500))

      await expect(generateTTS('Hello')).rejects.toThrow()
    })
  })
})