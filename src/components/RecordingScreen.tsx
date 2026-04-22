import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AudioRecorder } from './AudioRecorder'
import { TopBar } from './TopBar'
import { addRecording, createEvent, retryTranscribe, getEvent, EventData } from '../services/events'
import { extractErrorMessage } from '../lib/errors'

type RecordingState = 'idle' | 'uploading' | 'transcribing' | 'complete' | 'error'

export function RecordingScreen() {
  const navigate = useNavigate()
  const { eventId: urlEventId } = useParams<{ eventId?: string }>()
  const [state, setState] = useState<RecordingState>('idle')
  const [transcript, setTranscript] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [recordingId, setRecordingId] = useState<string>('')
  const [eventId, setEventId] = useState<string>('')
  const [retrying, setRetrying] = useState<boolean>(false)
  const [title, setTitle] = useState<string>('')
  const [statusMessage, setStatusMessage] = useState<string>('')

  const loadExistingEvent = async (id: string) => {
    try {
      const event: EventData = await getEvent(id)
      if (event.recordings && event.recordings.length > 0) {
        const lastRecording = event.recordings[event.recordings.length - 1]
        if (lastRecording.transcript) {
          setTranscript(lastRecording.transcript)
          setRecordingId(lastRecording.id)
        }
      }
      setState('idle')
    } catch (err) {
      console.error('Failed to load event:', err)
    }
  }

  useEffect(() => {
    if (urlEventId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setEventId(urlEventId)
      loadExistingEvent(urlEventId)
    }
  }, [urlEventId])

  const handleRecordingComplete = async (audioBlob: Blob) => {
    try {
      setState('uploading')
      setStatusMessage('Uploading your recording...')
      setError('')

      const eventTitle = title.trim() || 'My Life Story'
      const targetEventId = urlEventId || (await createEvent({ title: eventTitle })).id
      setEventId(targetEventId)

      try {
        setState('transcribing')
        setStatusMessage('Processing your story...')
        const recording = await addRecording(targetEventId, audioBlob, 'initial_story')
        setRecordingId(recording.id)
        setStatusMessage('')

        // Check if transcription succeeded
        if (recording.transcript) {
          setTranscript(recording.transcript)
          setState('complete')
        } else if (recording.detail && recording.detail.includes('saved')) {
          // Transcription failed but audio saved - show retry option
          setError('Transcription failed. Your recording is saved.')
          setState('error')
        } else {
          setTranscript('Your recording has been saved. Transcription will be available soon.')
          setState('complete')
        }
      } catch (err) {
        setStatusMessage('')
        // Check if we have audio_url (from transcription error with saved recording)
        const errorWithAudio = (err as any)
        if (errorWithAudio.audioUrl || (err as Error).message?.includes('saved')) {
          // Extract recording ID from error response if available
          setError('Transcription failed. Your recording is saved.')
          setRecordingId(errorWithAudio.recordingId || targetEventId)
          setState('error')
        } else {
          throw err
        }
      }
    } catch (err) {
      setStatusMessage('')
      setError(extractErrorMessage(err, 'Failed to process recording'))
      setState('error')
    }
  }

  const handleRetryTranscribe = async () => {
    if (!recordingId) return

    setRetrying(true)
    setError('')

    try {
      const recording = await retryTranscribe(recordingId)
      if (recording.transcript) {
        setTranscript(recording.transcript)
        setState('complete')
        setError('')
      }
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to retry transcription'))
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

  if (state === 'complete') {
    return (
      <div className="min-h-screen bg-gray-50">
        <TopBar title="Story Recorded" back={{ href: '/' }} />
        <div className="max-w-2xl mx-auto p-4">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-green-600 text-5xl mb-4">✓</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Story Recorded!
            </h1>
            <p className="text-gray-600 mb-6 text-lg">{transcript}</p>
            <div className="flex flex-col gap-3">
              <button
                onClick={() => navigate(`/interview/${eventId}`)}
                className="w-full py-4 min-h-12 bg-blue-600 text-white rounded-lg font-medium text-lg hover:bg-blue-700"
              >
                Continue to Interview
              </button>
              <button
                onClick={() => navigate('/')}
                className="w-full py-3 text-gray-600 hover:text-gray-800 text-lg"
              >
                Skip for now
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
        <TopBar title="Something went wrong" back={{ href: '/' }} />
        <div className="max-w-2xl mx-auto p-4">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              {retrying ? 'Retrying...' : 'Something went wrong'}
            </h1>
            <p className="text-gray-600 mb-6 text-lg">{error}</p>

            {recordingId && !retrying && (
              <button
                onClick={handleRetryTranscribe}
                className="w-full py-4 min-h-12 bg-blue-600 text-white rounded-lg font-medium text-lg hover:bg-blue-700 mb-4"
              >
                Retry Transcription
              </button>
            )}

            <button
              onClick={handleRetry}
              className="w-full py-4 min-h-12 bg-gray-200 text-gray-700 rounded-lg font-medium text-lg hover:bg-gray-300"
            >
              Record New Story
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar title="Tell Your Story" back={{ href: '/' }} />
      <div className="max-w-2xl mx-auto p-4">
        <div className="text-center mb-6">
          <p className="text-gray-600 text-lg">
            Press the button below and share your life story
          </p>
        </div>

        <div className="mb-4">
          <label htmlFor="title" className="block text-lg font-medium text-gray-700 mb-2">
            Title (optional)
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., My childhood in Warsaw"
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
