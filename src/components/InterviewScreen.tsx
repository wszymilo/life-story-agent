import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AudioRecorder } from './AudioRecorder'
import { TopBar } from './TopBar'
import {
  analyzeEvent,
  generateFollowUp,
  getEventWithQuestions,
  generateTTS,
  FollowUpQuestion,
  EventWithQuestions,
} from '../services/interview'
import { addRecording } from '../services/events'
import { extractErrorMessage } from '../lib/errors'

type InterviewState = 'loading' | 'analyzing' | 'ready' | 'playing' | 'recording' | 'complete' | 'error'

export function InterviewScreen() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const [state, setState] = useState<InterviewState>('loading')
  const [isUploading, setIsUploading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
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
        setError(extractErrorMessage(err, 'Failed to load event'))
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
      setError(extractErrorMessage(err, 'Failed to play audio'))
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
      setError(extractErrorMessage(err, 'Failed to save response'))
      setState('ready')
    } finally {
      setIsUploading(false)
    }
  }

  const handleNextQuestion = async () => {
    if (!eventId) return

    setIsGenerating(true)
    try {
      const question = await generateFollowUp(eventId)
      setCurrentQuestion(question as unknown as FollowUpQuestion)
      setState('ready')
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to generate next question'))
    } finally {
      setIsGenerating(false)
    }
  }

  const handleEnd = () => {
    if (eventId) {
      navigate(`/summary/${eventId}`)
    } else {
      navigate('/')
    }
  }

  if (state === 'loading' || state === 'analyzing') {
    return (
      <div className="min-h-screen bg-gray-50">
        <TopBar title="Interview"  />
        <div className="max-w-2xl mx-auto p-4 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">
            {state === 'loading' ? 'Loading...' : 'Analyzing your story...'}
          </h2>
          <p className="text-gray-600 mt-2 text-lg">
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
      <div className="min-h-screen bg-gray-50">
        <TopBar title="Error"  />
        <div className="max-w-2xl mx-auto p-4">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-red-600 mb-4">Something went wrong</h2>
            <p className="text-gray-600 mb-4 text-lg">{error}</p>
            <div className="flex gap-4">
              <button
                onClick={() => window.location.reload()}
                className="flex-1 py-3 min-h-12 bg-blue-600 text-white text-lg rounded-lg font-medium"
              >
                Try Again
              </button>
              <button
                onClick={() => navigate('/')}
                className="flex-1 py-3 min-h-12 bg-gray-200 text-gray-700 text-lg rounded-lg font-medium"
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
      <div className="min-h-screen bg-gray-50">
        <TopBar title="Interview Complete"  />
        <div className="max-w-2xl mx-auto p-4">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-green-600 text-5xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Interview Complete!</h2>
            <p className="text-gray-600 mb-6 text-lg">
              Thank you for sharing more about your life story.
            </p>
            <button
              onClick={handleEnd}
              className="w-full py-4 min-h-12 bg-blue-600 text-white text-lg rounded-lg font-medium"
            >
              Go to Timeline
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar
        title="Follow-up Question"
        secondary={{ label: 'End Interview', onClick: handleEnd }}
        tertiaryLeft={
          <button
            onClick={handleNextQuestion}
            disabled={isGenerating}
            className="px-4 py-3 min-h-12 bg-blue-600 hover:bg-blue-700 text-white text-lg rounded-lg font-medium disabled:opacity-50"
          >
            {isGenerating ? 'Generating...' : 'Next Question'}
          </button>
        }
      />
      <div className="max-w-2xl mx-auto p-4">
        <div className="bg-white rounded-lg shadow-md p-6">
          <p className="text-gray-600 mb-6 text-lg">
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
                  className="flex-1 py-3 min-h-12 bg-blue-600 text-white text-lg rounded-lg font-medium disabled:opacity-50"
                >
                  {state === 'playing' ? 'Playing...' : 'Play Question'}
                </button>
              </div>
            </div>
          )}

          <div className="border-t pt-6">
            <p className="text-gray-600 mb-4 text-lg">Record your answer:</p>
            <AudioRecorder
              onRecordingComplete={handleAudioComplete}
              disabled={state === 'playing'}
              isUploading={isUploading}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
