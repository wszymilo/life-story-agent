import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AudioRecorder } from './AudioRecorder'
import {
  analyzeEvent,
  generateFollowUp,
  skipFollowUp,
  getEventWithQuestions,
  generateTTS,
  FollowUpQuestion,
  EventWithQuestions,
} from '../services/interview'
import { addRecording } from '../services/events'

type InterviewState = 'loading' | 'analyzing' | 'ready' | 'playing' | 'recording' | 'complete' | 'error'

export function InterviewScreen() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const [state, setState] = useState<InterviewState>('loading')
  const [isUploading, setIsUploading] = useState(false)
  const [event, setEvent] = useState<EventWithQuestions | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<FollowUpQuestion | null>(null)
  const [error, setError] = useState<string>('')
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const isLoadingRef = useRef(false)

  useEffect(() => {
    if (!eventId || isLoadingRef.current) return

    const loadData = async () => {
      isLoadingRef.current = true
      setState('analyzing')

      try {
        const eventData = await getEventWithQuestions(eventId)
        setEvent(eventData)

        if (eventData.follow_up_questions && eventData.follow_up_questions.length > 0) {
          const unanswered = eventData.follow_up_questions.find(q => !q.was_answered && !q.audio_url)
          if (unanswered) {
            setCurrentQuestion(unanswered)
            setState('ready')
          } else {
            setState('complete')
          }
        } else {
          setState('analyzing')
          await analyzeEvent(eventId)
          const question = await generateFollowUp(eventId)
          setCurrentQuestion(question as unknown as FollowUpQuestion)
          setState('ready')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load event')
        setState('error')
      } finally {
        isLoadingRef.current = false
      }
    }

    loadData()
  }, [eventId])

  const playQuestionAudio = async () => {
    if (!currentQuestion || !eventId) return

    try {
      setState('playing')
      const result = await generateTTS(currentQuestion.question_text)

      if (audioRef.current) {
        audioRef.current.src = result.audio_url
        
        audioRef.current.onloadeddata = () => {
          console.log('Audio loaded, duration:', audioRef.current?.duration)
          audioRef.current?.play().catch(err => {
            console.error('Play error:', err)
            setError('Failed to play audio')
            setState('ready')
          })
        }
        
        audioRef.current.onended = () => {
          console.log('Audio playback ended')
          setState('ready')
        }
        
        audioRef.current.onerror = (e) => {
          console.error('Audio error event:', e)
          setError('Failed to play audio')
          setState('ready')
        }
      }
    } catch (err) {
      console.error('TTS generation error:', err)
      setError(err instanceof Error ? err.message : 'Failed to play audio')
      setState('ready')
    }
  }

  const handleAudioComplete = async (audioBlob: Blob) => {
    if (!eventId || !currentQuestion) return

    setIsUploading(true)
    try {
      await addRecording(eventId, audioBlob, 'follow_up_response')
      window.location.reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save response')
      setState('ready')
    } finally {
      setIsUploading(false)
    }
  }

  const handleSkip = async () => {
    if (!eventId || !currentQuestion) return

    try {
      await skipFollowUp(eventId, currentQuestion.id)
      window.location.reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to skip question')
    }
  }

  const handleNextQuestion = async () => {
    if (!eventId) return

    try {
      const question = await generateFollowUp(eventId)
      setCurrentQuestion(question as unknown as FollowUpQuestion)
      setState('ready')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate next question')
    }
  }

  const handleEnd = () => {
    navigate('/')
  }

  if (state === 'loading' || state === 'analyzing') {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-8">
        <div className="max-w-2xl mx-auto text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">
            {state === 'loading' ? 'Loading...' : 'Analyzing your story...'}
          </h2>
          <p className="text-gray-600 mt-2">
            {state === 'analyzing'
              ? 'Extracting details and preparing questions for you'
              : 'Please wait...'}
          </p>
        </div>
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-red-600 mb-4">Something went wrong</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="flex gap-4">
              <button
                onClick={() => window.location.reload()}
                className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium"
              >
                Try Again
              </button>
              <button
                onClick={() => navigate('/')}
                className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium"
              >
                Go Home
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (state === 'complete') {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-green-600 text-5xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Interview Complete!</h2>
            <p className="text-gray-600 mb-6">
              Thank you for sharing more about your life story.
            </p>
            <button
              onClick={handleEnd}
              className="w-full py-4 bg-blue-600 text-white rounded-lg font-medium text-lg"
            >
              Go to Timeline
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Follow-up Question</h1>
          <p className="text-gray-600 mb-6">
            {event?.title || 'Your Life Story'}
          </p>

          {currentQuestion && (
            <div className="mb-6">
              <p className="text-lg text-gray-800 mb-4">{currentQuestion.question_text}</p>

              <audio
                ref={audioRef}
                onEnded={() => setState('ready')}
                className="hidden"
              />

              <div className="flex gap-4 mb-4">
                <button
                  onClick={playQuestionAudio}
                  disabled={state === 'playing'}
                  className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50"
                >
                  {state === 'playing' ? 'Playing...' : 'Play Question'}
                </button>
              </div>
            </div>
          )}

          <div className="border-t pt-6">
            <p className="text-gray-600 mb-4">Record your answer:</p>
            <AudioRecorder
              onRecordingComplete={handleAudioComplete}
              disabled={state === 'playing'}
              isUploading={isUploading}
            />
          </div>

          <div className="flex gap-4 mt-6">
            <button
              onClick={handleSkip}
              className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium"
            >
              Skip Question
            </button>
            <button
              onClick={handleNextQuestion}
              className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium"
            >
              Next Question
            </button>
          </div>

          <button
            onClick={handleEnd}
            className="w-full mt-4 py-2 text-gray-600 hover:text-gray-800"
          >
            End Interview
          </button>
        </div>
      </div>
    </div>
  )
}