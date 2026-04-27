import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { AuthProvider } from './context/AuthContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import { LoadingScreen } from './components/LoadingScreen'
import { LoginScreen } from './components/LoginScreen'
import { OnboardingScreen } from './components/OnboardingScreen'
import { RecordingScreen } from './components/RecordingScreen'
import { InterviewScreen } from './components/InterviewScreen'
import { SummaryScreen } from './components/SummaryScreen'
import { DebugScreen } from './components/DebugScreen'
import { SignUpScreen } from './components/SignUpScreen'
import { VerifyEmailScreen } from './components/VerifyEmailScreen'
import { TimelineScreen } from './screens/TimelineScreen'
import { EventDetailScreen } from './screens/EventDetailScreen'
import { DashboardScreen } from './screens/DashboardScreen'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <LoadingScreen />
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function OnboardingCheck({ children, isOnboardingRoute = false }: { children: React.ReactNode; isOnboardingRoute?: boolean }) {
  const { user, loading, profileLoading, isProfileComplete } = useAuth()

  if (loading || profileLoading) {
    return <LoadingScreen />
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
      <Route path="/signup" element={<SignUpScreen />} />
      <Route path="/verify-email" element={<VerifyEmailScreen />} />
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
        path="/record/:eventId"
        element={
          <ProtectedRoute>
            <RecordingScreen />
          </ProtectedRoute>
        }
      />
      <Route
        path="/interview/:eventId"
        element={
          <ProtectedRoute>
            <InterviewScreen />
          </ProtectedRoute>
        }
      />
      <Route
        path="/summary/:eventId"
        element={
          <ProtectedRoute>
            <SummaryScreen />
          </ProtectedRoute>
        }
      />
      <Route
        path="/event/:eventId"
        element={
          <ProtectedRoute>
            <EventDetailScreen />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <OnboardingCheck>
              <TimelineScreen />
            </OnboardingCheck>
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <OnboardingCheck>
              <DashboardScreen />
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