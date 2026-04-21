import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { EventDetailScreen } from './EventDetailScreen'

const mockGetEvent = vi.fn()
const mockDeleteEvent = vi.fn()
const mockNavigate = vi.fn()

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useParams: () => ({ eventId: 'evt-1' }),
}))

vi.mock('../services/events', () => ({
  getEvent: (...args: unknown[]) => mockGetEvent(...args),
  deleteEvent: (...args: unknown[]) => mockDeleteEvent(...args),
}))

describe('EventDetailScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockClear()
  })

  it('renders loading state initially', async () => {
    mockGetEvent.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ id: 'evt-1' }), 100))
    )

    render(<EventDetailScreen />)

    await waitFor(
      () => {
        expect(screen.getByText(/loading/i)).toBeInTheDocument()
      },
      { timeout: 200 }
    )
  })

  it('renders draft story with Continue to Interview button', async () => {
    mockGetEvent.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Draft Story',
      status: 'draft',
      time_anchor: null,
      time_anchor_date: '2024-01-15',
      place: 'Warsaw',
      summary: null,
      recordings: [],
      follow_up_questions: [],
      created_at: new Date().toISOString(),
    })

    render(<EventDetailScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('Continue to Interview')).toBeInTheDocument()
      },
      { timeout: 200 }
    )
  })

  it('renders draft story with Record Again button', async () => {
    mockGetEvent.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Draft Story',
      status: 'draft',
      time_anchor: null,
      time_anchor_date: '2024-01-15',
      place: 'Warsaw',
      summary: null,
      recordings: [{ id: 'rec-1', recording_type: 'initial_story', created_at: new Date().toISOString() }],
      follow_up_questions: [],
      created_at: new Date().toISOString(),
    })

    render(<EventDetailScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('Record Again')).toBeInTheDocument()
      },
      { timeout: 200 }
    )
  })

  it('renders completed story without Continue button', async () => {
    mockGetEvent.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Completed Story',
      status: 'completed',
      time_anchor: null,
      time_anchor_date: '2024-01-15',
      place: 'Warsaw',
      summary: 'This is my life story summary.',
      recordings: [{ id: 'rec-1' }],
      follow_up_questions: [],
      created_at: new Date().toISOString(),
    })

    render(<EventDetailScreen />)

    await waitFor(
      () => {
        expect(screen.queryByText('Continue to Interview')).not.toBeInTheDocument()
      },
      { timeout: 200 }
    )
  })

  it('shows recordings section when recordings exist', async () => {
    mockGetEvent.mockResolvedValueOnce({
      id: 'evt-1',
      title: 'My Story',
      status: 'draft',
      time_anchor: null,
      time_anchor_date: null,
      place: null,
      summary: null,
      recordings: [
        { id: 'rec-1', recording_type: 'initial_story', created_at: '2024-01-15T10:00:00Z' },
        { id: 'rec-2', recording_type: 'follow_up', created_at: '2024-01-16T10:00:00Z' },
      ],
      follow_up_questions: [],
      created_at: new Date().toISOString(),
    })

    render(<EventDetailScreen />)

    await waitFor(
      () => {
        expect(screen.getByText(/recordings \(2\)/i)).toBeInTheDocument()
      },
      { timeout: 200 }
    )
  })
})
