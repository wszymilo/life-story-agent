import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { SignUpScreen } from './SignUpScreen'

const mockSignUp = vi.fn()
vi.mock('aws-amplify/auth', () => ({
  signUp: (...args: unknown[]) => mockSignUp(...args),
}))

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('SignUpScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders sign up form', () => {
    renderWithRouter(<SignUpScreen />)

    expect(screen.getByRole('heading', { name: 'Create Account' })).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('shows password requirements', () => {
    renderWithRouter(<SignUpScreen />)

    expect(screen.getByText(/password requirements/i)).toBeInTheDocument()
    expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument()
  })

  it('validates password mismatch', async () => {
    mockSignUp.mockResolvedValue({ success: true })

    renderWithRouter(<SignUpScreen />)

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'Password123')
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'DifferentPass123')

    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    expect(mockSignUp).not.toHaveBeenCalled()
  })

  it('calls signUp on submit', async () => {
    mockSignUp.mockResolvedValue({ success: true })

    renderWithRouter(<SignUpScreen />)

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'Password123')
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'Password123')

    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(mockSignUp).toHaveBeenCalledWith({
      username: 'test@example.com',
      password: 'Password123',
      options: {
        userAttributes: { email: 'test@example.com' },
      },
    })
  })

  it('shows success message on successful sign up', async () => {
    mockSignUp.mockResolvedValue({ success: true })

    renderWithRouter(<SignUpScreen />)

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'Password123')
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'Password123')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText(/check your email/i)).toBeInTheDocument()
  })

  it('shows error message on failure', async () => {
    mockSignUp.mockRejectedValue(new Error('User already exists'))

    renderWithRouter(<SignUpScreen />)

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'Password123')
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'Password123')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText(/user already exists/i)).toBeInTheDocument()
  })

  it('has link to sign in', () => {
    renderWithRouter(<SignUpScreen />)

    const link = screen.getByRole('link', { name: /sign in/i })
    expect(link).toHaveAttribute('href', '/login')
  })
})