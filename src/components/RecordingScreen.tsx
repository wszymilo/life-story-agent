import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AudioRecorder } from './AudioRecorder'
import { addRecording, createEvent, retryTranscribe } from '../services/events'

type RecordingState = 'idle' | 'uploading' | 'transcribing' | 'complete' | 'error'

export function RecordingScreen() {
  const navigate = useNavigate()
  const [state, setState] = useState<RecordingState>('idle')
  const [transcript, setTranscript] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [recordingId, setRecordingId] = useState<string>('')
  const [retrying, setRetrying] = useState<boolean>(false)

  const handleRecordingComplete = async (audioBlob: Blob) => {
    try {
      setState('uploading')
      setError('')

      const event = await createEvent({ title: 'My Life Story' })

      try {
        setState('transcribing')
        const recording = await addRecording(event.id, audioBlob, 'initial_story')
        setRecordingId(recording.id)

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
        // Check if we have audio_url (from transcription error with saved recording)
        const errorWithAudio = (err as any)
        if (errorWithAudio.audioUrl || (err as Error).message?.includes('saved')) {
          // Extract recording ID from error response if available
          setError('Transcription failed. Your recording is saved.')
          setRecordingId(errorWithAudio.recordingId || event.id)
          setState('error')
        } else {
          throw err
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process recording')
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
      setError(err instanceof Error ? err.message : 'Failed to retry transcription')
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
      <div className="min-h-screen bg-gray-50 px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-green-600 text-5xl mb-4">✓</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Story Recorded!
            </h1>
            <p className="text-gray-600 mb-6">{transcript}</p>
            <button
              onClick={() => navigate('/')}
              className="w-full py-4 bg-blue-600 text-white rounded-lg font-medium text-lg hover:bg-blue-700"
            >
              Go to Timeline
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              {retrying ? 'Retrying...' : 'Something went wrong'}
            </h1>
            <p className="text-gray-600 mb-6">{error}</p>

            {recordingId && !retrying && (
              <button
                onClick={handleRetryTranscribe}
                className="w-full py-4 bg-blue-600 text-white rounded-lg font-medium text-lg hover:bg-blue-700 mb-4"
              >
                Retry Transcription
              </button>
            )}

            <button
              onClick={handleRetry}
              className="w-full py-4 bg-gray-200 text-gray-700 rounded-lg font-medium text-lg hover:bg-gray-300"
            >
              Record New Story
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Tell Your Story</h1>
          <p className="text-gray-600 mt-2">
            Press the button below and share your life story
          </p>
        </div>

        {state === 'uploading' && (
          <div className="text-center mb-4">
            <p className="text-blue-600 font-medium">Uploading your recording...</p>
          </div>
        )}

        {state === 'transcribing' && (
          <div className="text-center mb-4">
            <p className="text-blue-600 font-medium">Processing your story...</p>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md p-6">
          <AudioRecorder onRecordingComplete={handleRecordingComplete} />
        </div>

        <p className="text-center text-gray-500 text-sm mt-6">
          {state === 'idle'
            ? 'Tap the red circle to start recording'
            : state === 'uploading'
            ? 'Please wait while we upload your recording'
            : 'Please wait while we process your story'}
        </p>
      </div>
    </div>
  )
}