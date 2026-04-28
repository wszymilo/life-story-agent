import { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react'
import i18n from '../i18n'
import { getUserProfile, isProfileComplete, UserProfile } from '../services/user'
import { onAuthChange, getIdToken, User } from '../lib/firebase'

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  profile: UserProfile | null
  profileLoading: boolean
  isProfileComplete: boolean | null
  refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function AuthProviderComponent({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
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
        const lang = data?.preferred_language
        if (lang && (lang === 'pl' || lang === 'en') && i18n.language !== lang) {
          i18n.changeLanguage(lang)
        }
      })
      .catch(() => {
        setProfileLoading(false)
      })
      .finally(() => {
        profileLoadInProgress.current = false
      })
  }

  useEffect(() => {
    const unsubscribe = onAuthChange(async (firebaseUser) => {
      setUser(firebaseUser)
      if (firebaseUser) {
        try {
          const idToken = await getIdToken(firebaseUser)
          setToken(idToken)
          localStorage.setItem('firebase_token', idToken)
        } catch (e) {
          setToken(null)
          localStorage.removeItem('firebase_token')
        }
        setLoading(false)
        loadProfile(firebaseUser.uid)
      } else {
        setToken(null)
        localStorage.removeItem('firebase_token')
        setLoading(false)
        setProfile(null)
        setProfileLoading(false)
      }
    })

    return () => unsubscribe()
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

  const isComplete = profile ? isProfileComplete(profile) : null

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
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
export type { AuthContextType }