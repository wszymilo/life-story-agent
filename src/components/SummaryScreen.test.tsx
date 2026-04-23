import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { SummaryScreen } from './SummaryScreen'

const mockCompleteEvent = vi.fn()
const mockGetEvent = vi.fn()
const mockUpdateEvent = vi.fn()
const mockGenerateTTS = vi.fn()
const mockGetEventWithQuestions = vi.fn()
const mockNavigate = vi.fn()

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useParams: () => ({ eventId: 'evt-1' }),
}))

vi.mock('../services/events', () => ({
  completeEvent: (...args: unknown[]) => mockCompleteEvent(...args),
  getEvent: (...args: unknown[]) => mockGetEvent(...args),
  updateEvent: (...args: unknown[]) => mockUpdateEvent(...args),
}))

vi.mock('../services/interview', () => ({
  generateTTS: (...args: unknown[]) => mockGenerateTTS(...args),
  getEventWithQuestions: (...args: unknown[]) => mockGetEventWithQuestions(...args),
}))

vi.mock('../hooks/useEncryption', () => ({
  useEncryption: vi.fn(() => ({ key: 'mock-key' as unknown as CryptoKey, isReady: true, isGenerating: false, error: null })),
}))

vi.mock('../lib/crypto', () => ({
  encrypt: vi.fn(async (text: string) => `enc:${text}`),
  decrypt: vi.fn(async (text: string) => text.replace(/^enc:/, '')),
}))

describe('SummaryScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockClear()
    mockGetEvent.mockResolvedValue({ id: 'evt-1', title: 'My Story', summary: null, status: 'recording', recordings: [], follow_up_questions: [] })
    mockGetEventWithQuestions.mockResolvedValue({ id: 'evt-1', title: 'My Story', summary: null, status: 'recording', recordings: [], follow_up_questions: [] })
  })

  it('shows loading state initially', async () => {
    mockCompleteEvent.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ id: 'evt-1', title: 'My Story', summary: 'Test' }), 100))
    )

    render(<SummaryScreen />)

    expect(screen.getByText('Generating your story summary...')).toBeInTheDocument()
  })

  it('shows summary when ready', async () => {
    mockCompleteEvent.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Story',
      summary: 'This is my life story about growing up in Warsaw.',
      status: 'completed',
    })

    render(<SummaryScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('My Story')).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('shows error state on failure', async () => {
    mockCompleteEvent.mockRejectedValueOnce(new Error('Failed to generate'))

    render(<SummaryScreen />)

    await waitFor(
      () => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('has listen button when ready', async () => {
    mockCompleteEvent.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Story',
      summary: 'Summary',
      status: 'completed',
    })

    render(<SummaryScreen />)

    await waitFor(
      () => {
        expect(screen.getByRole('button', { name: /listen to summary/i })).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('has save and continue button', async () => {
    mockCompleteEvent.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Story',
      summary: 'Summary',
      status: 'completed',
    })

    render(<SummaryScreen />)

    await waitFor(
      () => {
        expect(screen.getByRole('button', { name: /save & continue/i })).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })
})