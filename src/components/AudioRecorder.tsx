import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useRecorder } from '../hooks/useRecorder'

interface AudioRecorderProps {
  onRecordingComplete?: (blob: Blob) => void
  onRecordingStopped?: () => void
  disabled?: boolean
  isUploading?: boolean
  statusMessage?: string
}

export function AudioRecorder({ onRecordingComplete, onRecordingStopped, disabled, isUploading, statusMessage }: AudioRecorderProps) {
  const { t } = useTranslation()
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

  const handleStop = () => {
    onRecordingStopped?.()
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
          type="button"
          onClick={handleReset}
          className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium"
        >
          {t('common.tryAgain')}
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center p-8">
      {isRecording && (
        <div className="flex items-center gap-3 mb-6">
          <span className="w-4 h-4 bg-red-600 rounded-full animate-pulse" />
          <span className="text-red-600 font-medium">{t('common.recording')}</span>
        </div>
      )}

      {statusMessage && (
        <div className="mb-6" aria-live="polite">
          <p className="text-blue-600 font-medium text-lg">{statusMessage}</p>
        </div>
      )}

      <div className="text-4xl font-bold text-gray-900 mb-8">
        {formatTime(duration)}
      </div>

      {!isRecording && !audioBlob && (
        <button
          onClick={startRecording}
          disabled={disabled}
          className="w-24 h-24 bg-red-600 rounded-full flex items-center justify-center hover:bg-red-700 transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label={t('audioRecorder.startRecording')}
        >
          <span className="w-8 h-8 bg-white rounded-full" />
        </button>
      )}

      {isRecording && (
        <button
          onClick={handleStop}
          disabled={disabled}
          className="w-24 h-24 bg-gray-900 rounded-full flex items-center justify-center hover:bg-gray-800 transition-colors shadow-lg disabled:opacity-50"
          aria-label={t('audioRecorder.stopRecording')}
        >
          <span className="w-8 h-8 bg-white rounded" />
        </button>
      )}

      {audioBlob && isUploading && (
        <div className="flex flex-col items-center gap-4">
          <div className="text-blue-600 font-medium">{t('common.uploading')}</div>
        </div>
      )}

      {!audioBlob && (
        isRecording ? (
          <p className="text-gray-500 text-sm mt-8 text-center max-w-xs">
            {t('audioRecorder.tapToStop')}
          </p>
        ) : (
          <p className="text-gray-500 text-sm mt-8 text-center max-w-xs">
            {t('audioRecorder.tapToStart')}
          </p>
        )
      )}
    </div>
  )
}
