import { useEffect, useRef } from 'react'
import { useRecorder } from '../hooks/useRecorder'

interface AudioRecorderProps {
  onRecordingComplete?: (blob: Blob) => void
  disabled?: boolean
  isUploading?: boolean
}

export function AudioRecorder({ onRecordingComplete, disabled, isUploading }: AudioRecorderProps) {
  const {
    startRecording,
    stopRecording,
    reset,
    isRecording,
    duration,
    audioBlob,
    error,
  } = useRecorder()

  const prevBlobRef = useRef<Blob | null>(null)

  useEffect(() => {
    if (audioBlob && audioBlob !== prevBlobRef.current && onRecordingComplete) {
      prevBlobRef.current = audioBlob
      onRecordingComplete(audioBlob)
    }
  }, [audioBlob, onRecordingComplete])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handleRecord = async () => {
    await startRecording()
  }

  const handleStop = () => {
    stopRecording()
  }

  const handleReset = () => {
    prevBlobRef.current = null
    reset()
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <div className="text-red-600 text-xl mb-4">{error}</div>
        <button
          onClick={handleReset}
          className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center p-8">
      {isRecording && (
        <div className="flex items-center gap-3 mb-6">
          <span className="w-4 h-4 bg-red-600 rounded-full animate-pulse" />
          <span className="text-red-600 font-medium">Recording...</span>
        </div>
      )}

      <div className="text-4xl font-bold text-gray-900 mb-8">
        {formatTime(duration)}
      </div>

      {!isRecording && !audioBlob && (
        <button
          onClick={handleRecord}
          disabled={disabled}
          className="w-24 h-24 bg-red-600 rounded-full flex items-center justify-center hover:bg-red-700 transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Start recording"
        >
          <span className="w-8 h-8 bg-white rounded-full" />
        </button>
      )}

      {isRecording && (
        <button
          onClick={handleStop}
          disabled={disabled}
          className="w-24 h-24 bg-gray-900 rounded-full flex items-center justify-center hover:bg-gray-800 transition-colors shadow-lg disabled:opacity-50"
          aria-label="Stop recording"
        >
          <span className="w-8 h-8 bg-white rounded" />
        </button>
      )}

      {audioBlob && !isUploading && (
        <div className="flex flex-col items-center gap-4">
          <div className="text-green-600 font-medium">Recording saved!</div>
          <button
            onClick={handleReset}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            Record Another
          </button>
        </div>
      )}

      {audioBlob && isUploading && (
        <div className="flex flex-col items-center gap-4">
          <div className="text-blue-600 font-medium">Uploading...</div>
        </div>
      )}

      <p className="text-gray-500 text-sm mt-8 text-center max-w-xs">
        {isRecording
          ? 'Tap the square to stop recording'
          : 'Tap the red circle to start recording'}
      </p>
    </div>
  )
}