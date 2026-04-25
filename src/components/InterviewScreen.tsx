import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { AudioRecorder } from './AudioRecorder'
import { TopBar } from './TopBar'
import { LoadingScreen } from './LoadingScreen'
import {
  analyzeEvent,
  generateFollowUp,
  getEventWithQuestions,
  generateTTS,
  createQuestion,
  FollowUpQuestion,
  EventWithQuestions,
} from '../services/interview'
import { addRecording, updateRecordingTranscript } from '../services/events'
import { encrypt, decrypt } from '../lib/crypto'
import { extractErrorMessage } from '../lib/errors'
import { useAudioPlayer } from '../hooks/useAudioPlayer'
import { useEncryption } from '../hooks/useEncryption'

type InterviewState = 'loading' | 'analyzing' | 'ready' | 'playing' | 'recording' | 'complete' | 'error'

export function InterviewScreen() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { key, isReady } = useEncryption()
  const [state, setState] = useState<InterviewState>('loading')
  const [statusMessage, setStatusMessage] = useState<string>('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [event, setEvent] = useState<EventWithQuestions | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<FollowUpQuestion | null>(null)
  const [error, setError] = useState<string>('')
  const [plaintextTranscript, setPlaintextTranscript] = useState<string>('')
  const [showRecordLabel, setShowRecordLabel] = useState(true)
  const isLoadingRef = useRef(false)
  const { play } = useAudioPlayer()

  const decryptEventData = useCallback(async (eventData: EventWithQuestions): Promise<EventWithQuestions> => {
    if (!key) return eventData

    const decryptedRecordings = await Promise.all(
      (eventData.recordings || []).map(async (r) => ({
        ...r,
        transcript: r.transcript ? await decrypt(r.transcript, key) : null,
      }))
    )

    const decryptedQuestions = await Promise.all(
      (eventData.follow_up_questions || []).map(async (q) => ({
        ...q,
        question_text: q.question_text ? await decrypt(q.question_text, key) : '',
      }))
    )

    return {
      ...eventData,
      title: eventData.title ? await decrypt(eventData.title, key) : null,
      recordings: decryptedRecordings,
      follow_up_questions: decryptedQuestions,
    }
  }, [key])

  useEffect(() => {
    if (!eventId || isLoadingRef.current || !isReady) return

    const loadData = async () => {
      isLoadingRef.current = true
      setState('analyzing')

      try {
        const eventData = await getEventWithQuestions(eventId)
        const decryptedEvent = await decryptEventData(eventData)
        setEvent(decryptedEvent)

        // Build plaintext transcript from all recordings
        const transcripts = (decryptedEvent.recordings || [])
          .map(r => r.transcript)
          .filter((t): t is string => !!t)
        const combinedTranscript = transcripts.join('\n\n')
        setPlaintextTranscript(combinedTranscript)

        if (decryptedEvent.follow_up_questions && decryptedEvent.follow_up_questions.length > 0) {
          const unanswered = decryptedEvent.follow_up_questions.find(q => !q.was_answered && !q.audio_url)
          if (unanswered) {
            setCurrentQuestion(unanswered)
            setState('ready')
          } else {
            setState('complete')
          }
        } else {
          setState('analyzing')
          await analyzeEvent(eventId, combinedTranscript)
          const existingQuestions = decryptedEvent.follow_up_questions?.map(q => q.question_text) || []
          const question = await generateFollowUp(eventId, combinedTranscript, existingQuestions)
          // Encrypt and store the question
          if (key) {
            const encryptedQuestion = await encrypt(question.question_text, key)
            const storedQuestion = await createQuestion(eventId, {
              question_text: encryptedQuestion,
              question_type: question.question_type,
            })
            setCurrentQuestion({
              ...question,
              id: storedQuestion.id,
              event_id: eventId,
              was_answered: false,
              sequence_order: storedQuestion.sequence_order,
              created_at: storedQuestion.created_at,
            })
          }
          setState('ready')
        }
      } catch (err) {
        setError(extractErrorMessage(err, t('interview.loadError')))
        setState('error')
      } finally {
        isLoadingRef.current = false
      }
    }

    loadData()
  }, [eventId, isReady, key, decryptEventData, t])

  const playQuestionAudio = async () => {
    if (!currentQuestion || !eventId) return

    try {
      setState('playing')
      const result = await generateTTS(currentQuestion.question_text)
      await play(result.audio_url, {
        onEnded: () => {
          setState('ready')
        },
        onError: () => {
          setError(t('interview.playError'))
          setState('ready')
        },
      })
    } catch (err) {
      setError(extractErrorMessage(err, t('interview.playError')))
      setState('ready')
    }
  }

  const handleAudioComplete = async (audioBlob: Blob) => {
    if (!eventId || !currentQuestion || !key) return

    setStatusMessage('Uploading your recording...')
    try {
      setStatusMessage('Processing your response...')
      const recording = await addRecording(eventId, audioBlob, 'follow_up_response')
      if (recording.transcript) {
        const encryptedTranscript = await encrypt(recording.transcript, key)
        await updateRecordingTranscript(recording.id, encryptedTranscript)
      }
      window.location.reload()
    } catch (err) {
      setError(extractErrorMessage(err, t('interview.saveError')))
      setState('ready')
      setStatusMessage('')
    }
  }

  const handleNextQuestion = async () => {
    if (!eventId || !key) return

    setIsGenerating(true)
    try {
      const existingQuestions = event?.follow_up_questions?.map(q => q.question_text) || []
      const question = await generateFollowUp(eventId, plaintextTranscript, existingQuestions)
      const encryptedQuestion = await encrypt(question.question_text, key)
      const storedQuestion = await createQuestion(eventId, {
        question_text: encryptedQuestion,
        question_type: question.question_type,
      })
      setCurrentQuestion({
        ...question,
        id: storedQuestion.id,
        event_id: eventId,
        was_answered: false,
        sequence_order: storedQuestion.sequence_order,
        created_at: storedQuestion.created_at,
      })
      setState('ready')
    } catch (err) {
      setError(extractErrorMessage(err, t('interview.generateError')))
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
      <LoadingScreen
        message={
          state === 'analyzing'
            ? t('interview.analyzing')
            : t('interview.loading')
        }
      />
    )
  }

  if (state === 'error') {
    return (
      <div className="min-h-screen bg-gray-50">
        <TopBar title={t('interview.errorTitle')} />
        <div className="max-w-2xl mx-auto p-4">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-red-600 mb-4">{t('common.error')}</h2>
            <p className="text-gray-600 mb-4 text-lg">{error}</p>
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => window.location.reload()}
                disabled={isGenerating}
                className="flex-1 py-3 min-h-12 bg-blue-600 text-white text-lg rounded-lg font-medium disabled:opacity-50"
              >
                {t('interview.errorRetry')}
              </button>
              <button
                type="button"
                onClick={() => navigate('/')}
                disabled={isGenerating}
                className="flex-1 py-3 min-h-12 bg-gray-200 text-gray-700 text-lg rounded-lg font-medium disabled:opacity-50"
              >
                {t('interview.errorGoHome')}
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
        <TopBar title={t('interview.completeTitle')}  />
        <div className="max-w-2xl mx-auto p-4">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-green-600 text-5xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">{t('interview.completeHeading')}</h2>
            <p className="text-gray-600 mb-6 text-lg">
              {t('interview.completeMessage')}
            </p>
              <button
                type="button"
                onClick={handleEnd}
                className="w-full py-4 min-h-12 bg-blue-600 text-white text-lg rounded-lg font-medium"
              >
                {t('interview.goToTimeline')}
              </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar
        title={t('interview.title')}
        secondary={{ label: t('interview.endInterview'), onClick: handleEnd }}
        tertiaryLeft={
          <button
            type="button"
            onClick={handleNextQuestion}
            disabled={isGenerating}
            className="px-4 py-3 min-h-12 bg-blue-600 hover:bg-blue-700 text-white text-lg rounded-lg font-medium disabled:opacity-50"
          >
            {isGenerating ? t('interview.generating') : t('interview.nextQuestion')}
          </button>
        }
      />
      <div className="max-w-2xl mx-auto p-4">
        <div className="bg-white rounded-lg shadow-md p-6">
          <p className="text-gray-600 mb-6 text-lg">
            {event?.title || t('interview.title')}
          </p>

          {currentQuestion && (
            <div className="mb-6">
              <p className="text-lg text-gray-800 mb-4">{currentQuestion.question_text}</p>

              <div className="flex gap-4 mb-4">
                <button
                  type="button"
                  onClick={playQuestionAudio}
                  disabled={state === 'playing'}
                  className="flex-1 py-3 min-h-12 bg-blue-600 text-white text-lg rounded-lg font-medium disabled:opacity-50"
                >
                  {state === 'playing' ? t('interview.playing') : t('interview.playQuestion')}
                </button>
              </div>
            </div>
          )}

          <div className="border-t pt-6">
            {showRecordLabel && (
              <p className="text-gray-600 mb-4 text-lg">{t('interview.recordAnswer')}</p>
            )}
            <AudioRecorder
              onRecordingComplete={handleAudioComplete}
              onRecordingStopped={() => setShowRecordLabel(false)}
              disabled={state === 'playing'}
              statusMessage={statusMessage}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
