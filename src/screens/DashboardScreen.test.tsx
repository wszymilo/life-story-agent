import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { DashboardScreen } from './DashboardScreen'

const mockGetDashboardStats = vi.fn()
const mockNavigate = vi.fn()

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

vi.mock('../services/evaluation', () => ({
  getDashboardStats: () => mockGetDashboardStats(),
}))

describe('DashboardScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockClear()
  })

  it('renders loading state initially', () => {
    mockGetDashboardStats.mockImplementation(
      () => new Promise(() => {})
    )

    render(<DashboardScreen />)

    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument()
  })

  it('renders dashboard stats when loaded', async () => {
    mockGetDashboardStats.mockResolvedValueOnce({
      total_evaluations: 42,
      avg_factual_accuracy: 4.2,
      avg_coherence: 3.8,
      avg_completeness: 4.5,
      avg_overall_score: 4.1,
      recent_evaluations: [
        {
          id: 'eval-1',
          event_id: 'evt-1',
          eval_type: 'summary',
          prompt_text: null,
          summary_text: null,
          factual_accuracy: 4,
          coherence: 3,
          completeness: 5,
          overall_score: 4,
          evaluator_model: 'gpt-4o-mini',
          created_at: '2024-06-15T10:00:00Z',
        },
      ],
    })

    render(<DashboardScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('42')).toBeInTheDocument()
      },
      { timeout: 200 }
    )

    expect(screen.getByText('Total Evaluations')).toBeInTheDocument()
    expect(screen.getByText('4.2')).toBeInTheDocument()
    expect(screen.getByText('3.8')).toBeInTheDocument()
    expect(screen.getByText('4.5')).toBeInTheDocument()
    expect(screen.getByText('4.1')).toBeInTheDocument()
    expect(screen.getByText('summary')).toBeInTheDocument()
  })

  it('navigates back to timeline when back button is clicked', async () => {
    mockGetDashboardStats.mockResolvedValueOnce({
      total_evaluations: 5,
      avg_factual_accuracy: 3.5,
      avg_coherence: 3.5,
      avg_completeness: 3.5,
      avg_overall_score: 3.5,
      recent_evaluations: [],
    })

    render(<DashboardScreen />)

    await waitFor(
      () => {
        expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument()
      },
      { timeout: 200 }
    )

    fireEvent.click(screen.getByRole('button', { name: /back/i }))
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('shows error fallback with back button on failure', async () => {
    mockGetDashboardStats.mockRejectedValueOnce(new Error('Network error'))

    render(<DashboardScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      },
      { timeout: 200 }
    )

    const backButton = screen.getByRole('button', { name: /back to timeline/i })
    expect(backButton).toBeInTheDocument()

    fireEvent.click(backButton)
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('shows no data message when stats are null', async () => {
    mockGetDashboardStats.mockResolvedValueOnce(null)

    render(<DashboardScreen />)

    await waitFor(
      () => {
        expect(screen.getByText('No data available')).toBeInTheDocument()
      },
      { timeout: 200 }
    )
  })
})
