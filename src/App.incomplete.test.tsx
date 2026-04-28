import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'

vi.mock('./hooks/useAuth')
vi.mock('./services/user')

import { useAuth } from './hooks/useAuth'
import { getUserProfile, isProfileComplete, UserProfile } from './services/user'

function TestApp() {
  const auth = useAuth()
  
  if (auth.loading) {
    return <div>Loading...</div>
  }
  
  if (!auth.user) {
    return <Navigate to="/login" />
  }
  
  return <ProfileCheck />
}

function ProfileCheck() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [profileLoading, setProfileLoading] = useState(true)
  
  useEffect(() => {
    getUserProfile()
      .then((data: UserProfile) => {
        setProfile(data)
        setProfileLoading(false)
      })
      .catch(() => {
        setProfileLoading(false)
      })
  }, [])
  
  if (profileLoading) {
    return <div>Loading...</div>
  }
  
  if (profile && !isProfileComplete(profile)) {
    return <Navigate to="/onboarding" />
  }
  
  return <div data-testid="timeline">Timeline</div>
}

describe('Profile redirect - incomplete', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('redirects to onboarding when profile is incomplete', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        uid: '123',
        email: 'test@example.com',
      } as any,
      token: 'firebase-token',
      loading: false,
      profile: {
        id: '123',
        email: 'test@example.com',
        name: null,
        birth_date: null,
        country_of_origin: null,
        created_at: '2024-01-01',
        relatives: [],
      },
      profileLoading: false,
      isProfileComplete: false,
      refreshProfile: vi.fn(),
    })
    
    vi.mocked(getUserProfile).mockResolvedValue({
      id: '123',
      email: 'test@example.com',
      name: null,
      birth_date: null,
      country_of_origin: null,
      created_at: '2024-01-01',
      relatives: [],
    })
    
    vi.mocked(isProfileComplete).mockReturnValue(false)
    
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<div>Login</div>} />
          <Route path="/onboarding" element={<div data-testid="onboarding">Onboarding</div>} />
          <Route path="/" element={<TestApp />} />
        </Routes>
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByTestId('onboarding')).toBeInTheDocument()
    }, { timeout: 2000 })
  })
})