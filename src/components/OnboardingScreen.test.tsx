import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { OnboardingScreen } from './OnboardingScreen'
import { AuthContext } from '../context/AuthContext'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../services/user', () => ({
  updateUserProfile: vi.fn(),
}))

const mockAuthContextValue = {
  user: { id: 'test-user-id', email: 'test@example.com' } as any,
  session: {} as any,
  loading: false,
  profile: null,
  profileLoading: false,
  isProfileComplete: false,
  refreshProfile: vi.fn(),
}

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={mockAuthContextValue}>
        {component}
      </AuthContext.Provider>
    </BrowserRouter>
  )
}

describe('OnboardingScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockClear()
  })

  it('renders step 1 (name input) initially', () => {
    renderWithRouter(<OnboardingScreen />)
    expect(screen.getByText('What is your name?')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Your full name')).toBeInTheDocument()
  })

  it('shows error for empty name on Next', async () => {
    renderWithRouter(<OnboardingScreen />)
    
    const button = screen.getByRole('button', { name: /next/i })
    await userEvent.click(button)
    
    expect(await screen.findByText('Please enter your name')).toBeInTheDocument()
  })

  it('navigates to step 2 with valid name', async () => {
    renderWithRouter(<OnboardingScreen />)
    
    const input = screen.getByPlaceholderText('Your full name')
    await userEvent.type(input, 'John Doe')
    
    const button = screen.getByRole('button', { name: /next/i })
    await userEvent.click(button)
    
    await waitFor(() => {
      expect(screen.getByText('When were you born?')).toBeInTheDocument()
    })
  })

  it('can go back to step 1 from step 2', async () => {
    renderWithRouter(<OnboardingScreen />)
    
    const input = screen.getByPlaceholderText('Your full name')
    await userEvent.type(input, 'John Doe')
    
    await userEvent.click(screen.getByRole('button', { name: /next/i }))
    
    await waitFor(() => {
      expect(screen.getByText('When were you born?')).toBeInTheDocument()
    })
    
    await userEvent.click(screen.getByRole('button', { name: /back/i }))
    
    await waitFor(() => {
      expect(screen.getByText('What is your name?')).toBeInTheDocument()
    })
  })

  it('shows step indicator with 3 dots', () => {
    renderWithRouter(<OnboardingScreen />)
    
    const dots = document.querySelectorAll('.rounded-full')
    expect(dots.length).toBe(3)
  })
})