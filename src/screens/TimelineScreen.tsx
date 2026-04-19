import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Timeline } from '../components/Timeline'
import { EventCard } from '../components/EventCard'
import { listEvents, EventData } from '../services/events'

export function TimelineScreen() {
  const navigate = useNavigate()
  const [events, setEvents] = useState<EventData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  const handleEventClick = (event: EventData) => {
    navigate(`/event/${event.id}`)
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

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Your Life Story
        </h1>

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