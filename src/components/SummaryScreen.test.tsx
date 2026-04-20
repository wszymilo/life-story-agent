import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { SummaryScreen } from './SummaryScreen'

const mockCompleteEvent = vi.fn()
const mockGenerateTTS = vi.fn()
const mockNavigate = vi.fn()

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useParams: () => ({ eventId: 'evt-1' }),
}))

vi.mock('../services/events', () => ({
  completeEvent: (...args: unknown[]) => mockCompleteEvent(...args),
}))

vi.mock('../services/interview', () => ({
  generateTTS: (...args: unknown[]) => mockGenerateTTS(...args),
}))

describe('SummaryScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockClear()
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