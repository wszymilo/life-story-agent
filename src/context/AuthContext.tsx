import { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'
import { getUserProfile, isProfileComplete, UserProfile } from '../services/user'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  profile: UserProfile | null
  profileLoading: boolean
  isProfileComplete: boolean | null
  refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function AuthProviderComponent({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [profileLoading, setProfileLoading] = useState(true)

  const profileLoadInProgress = useRef(false)

  const loadProfile = (_userId: string) => {
    if (profileLoadInProgress.current) {
      return
    }
    profileLoadInProgress.current = true
    setProfileLoading(true)
    getUserProfile()
      .then((data) => {
        setProfile(data)
        setProfileLoading(false)
      })
      .catch(() => {
        setProfileLoading(false)
      })
      .finally(() => {
        profileLoadInProgress.current = false
      })
  }

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setSession(session)
      setLoading(false)
      if (session?.user) {
        loadProfile(session.user.id)
      } else {
        setProfile(null)
        setProfileLoading(false)
      }
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
      setSession(session)
      setLoading(false)
      if (session?.user) {
        loadProfile(session.user.id)
      } else {
        setProfile(null)
        setProfileLoading(false)
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  const refreshProfile = async () => {
    if (!user) return

    try {
      const data = await getUserProfile()
      setProfile(data)
    } catch {
      setProfile(null)
    }
  }

  const isComplete = profile ? isProfileComplete(profile) : null

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        profile,
        profileLoading,
        isProfileComplete: isComplete,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

function useAuthContext() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = AuthProviderComponent
export { useAuthContext as useAuth, AuthContext }

// eslint-disable-next-line react-refresh/only-export-components
export type { AuthContextType }