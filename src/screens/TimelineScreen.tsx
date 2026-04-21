import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { Timeline } from '../components/Timeline'
import { EventCard } from '../components/EventCard'
import { listEvents, generateMetaStory, EventData } from '../services/events'
import { useAuth } from '../context/AuthContext'
import { updatePreferredLanguage } from '../services/user'
import { LANGUAGE_OPTIONS } from '../services/constants'

export function TimelineScreen() {
  const navigate = useNavigate()
  const { profile, refreshProfile } = useAuth()
  const [events, setEvents] = useState<EventData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [multiSelectMode, setMultiSelectMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [generating, setGenerating] = useState(false)
  const [changingLanguage, setChangingLanguage] = useState(false)

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

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  const handleEventClick = (event: EventData) => {
    if (multiSelectMode) return
    navigate(`/event/${event.id}`)
  }

  const handleSelectToggle = (eventId: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(eventId)) {
      newSelected.delete(eventId)
    } else {
      newSelected.add(eventId)
    }
    setSelectedIds(newSelected)
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
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading memories...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={handleRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  const completedCount = events.filter(e => e.status === 'complete').length

  const currentLanguage = profile?.preferred_language || 'pl'
  
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <select
            value={currentLanguage}
            onChange={(e) => handleLanguageChange(e.target.value)}
            disabled={changingLanguage || !profile}
            className="text-sm px-2 py-1 border border-gray-300 rounded bg-white text-gray-700 disabled:opacity-50"
          >
            {LANGUAGE_OPTIONS.map((opt) => (
              <option key={opt.code} value={opt.code}>
                {opt.label}
              </option>
            ))}
          </select>
          <button
            onClick={handleLogout}
            className="text-sm px-3 py-1 text-gray-600 hover:text-gray-800"
          >
            Wyloguj
          </button>
          {completedCount >= 2 && !multiSelectMode && (
            <button
              onClick={() => setMultiSelectMode(true)}
              className="text-sm px-3 py-1 text-blue-600 hover:text-blue-800"
            >
              Select
            </button>
          )}
          {multiSelectMode && (
            <button
              onClick={() => {
                setMultiSelectMode(false)
                setSelectedIds(new Set())
              }}
              className="text-sm px-3 py-1 text-gray-600 hover:text-gray-800"
            >
              Done
            </button>
          )}
        </div>

        {multiSelectMode && selectedIds.size >= 2 && (
          <button
            onClick={handleCombineStories}
            disabled={generating}
            className="w-full mb-4 py-3 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50"
          >
            {generating ? 'Combining stories...' : `Combine ${selectedIds.size} Stories`}
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
              />
            ))}
          </Timeline>
        )}
      </div>

      {events.length > 0 && (
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
      )}
    </div>
  )
}