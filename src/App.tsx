import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { AuthProvider } from './context/AuthContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import { LoginScreen } from './components/LoginScreen'
import { OnboardingScreen } from './components/OnboardingScreen'
import { RecordingScreen } from './components/RecordingScreen'
import { DebugScreen } from './components/DebugScreen'

function Timeline() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <h1 className="text-2xl font-bold text-gray-800">Timeline (Coming Soon)</h1>
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function OnboardingCheck({ children, isOnboardingRoute = false }: { children: React.ReactNode; isOnboardingRoute?: boolean }) {
  const { user, loading, profileLoading, isProfileComplete } = useAuth()

  if (loading || profileLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    )
  }

  if (user && isProfileComplete === true) {
    if (isOnboardingRoute) {
      return <Navigate to="/" replace />
    }
    return <>{children}</>
  }

  if (user && isProfileComplete === false) {
    if (isOnboardingRoute) {
      return <>{children}</>
    }
    return <Navigate to="/onboarding" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginScreen />} />
      <Route path="/debug" element={<DebugScreen />} />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <OnboardingCheck isOnboardingRoute={true}>
              <OnboardingScreen />
            </OnboardingCheck>
          </ProtectedRoute>
        }
      />
      <Route
        path="/record"
        element={
          <ProtectedRoute>
            <RecordingScreen />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <OnboardingCheck>
              <Timeline />
            </OnboardingCheck>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App