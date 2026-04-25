import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { completeEvent, getEvent, updateEvent, EventData, AudioRecording, QuestionAnswer } from '../services/events'
import { getEventWithQuestions } from '../services/interview'
import { generateTTS } from '../services/interview'
import { encrypt, decrypt } from '../lib/crypto'
import { TopBar } from './TopBar'
import { LoadingScreen } from './LoadingScreen'
import { ErrorFallback } from './ErrorFallback'
import { extractErrorMessage } from '../lib/errors'
import { useAudioPlayer } from '../hooks/useAudioPlayer'
import { useEncryption } from '../hooks/useEncryption'

type SummaryState = 'loading' | 'ready' | 'playing' | 'error'

export function SummaryScreen() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { key, isReady } = useEncryption()
  const [state, setState] = useState<SummaryState>('loading')
  const [event, setEvent] = useState<EventData | null>(null)
  const [error, setError] = useState<string>('')
  const { play, isPlaying } = useAudioPlayer()

  const loadEvent = useCallback(async () => {
    if (!eventId || !key) return

    try {
      setState('loading')
      setError('')

      // Fetch event with recordings and questions
      const [eventData, eventWithQuestions] = await Promise.all([
        getEvent(eventId),
        getEventWithQuestions(eventId),
      ])

      // Decrypt transcripts from recordings
      const decryptedRecordings: AudioRecording[] = await Promise.all(
        (eventWithQuestions.recordings || []).map(async (r) => ({
          ...r,
          transcript: r.transcript ? await decrypt(r.transcript, key) : null,
        }))
      )

      // Build plaintext transcripts array
      const transcripts = decryptedRecordings
        .map(r => r.transcript)
        .filter((t): t is string => !!t)

      // Build Q&A from follow-up questions
      const questionsAndAnswers: QuestionAnswer[] = []
      for (const q of eventWithQuestions.follow_up_questions || []) {
        if (q.was_answered && q.audio_url) {
          const answerRecording = decryptedRecordings.find(r => r.audio_url === q.audio_url)
          if (answerRecording?.transcript) {
            const decryptedQuestion = q.question_text ? await decrypt(q.question_text, key) : ''
            questionsAndAnswers.push({
              question: decryptedQuestion,
              answer: answerRecording.transcript,
            })
          }
        }
      }

      // Call complete with plaintext
      const completedEvent = await completeEvent(eventId, transcripts, questionsAndAnswers)

      // Encrypt and store summary + title
      const encryptedTitle = await encrypt(completedEvent.title, key)
      const encryptedSummary = await encrypt(completedEvent.summary, key)
      await updateEvent(eventId, {
        title: encryptedTitle,
        summary: encryptedSummary,
        status: 'complete',
        time_anchor_date: completedEvent.time_anchor_date,
      })

      // Set decrypted event for display
      setEvent({
        ...eventData,
        title: completedEvent.title,
        summary: completedEvent.summary,
        status: 'complete',
        recordings: decryptedRecordings,
      })
      setState('ready')
    } catch (err) {
      setError(extractErrorMessage(err, t('summary.generateError')))
      setState('error')
    }
  }, [eventId, key, t])

  useEffect(() => {
    if (!eventId || event || !isReady || !key) return

    loadEvent()
  }, [eventId, event, isReady, key, loadEvent])

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
          setError(t('summary.playbackError'))
        },
      })
    } catch (err) {
      setState('ready')
      setError(extractErrorMessage(err, t('summary.generateError')))
    }
  }

  const handleConfirm = () => {
    navigate('/')
  }

  if (state === 'loading') {
    return <LoadingScreen message={t('summary.loading')} />
  }

  if (state === 'error') {
    return <ErrorFallback message={error} onRetry={loadEvent} />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar title={event?.title || t('summary.yourStory')} />
      <div className="max-w-2xl mx-auto p-4">
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-3">
            {t('summary.yourStory')}
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
            type="button"
            onClick={handlePlaySummary}
            disabled={isPlaying}
            className="w-full py-4 min-h-12 bg-blue-600 text-white text-lg rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isPlaying ? (
              <span className="animate-pulse">{t('summary.playing')}</span>
            ) : (
              <span className="flex items-center gap-2">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
                {t('summary.listen')}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={handleConfirm}
            className="w-full py-4 min-h-12 bg-green-600 text-white text-lg rounded-xl font-medium hover:bg-green-700"
          >
            {t('summary.saveAndContinue')}
          </button>
        </div>
      </div>
    </div>
  )
}
