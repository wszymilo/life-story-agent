import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { completeEvent, CompletedEvent } from '../services/events'
import { generateTTS } from '../services/interview'
import { TopBar } from './TopBar'
import { LoadingScreen } from './LoadingScreen'
import { ErrorFallback } from './ErrorFallback'
import { extractErrorMessage } from '../lib/errors'
import { useAudioPlayer } from '../hooks/useAudioPlayer'

type SummaryState = 'loading' | 'ready' | 'playing' | 'error'

export function SummaryScreen() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const [state, setState] = useState<SummaryState>('loading')
  const [event, setEvent] = useState<CompletedEvent | null>(null)
  const [error, setError] = useState<string>('')
  const { play, isPlaying } = useAudioPlayer()

  const loadEvent = async () => {
    if (!eventId) { return }

    try {
      setState('loading')
      setError('')

      const completedEvent = await completeEvent(eventId)
      setEvent(completedEvent)
      setState('ready')
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to generate summary'))
      setState('error')
    }
  }

  useEffect(() => {
    if (!eventId || event) { return }

    const fetchData = async () => {
      try {
        setState('loading')
        setError('')

        const completedEvent = await completeEvent(eventId)
        setEvent(completedEvent)
        setState('ready')
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to generate summary'))
        setState('error')
      }
    }

    fetchData()
  }, [eventId, event])

  const handlePlaySummary = async () => {
    if (!event?.summary) return

    try {
      setState('playing')
      const { audio_url } = await generateTTS(event.summary)
      await play(audio_url, {
        onEnded: () => {
          setState('ready')
        },
        onError: () => {
          setState('ready')
          setError('Playback failed')
        },
      })
    } catch (err) {
      setState('ready')
      setError(extractErrorMessage(err, 'Failed to generate audio'))
    }
  }

  const handleConfirm = () => {
    navigate('/')
  }

  if (state === 'loading') {
    return <LoadingScreen message="Generating your story summary..." />
  }

  if (state === 'error') {
    return <ErrorFallback message={error} onRetry={loadEvent} />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar title={event?.title || 'Your Story'} />
      <div className="max-w-2xl mx-auto p-4">
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-3">
            Your Life Story
          </h2>
          <div className="prose prose-lg max-w-none">
            <p className="text-gray-700 text-lg leading-relaxed whitespace-pre-wrap">
              {event?.summary}
            </p>
          </div>
        </div>

        {error && (
          <p className="text-red-600 text-center mb-4">{error}</p>
        )}

        <div className="flex flex-col gap-3">
          <button
            onClick={handlePlaySummary}
            disabled={isPlaying}
            className="w-full py-4 min-h-12 bg-blue-600 text-white text-lg rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isPlaying ? (
              <span className="animate-pulse">Playing...</span>
            ) : (
              <span className="flex items-center gap-2">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
                Listen to Summary
              </span>
            )}
          </button>

          <button
            onClick={handleConfirm}
            className="w-full py-4 min-h-12 bg-green-600 text-white text-lg rounded-xl font-medium hover:bg-green-700"
          >
            Save & Continue to Timeline
          </button>
        </div>
      </div>
    </div>
  )
}
