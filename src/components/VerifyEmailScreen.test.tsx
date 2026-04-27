import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { VerifyEmailScreen } from './VerifyEmailScreen'

vi.mock('aws-amplify/auth', () => ({
  confirmSignUp: vi.fn(),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: vi.fn(),
    useLocation: () => ({ state: { email: 'test@example.com' } }),
  }
})

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('VerifyEmailScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders verification form', () => {
    renderWithRouter(<VerifyEmailScreen />)

    expect(screen.getByText('Verify Your Email')).toBeInTheDocument()
    expect(screen.getByLabelText(/code/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /verify/i })).toBeInTheDocument()
  })

  it('shows email in description', () => {
    renderWithRouter(<VerifyEmailScreen />)

    expect(screen.getByText(/test@example.com/)).toBeInTheDocument()
  })

  it('calls confirmSignUp on submit', async () => {
    const mockConfirmSignUp = vi.mocked((await import('aws-amplify/auth')).confirmSignUp)
    mockConfirmSignUp.mockResolvedValueOnce({} as any)

    renderWithRouter(<VerifyEmailScreen />)

    await userEvent.type(screen.getByLabelText(/code/i), '123456')
    await userEvent.click(screen.getByRole('button', { name: /verify/i }))

    expect(mockConfirmSignUp).toHaveBeenCalledWith({
      username: 'test@example.com',
      confirmationCode: '123456',
    })
  })

  it('shows success and navigate to login on success', async () => {
    const mockConfirmSignUp = vi.mocked((await import('aws-amplify/auth')).confirmSignUp)
    mockConfirmSignUp.mockResolvedValueOnce({} as any)

    renderWithRouter(<VerifyEmailScreen />)

    await userEvent.type(screen.getByLabelText(/code/i), '123456')
    await userEvent.click(screen.getByRole('button', { name: /verify/i }))

    expect(await screen.findByText(/email verified/i)).toBeInTheDocument()

    const goToLoginButton = screen.getByRole('button', { name: /go to sign in/i })
    expect(goToLoginButton).toBeInTheDocument()
  })

  it('shows error state on failure', async () => {
    const mockConfirmSignUp = vi.mocked((await import('aws-amplify/auth')).confirmSignUp)
    mockConfirmSignUp.mockRejectedValueOnce(new Error('Invalid code'))

    renderWithRouter(<VerifyEmailScreen />)

    await userEvent.type(screen.getByLabelText(/code/i), 'wrong')
    await userEvent.click(screen.getByRole('button', { name: /verify/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /verify/i })).not.toBeDisabled()
    })
  })

  it('only allows numeric input', async () => {
    const mockConfirmSignUp = vi.mocked((await import('aws-amplify/auth')).confirmSignUp)
    mockConfirmSignUp.mockResolvedValueOnce({} as any)

    renderWithRouter(<VerifyEmailScreen />)

    const input = screen.getByLabelText(/code/i)
    await userEvent.type(input, 'abc123def456')

    expect(input).toHaveValue('123456')
  })
})