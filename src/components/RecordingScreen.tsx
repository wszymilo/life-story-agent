import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { AudioRecorder } from './AudioRecorder'
import { TopBar } from './TopBar'
import { addRecording, createEvent, retryTranscribe, updateRecordingTranscript, getEvent, EventData, RecordingError } from '../services/events'
import { encrypt } from '../lib/crypto'
import { extractErrorMessage } from '../lib/errors'
import { useEncryption } from '../hooks/useEncryption'

type RecordingState = 'idle' | 'uploading' | 'transcribing' | 'complete' | 'error'

export function RecordingScreen() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { eventId: urlEventId } = useParams<{ eventId?: string }>()
  const { key, isReady } = useEncryption()
  const [state, setState] = useState<RecordingState>('idle')
  const [transcript, setTranscript] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [recordingId, setRecordingId] = useState<string>('')
  const [eventId, setEventId] = useState<string>('')
  const [retrying, setRetrying] = useState<boolean>(false)
  const [title, setTitle] = useState<string>('')
  const [statusMessage, setStatusMessage] = useState<string>('')

  const loadExistingEvent = useCallback(async (id: string) => {
    try {
      const event: EventData = await getEvent(id)
      if (event.recordings && event.recordings.length > 0) {
        const lastRecording = event.recordings[event.recordings.length - 1]
        if (lastRecording.transcript && key) {
          // Note: encrypted transcript can't be shown without decryption
          // For MVP, we show a placeholder if transcript is encrypted
          setTranscript('[Encrypted transcript — will be decrypted after key loads]')
          setRecordingId(lastRecording.id)
        }
      }
      setState('idle')
    } catch (err) {
      setError(extractErrorMessage(err, t('recording.loadError')))
    }
  }, [key, t])

  useEffect(() => {
    if (urlEventId) {
      setEventId(urlEventId)
      loadExistingEvent(urlEventId)
    }
  }, [urlEventId, loadExistingEvent])

  const handleRecordingComplete = async (audioBlob: Blob) => {
    if (!key) {
      setError(t('recording.encryptionError'))
      setState('error')
      return
    }

    try {
      setState('uploading')
      setStatusMessage(t('recording.statusUploading'))
      setError('')

      const eventTitle = title.trim() || t('recording.titlePlaceholder')
      const encryptedTitle = await encrypt(eventTitle, key)
      const targetEventId = urlEventId || (await createEvent({ title: encryptedTitle })).id
      setEventId(targetEventId)

      try {
        setState('transcribing')
        setStatusMessage(t('recording.statusProcessing'))
        const recording = await addRecording(targetEventId, audioBlob, 'initial_story')
        setRecordingId(recording.id)
        setStatusMessage('')

        // Check if transcription succeeded
        if (recording.transcript) {
          // Encrypt transcript and store
          const encryptedTranscript = await encrypt(recording.transcript, key)
          await updateRecordingTranscript(recording.id, encryptedTranscript)
          setTranscript(recording.transcript)
          setState('complete')
        } else if (recording.detail && recording.detail.includes('saved')) {
          setError(t('recording.transcriptionFailed'))
          setState('error')
        } else {
          setTranscript(t('recording.transcriptPlaceholder'))
          setState('complete')
        }
      } catch (err) {
        setStatusMessage('')
        const errorWithAudio = err as RecordingError
        if (errorWithAudio.audioUrl || errorWithAudio.message?.includes('saved')) {
          setError(t('recording.transcriptionFailed'))
          setRecordingId(errorWithAudio.recordingId || targetEventId)
          setState('error')
        } else {
          throw err
        }
      }
    } catch (err) {
      setStatusMessage('')
      setError(extractErrorMessage(err, t('common.error')))
      setState('error')
    }
  }

  const handleRetryTranscribe = async () => {
    if (!recordingId || !key) return

    setRetrying(true)
    setError('')

    try {
      const recording = await retryTranscribe(recordingId)
      if (recording.transcript) {
        const encryptedTranscript = await encrypt(recording.transcript, key)
        await updateRecordingTranscript(recording.id, encryptedTranscript)
        setTranscript(recording.transcript)
        setState('complete')
        setError('')
      }
    } catch (err) {
      setError(extractErrorMessage(err, t('recording.retryTranscription')))
    } finally {
      setRetrying(false)
    }
  }

  const handleRetry = () => {
    setState('idle')
    setError('')
    setTranscript('')
    setRecordingId('')
  }

  if (!isReady && !urlEventId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">{t('recording.securing')}</p>
        </div>
      </div>
    )
  }

  if (state === 'complete') {
    return (
      <div className="min-h-screen bg-gray-50">
        <TopBar title={t('recording.successTitle')} back={{ href: '/' }} />
        <div className="max-w-2xl mx-auto p-4">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-green-600 text-5xl mb-4">✓</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              {t('recording.successHeading')}
            </h1>
            <p className="text-gray-600 mb-6 text-lg">{transcript}</p>
            <div className="flex flex-col gap-3">
              <button
                type="button"
                onClick={() => navigate(`/interview/${eventId}`)}
                className="w-full py-4 min-h-12 bg-blue-600 text-white rounded-lg font-medium text-lg hover:bg-blue-700"
              >
                {t('recording.continueInterview')}
              </button>
              <button
                type="button"
                onClick={() => navigate('/')}
                className="w-full py-3 text-gray-600 hover:text-gray-800 text-lg"
              >
                {t('recording.skipForNow')}
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div className="min-h-screen bg-gray-50">
        <TopBar title={t('recording.errorTitle')} back={{ href: '/' }} />
        <div className="max-w-2xl mx-auto p-4">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              {retrying ? t('recording.retrying') : t('recording.errorTitle')}
            </h1>
            <p className="text-gray-600 mb-6 text-lg">{error}</p>

            {recordingId && !retrying && (
              <button
                type="button"
                onClick={handleRetryTranscribe}
                disabled={retrying}
                className="w-full py-4 min-h-12 bg-blue-600 text-white rounded-lg font-medium text-lg hover:bg-blue-700 mb-4 disabled:opacity-50"
              >
                {retrying ? t('recording.retrying') : t('recording.retryTranscription')}
              </button>
            )}

            <button
              type="button"
              onClick={handleRetry}
              className="w-full py-4 min-h-12 bg-gray-200 text-gray-700 rounded-lg font-medium text-lg hover:bg-gray-300"
            >
              {t('recording.recordNew')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar title={t('recording.title')} back={{ href: '/' }} />
      <div className="max-w-2xl mx-auto p-4">
        <div className="text-center mb-6">
          <p className="text-gray-600 text-lg">
            {t('recording.instruction')}
          </p>
        </div>

        <div className="mb-4">
          <label htmlFor="title" className="block text-lg font-medium text-gray-700 mb-2">
            {t('recording.titleLabel')}
          </label>
          <input
            id="title"
            name="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={t('recording.titlePlaceholder')}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg min-h-12"
            maxLength={100}
          />
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <AudioRecorder onRecordingComplete={handleRecordingComplete} statusMessage={statusMessage} />
        </div>
      </div>
    </div>
  )
}
