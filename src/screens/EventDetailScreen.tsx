import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getEvent, deleteEvent, streamAudio, EventData, AudioRecording } from '../services/events'

export function EventDetailScreen() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const [event, setEvent] = useState<EventData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [deleting, setDeleting] = useState(false)
  const [playingId, setPlayingId] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    if (!eventId) return

    const loadEvent = async () => {
      try {
        setLoading(true)
        setError('')
        const data = await getEvent(eventId)
        setEvent(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load event')
      } finally {
        setLoading(false)
      }
    }

    loadEvent()
  }, [eventId])

  const handleDelete = async () => {
    if (!event?.id) return

    const confirmed = window.confirm(
      'Are you sure you want to delete this memory? This cannot be undone.'
    )
    if (!confirmed) return

    setDeleting(true)
    try {
      await deleteEvent(event.id)
      navigate('/')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete')
      setDeleting(false)
    }
  }

  const playAudio = async (recording: AudioRecording) => {
    if (!event?.id) return

    if (playingId === recording.id) {
      audioRef.current?.pause()
      setPlayingId(null)
      return
    }

    if (audioRef.current) {
      audioRef.current.pause()
    }

    try {
      const blob = await streamAudio(event.id, recording.id)
      const url = URL.createObjectURL(blob)
      audioRef.current = new Audio(url)
      audioRef.current.onended = () => {
        setPlayingId(null)
        URL.revokeObjectURL(url)
      }
      audioRef.current.play()
      setPlayingId(recording.id)
    } catch (err) {
      console.error('Failed to play audio:', err)
      alert('Failed to play audio')
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('pl-PL', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return null
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (error || !event) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Event not found'}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg"
          >
            Back to Timeline
          </button>
        </div>
      </div>
    )
  }

  const isDraft = event.status === 'draft'
  const displayDate = event.time_anchor_date || event.time_anchor

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => navigate('/')}
            className="flex items-center text-gray-600"
          >
            <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="text-red-600 text-sm hover:text-red-800 disabled:opacity-50"
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 mb-4">
          <div className="flex justify-between items-start mb-4">
            <h1 className="text-2xl font-bold text-gray-900 flex-1">
              {event.title || 'Untitled Memory'}
            </h1>
            {isDraft && (
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                Draft
              </span>
            )}
          </div>

          {displayDate && (
            <p className="text-gray-600 mb-2">{formatDate(displayDate)}</p>
          )}

          {event.place && (
            <p className="text-gray-500 mb-4">{event.place}</p>
          )}

          {event.summary && (
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">{event.summary}</p>
            </div>
          )}

          {isDraft && (
            <button
              onClick={() => navigate(`/record/${event.id}`)}
              className="mt-4 w-full py-3 bg-blue-600 text-white rounded-lg font-medium"
            >
              Continue Recording
            </button>
          )}
        </div>

        {event.recordings && event.recordings.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Recordings ({event.recordings.length})
            </h2>
            <div className="space-y-3">
              {event.recordings.map((recording) => (
                <div
                  key={recording.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {recording.recording_type === 'initial_story'
                        ? 'Initial Story'
                        : 'Follow-up Answer'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatDate(recording.created_at)}
                      {recording.duration_seconds &&
                        ` · ${formatDuration(recording.duration_seconds)}`}
                    </p>
                    {recording.transcript && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {recording.transcript}
                      </p>
                    )}
                  </div>
                  {recording.audio_url && (
                    <button
                      onClick={() => playAudio(recording)}
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        playingId === recording.id
                          ? 'bg-red-600 text-white'
                          : 'bg-blue-600 text-white'
                      }`}
                      aria-label={
                        playingId === recording.id ? 'Pause' : 'Play recording'
                      }
                    >
                      {playingId === recording.id ? (
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      )}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        </div>
    </div>
  )
}