import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { ReactNode } from 'react'
import { AuthProvider, useAuth as useAuthContext } from '../context/AuthContext'

vi.mock('../services/user', () => ({
  getUserProfile: vi.fn().mockResolvedValue(null),
  isProfileComplete: vi.fn(),
}))

function TestComponent() {
  const { user, loading } = useAuthContext()
  return (
    <div>
      <div data-testid="user">{user ? 'has-user' : 'no-user'}</div>
      <div data-testid="loading">{loading ? 'loading' : 'not-loading'}</div>
    </div>
  )
}

function renderWithProvider(ui: ReactNode) {
  return render(<AuthProvider>{ui}</AuthProvider>)
}

describe.skip('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('provides user as null when not authenticated', async () => {
    renderWithProvider(<TestComponent />)

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('no-user')
    })
  })

  it('provides loading state initially', () => {
    renderWithProvider(<TestComponent />)

    expect(screen.getByTestId('loading')).toHaveTextContent('loading')
  })

  it('throws error when used outside provider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => render(<TestComponent />)).toThrow('useAuth must be used within an AuthProvider')

    consoleError.mockRestore()
  })
})