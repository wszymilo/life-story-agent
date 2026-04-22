import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { Timeline } from '../components/Timeline'
import { EventCard } from '../components/EventCard'
import { TopBar } from '../components/TopBar'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { LoadingScreen } from '../components/LoadingScreen'
import { ErrorFallback } from '../components/ErrorFallback'
import { listEvents, generateMetaStory, EventData } from '../services/events'
import { useAuth } from '../context/AuthContext'
import { updatePreferredLanguage } from '../services/user'
import { LANGUAGE_OPTIONS } from '../services/constants'
import { useEventSelection } from '../hooks/useEventSelection'

export function TimelineScreen() {
  const navigate = useNavigate()
  const { profile, refreshProfile } = useAuth()
  const [events, setEvents] = useState<EventData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [generating, setGenerating] = useState(false)
  const [changingLanguage, setChangingLanguage] = useState(false)
  const [showLogoutDialog, setShowLogoutDialog] = useState(false)
  const [logoutLoading, setLogoutLoading] = useState(false)
  const {
    multiSelectMode,
    selectedIds,
    toggleSelection,
    clearSelection,
    enterSelectionMode,
  } = useEventSelection()

  const handleLanguageChange = async (lang: string) => {
    if (changingLanguage || !profile) return
    setChangingLanguage(true)
    try {
      await updatePreferredLanguage(lang)
      await refreshProfile()
    } catch (err) {
      console.error('Failed to update language:', err)
    } finally {
      setChangingLanguage(false)
    }
  }

  const handleLogout = () => {
    setShowLogoutDialog(true)
  }

  const handleConfirmLogout = async () => {
    setLogoutLoading(true)
    await supabase.auth.signOut()
    navigate('/login')
  }

  const handleEventClick = (event: EventData) => {
    if (multiSelectMode) return
    navigate(`/event/${event.id}`)
  }

  const handleSelectToggle = (eventId: string) => {
    toggleSelection(eventId)
  }

  const handleCombineStories = async () => {
    if (selectedIds.size < 2 || generating) return

    setGenerating(true)
    try {
      const result = await generateMetaStory(Array.from(selectedIds))
      navigate(`/event/${result.id}`)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to generate meta-story')
    } finally {
      setGenerating(false)
    }
  }

  const handleRetry = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await listEvents()
      setEvents(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const loadEvents = async () => {
      try {
        setLoading(true)
        setError('')
        const data = await listEvents()
        setEvents(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load events')
      } finally {
        setLoading(false)
      }
    }
    loadEvents()
  }, [])

  if (loading) {
    return <LoadingScreen message="Loading memories..." />
  }

  if (error) {
    return <ErrorFallback message={error} onRetry={handleRetry} />
  }

  const completedCount = events.filter(e => e.status === 'complete').length

  const currentLanguage = profile?.preferred_language || 'pl'

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar
        title=""
        secondary={
          multiSelectMode
            ? { label: 'Done', onClick: clearSelection }
            : { label: 'Logout', onClick: handleLogout }
        }
        primary={
          completedCount >= 2 && !multiSelectMode
            ? { label: 'Select', onClick: enterSelectionMode }
            : undefined
        }
        tertiaryLeft={
          !multiSelectMode && (
            <div className="flex items-center gap-2">
              <select
                value={currentLanguage}
                onChange={(e) => handleLanguageChange(e.target.value)}
                disabled={changingLanguage || !profile}
                className="px-3 py-2 text-base min-h-10 border border-gray-300 rounded-lg bg-white text-gray-700 disabled:opacity-50"
              >
                {LANGUAGE_OPTIONS.map((opt) => (
                  <option key={opt.code} value={opt.code}>
                    {opt.label}
                  </option>
                ))}
              </select>
              {profile?.is_admin && (
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-3 py-2 text-base min-h-10 text-gray-600 hover:text-gray-800"
                  title="Dashboard"
                >
                  📊
                </button>
              )}
            </div>
          )
        }
      />

      <div className="max-w-2xl mx-auto p-4">
        {multiSelectMode && selectedIds.size >= 2 && (
          <button
            onClick={handleCombineStories}
            disabled={generating}
            className="w-full mb-4 py-4 min-h-14 bg-blue-600 hover:bg-blue-700 text-white text-lg rounded-lg font-medium disabled:opacity-50"
          >
            {generating ? 'Combining...' : `Combine ${selectedIds.size} Stories`}
          </button>
        )}

        {events.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">
              No memories yet. Start recording your life story!
            </p>
            <button
              onClick={() => navigate('/record')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium"
            >
              Record Your First Memory
            </button>
          </div>
        ) : (
          <Timeline>
            {events.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                onClick={handleEventClick}
                multiSelectMode={multiSelectMode}
                selected={selectedIds.has(event.id)}
                onSelect={handleSelectToggle}
                language={currentLanguage}
              />
            ))}
          </Timeline>
        )}

        {events.length > 0 && (
          <>
            <button
              onClick={() => navigate('/record')}
              className="fixed bottom-6 right-6 w-16 h-16 bg-blue-600 rounded-full shadow-lg flex items-center justify-center hover:bg-blue-700 transition-colors"
              aria-label="Add new memory"
            >
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </button>

            <ConfirmDialog
              open={showLogoutDialog}
              onClose={() => setShowLogoutDialog(false)}
              onConfirm={handleConfirmLogout}
              title="Sign Out"
              message="Are you sure you want to sign out?"
              confirmLabel="Sign Out"
              cancelLabel="Cancel"
              destructive
              loading={logoutLoading}
            />
          </>
        )}
      </div>
    </div>
  )
}
