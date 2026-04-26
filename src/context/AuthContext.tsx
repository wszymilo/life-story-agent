import { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react'
import { Hub } from 'aws-amplify/utils'
import i18n from '../i18n'
import { getUserProfile, isProfileComplete, UserProfile } from '../services/user'

interface AuthContextType {
  user: { userId: string; signInDetails?: { loginId?: string } } | null
  loading: boolean
  profile: UserProfile | null
  profileLoading: boolean
  isProfileComplete: boolean | null
  refreshProfile: () => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function AuthProviderComponent({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthContextType['user']>(null)
  const [loading, setLoading] = useState(true)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [profileLoading, setProfileLoading] = useState(true)

  const profileLoadInProgress = useRef(false)

const loadProfile = async (_userId: string) => {
    if (profileLoadInProgress.current) {
      return
    }
    profileLoadInProgress.current = true
    setProfileLoading(true)
    try {
      const data = await getUserProfile()
      setProfile(data)
      const lang = data?.preferred_language
      if (lang && (lang === 'pl' || lang === 'en') && i18n.language !== lang) {
        i18n.changeLanguage(lang)
      }
    } catch {
      setProfile(null)
    } finally {
      setProfileLoading(false)
      profileLoadInProgress.current = false
    }
  }

  useEffect(() => {
    const checkUser = async () => {
      try {
        const { getCurrentUser } = await import('aws-amplify/auth')
        const currentUser = await getCurrentUser()
        setUser({ userId: currentUser.userId, signInDetails: currentUser.signInDetails })
        await loadProfile(currentUser.userId)
      } catch {
        setUser(null)
        setProfile(null)
        setProfileLoading(false)
      } finally {
        setLoading(false)
      }
    }

    checkUser()

    const unsubscribe = Hub.listen('auth', async ({ payload }) => {
      const { event } = payload
      if (event === 'signedIn' || event === 'tokenRefresh') {
        try {
          const { getCurrentUser } = await import('aws-amplify/auth')
          const currentUser = await getCurrentUser()
          setUser({ userId: currentUser.userId, signInDetails: currentUser.signInDetails })
          await loadProfile(currentUser.userId)
        } catch {
          setUser(null)
          setProfile(null)
        }
      } else if (event === 'signedOut' || event === 'tokenRefresh_failure') {
        setUser(null)
        setProfile(null)
        setProfileLoading(false)
      }
      setLoading(false)
    })

    return unsubscribe
  }, [])

  const refreshProfile = async () => {
    if (!user) return

    try {
      const data = await getUserProfile()
      setProfile(data)
      const lang = data?.preferred_language
      if (lang && (lang === 'pl' || lang === 'en') && i18n.language !== lang) {
        i18n.changeLanguage(lang)
      }
    } catch {
      setProfile(null)
    }
  }

  const signOutUser = async () => {
    const { signOut } = await import('aws-amplify/auth')
    await signOut()
    setUser(null)
    setProfile(null)
  }

  const isComplete = profile ? isProfileComplete(profile) : null

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        profile,
        profileLoading,
        isProfileComplete: isComplete,
        refreshProfile,
        signOut: signOutUser,
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
// eslint-disable-next-line react-refresh/only-export-components
export { useAuthContext as useAuth, AuthContext }
export type { AuthContextType }