import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginScreen } from './LoginScreen'

const mockSignIn = vi.fn()
vi.mock('../services/auth', () => ({
  signInWithPassword: (...args: unknown[]) => mockSignIn(...args),
}))

describe('LoginScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login form', () => {
    render(<LoginScreen />)

    expect(screen.getByText('Life Story Agent')).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows success message after successful login', async () => {
    mockSignIn.mockResolvedValue({ success: true })

    render(<LoginScreen />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const button = screen.getByRole('button', { name: /sign in/i })

    await userEvent.type(emailInput, 'test@example.com')
    await userEvent.type(passwordInput, 'password123')
    await userEvent.click(button)

    expect(screen.getByText(/welcome/i)).toBeInTheDocument()
  })

  it('shows error message on failure', async () => {
    mockSignIn.mockResolvedValue({ success: false, error: 'Rate limit exceeded' })

    render(<LoginScreen />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const button = screen.getByRole('button', { name: /sign in/i })

    await userEvent.type(emailInput, 'test@example.com')
    await userEvent.type(passwordInput, 'password123')
    await userEvent.click(button)

    expect(screen.getByText(/rate limit exceeded/i)).toBeInTheDocument()
  })
})