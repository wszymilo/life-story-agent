import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { completeEvent, CompletedEvent } from '../services/events'
import { generateTTS } from '../services/interview'

type SummaryState = 'loading' | 'ready' | 'playing' | 'error'

export function SummaryScreen() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const [state, setState] = useState<SummaryState>('loading')
  const [event, setEvent] = useState<CompletedEvent | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [error, setError] = useState<string>('')
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const loadEvent = async () => {
    if (!eventId) { return }

    try {
      setState('loading')
      setError('')

      const completedEvent = await completeEvent(eventId)
      setEvent(completedEvent)
      setState('ready')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate summary')
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
        setError(err instanceof Error ? err.message : 'Failed to generate summary')
        setState('error')
      }
    }

    fetchData()
  }, [eventId, event])

  const handlePlaySummary = async () => {
    if (!event?.summary) return

    try {
      setIsPlaying(true)
      setState('playing')

      const { audio_url } = await generateTTS(event.summary)

      const audio = new Audio(audio_url)
      audioRef.current = audio

      audio.onended = () => {
        setIsPlaying(false)
        setState('ready')
      }

      audio.onerror = () => {
        setIsPlaying(false)
        setState('ready')
        setError('Playback failed')
      }

      await audio.play()
    } catch (err) {
      setIsPlaying(false)
      setState('ready')
      setError(err instanceof Error ? err.message : 'Failed to generate audio')
    }
  }

  const handleConfirm = () => {
    navigate('/')
  }

  if (state === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">Generating your story summary...</p>
        </div>
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <p className="text-red-600 text-lg mb-4">{error}</p>
          <button
            onClick={loadEvent}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
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
        {event?.title && (
          <h1 className="text-2xl font-bold text-gray-900 mb-4 text-center">
            {event.title}
          </h1>
        )}

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
            className="w-full py-4 bg-blue-600 text-white rounded-xl font-medium text-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
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
            className="w-full py-4 bg-green-600 text-white rounded-xl font-medium text-lg hover:bg-green-700"
          >
            Save & Continue to Timeline
          </button>
        </div>
      </div>
    </div>
  )
}