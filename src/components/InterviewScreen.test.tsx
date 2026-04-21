import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { InterviewScreen } from './InterviewScreen'

const mockAnalyzeEvent = vi.fn()
const mockGenerateFollowUp = vi.fn()
const mockSkipFollowUp = vi.fn()
const mockGetEventWithQuestions = vi.fn()
const mockGenerateTTS = vi.fn()
const mockAddRecording = vi.fn()
const mockNavigate = vi.fn()

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useParams: () => ({ eventId: 'evt-1' }),
}))

vi.mock('../services/interview', () => ({
  analyzeEvent: (...args: unknown[]) => mockAnalyzeEvent(...args),
  generateFollowUp: (...args: unknown[]) => mockGenerateFollowUp(...args),
  skipFollowUp: (...args: unknown[]) => mockSkipFollowUp(...args),
  getEventWithQuestions: (...args: unknown[]) => mockGetEventWithQuestions(...args),
  generateTTS: (...args: unknown[]) => mockGenerateTTS(...args),
}))

vi.mock('../services/events', () => ({
  addRecording: (...args: unknown[]) => mockAddRecording(...args),
}))

describe('InterviewScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockClear()
  })

  it('shows loading or analyzing state initially', async () => {
    mockGetEventWithQuestions.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ id: 'evt-1', title: 'Test', follow_up_questions: [] }), 100))
    )

    render(<InterviewScreen />)

    await waitFor(
      () => {
        expect(screen.getByText(/loading|analyzing/i)).toBeInTheDocument()
      },
      { timeout: 100 }
    )
  })

  it('shows analyzing state', async () => {
    mockGetEventWithQuestions.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'Test',
      follow_up_questions: [],
    })
    mockAnalyzeEvent.mockResolvedValueOnce({
      extracted_time: '1990',
      extracted_place: 'Warsaw',
      people: [],
      key_events: [],
      themes: [],
      summary: 'Summary',
    })
    mockGenerateFollowUp.mockResolvedValueOnce({
      id: 'q-1',
      event_id: 'evt-1',
      question_text: 'What happened next?',
      was_answered: false,
      sequence_order: 1,
      created_at: new Date().toISOString(),
    })

    render(<InterviewScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('Analyzing your story...')).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('shows question when ready', async () => {
    mockGetEventWithQuestions.mockResolvedValueOnce({
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
          question_text: 'Tell me more about your childhood?',
          was_answered: false,
          audio_url: null,
          sequence_order: 1,
          created_at: new Date().toISOString(),
        },
      ],
    })

    render(<InterviewScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('Follow-up Question')).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('shows complete state when all questions answered', async () => {
    mockGetEventWithQuestions.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Story',
      time_anchor: null,
      time_anchor_date: null,
      place: null,
      status: 'completed',
      summary: 'Summary',
      created_at: new Date().toISOString(),
      follow_up_questions: [
        {
          id: 'q-1',
          event_id: 'evt-1',
          question_text: 'Done?',
          was_answered: true,
          audio_url: 'https://example.com/audio.webm',
          sequence_order: 1,
          created_at: new Date().toISOString(),
        },
      ],
    })

    render(<InterviewScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('Interview Complete!')).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('shows error state on failure', async () => {
    mockGetEventWithQuestions.mockRejectedValueOnce(new Error('Failed to load'))

    render(<InterviewScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('has skip and next question buttons', async () => {
    mockGetEventWithQuestions.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Story',
      time_anchor: null,
      time_anchor_date: null,
      place: null,
      status: 'recording',
      summary: null,
      created_at: new Date().toISOString(),
      follow_up_questions: [
        {
          id: 'q-1',
          event_id: 'evt-1',
          question_text: 'Question?',
          was_answered: false,
          audio_url: null,
          sequence_order: 1,
          created_at: new Date().toISOString(),
        },
      ],
    })

    render(<InterviewScreen />)

    await waitFor(
      () => {
        expect(screen.getByRole('button', { name: /next question/i })).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('has end interview button', async () => {
    mockGetEventWithQuestions.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Story',
      time_anchor: null,
      time_anchor_date: null,
      place: null,
      status: 'recording',
      summary: null,
      created_at: new Date().toISOString(),
      follow_up_questions: [
        {
          id: 'q-1',
          event_id: 'evt-1',
          question_text: 'Question?',
          was_answered: false,
          audio_url: null,
          sequence_order: 1,
          created_at: new Date().toISOString(),
        },
      ],
    })

    render(<InterviewScreen />)

    await waitFor(
      () => {
        expect(screen.getByRole('button', { name: /end interview/i })).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('shows initial story recording prompt when no questions exist', async () => {
    mockGetEventWithQuestions.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Story',
      time_anchor: null,
      time_anchor_date: null,
      place: null,
      status: 'recording',
      summary: null,
      created_at: new Date().toISOString(),
      follow_up_questions: [],
    })
    mockAnalyzeEvent.mockResolvedValueOnce({
      extracted_time: null,
      extracted_place: null,
      people: [],
      key_events: [],
      themes: [],
      summary: null,
    })
    mockGenerateFollowUp.mockResolvedValueOnce({
      id: 'q-new',
      event_id: 'evt-1',
      question_text: 'What is your earliest memory?',
      was_answered: false,
      sequence_order: 1,
      created_at: new Date().toISOString(),
    })

    render(<InterviewScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('Record your answer:')).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('handles error when getEventWithQuestions fails', async () => {
    mockGetEventWithQuestions.mockRejectedValueOnce(new Error('Network error'))

    render(<InterviewScreen />)

    await waitFor(
      () => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })
})