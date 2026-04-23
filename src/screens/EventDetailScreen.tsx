import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getEvent, deleteEvent, streamAudio, EventData, AudioRecording } from '../services/events'
import { TopBar } from '../components/TopBar'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { LoadingScreen } from '../components/LoadingScreen'
import { ErrorFallback } from '../components/ErrorFallback'
import { useAudioPlayer } from '../hooks/useAudioPlayer'
import { useEventExport } from '../hooks/useEventExport'
import { useEncryption } from '../hooks/useEncryption'
import { decrypt } from '../lib/crypto'
import { formatDate, formatDuration } from '../lib/date'

export function EventDetailScreen() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const { key } = useEncryption()
  const [event, setEvent] = useState<EventData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [deleting, setDeleting] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showRecordAgainDialog, setShowRecordAgainDialog] = useState(false)
  const [playingRecordingId, setPlayingRecordingId] = useState<string | null>(null)
  const { play, pause } = useAudioPlayer()
  const { exporting, downloadExport } = useEventExport()

  useEffect(() => {
    if (!eventId) return

    const loadEvent = async () => {
      try {
        setLoading(true)
        setError('')
        const data = await getEvent(eventId)

        if (key) {
          // Decrypt title, summary, and transcripts
          const decryptedTitle = data.title ? await decrypt(data.title, key) : null
          const decryptedSummary = data.summary ? await decrypt(data.summary, key) : null
          const decryptedRecordings = await Promise.all(
            (data.recordings || []).map(async (r) => ({
              ...r,
              transcript: r.transcript ? await decrypt(r.transcript, key) : null,
            }))
          )

          setEvent({
            ...data,
            title: decryptedTitle,
            summary: decryptedSummary,
            recordings: decryptedRecordings,
          })
        } else {
          setEvent(data)
        }
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to load event'))
      } finally {
        setLoading(false)
      }
    }

    loadEvent()
  }, [eventId, key])

  const handleDelete = () => {
    if (!event?.id) return
    setShowDeleteDialog(true)
  }

  const handleConfirmDelete = async () => {
    if (!event?.id) return

    setDeleting(true)
    try {
      await deleteEvent(event.id)
      navigate('/')
    } catch (err) {
      alert(extractErrorMessage(err, 'Failed to delete'))
      setDeleting(false)
    }
  }

  const handleRecordAgain = () => {
    setShowRecordAgainDialog(true)
  }

  const handleConfirmRecordAgain = async () => {
    if (!event?.id) return

    setDeleting(true)
    try {
      await deleteEvent(event.id)
      navigate('/record')
    } catch (err) {
      alert(extractErrorMessage(err, 'Failed to delete draft'))
      setDeleting(false)
    }
  }

  const handleExport = () => {
    if (!event) return
    downloadExport(event)
  }

  const playAudio = async (recording: AudioRecording) => {
    if (!event?.id) return

    if (playingRecordingId === recording.id) {
      pause()
      setPlayingRecordingId(null)
      return
    }

    try {
      const blob = await streamAudio(event.id, recording.id)
      const url = URL.createObjectURL(blob)
      setPlayingRecordingId(recording.id)
      await play(url, {
        onEnded: () => {
          setPlayingRecordingId(null)
          URL.revokeObjectURL(url)
        },
        onError: () => {
          setPlayingRecordingId(null)
          URL.revokeObjectURL(url)
          alert('Failed to play audio')
        },
      })
    } catch (err) {
      setPlayingRecordingId(null)
      alert('Failed to play audio')
    }
  }



  if (loading) {
    return <LoadingScreen />
  }

  if (error || !event) {
    return (
      <ErrorFallback
        message={error || 'Event not found'}
        onRetry={() => navigate('/')}
        retryLabel="Back to Timeline"
      />
    )
  }

  const isDraft = event.status === 'draft'
  const displayDate = event.time_anchor_date || event.time_anchor

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar
        title=""
        back={{ href: '/' }}
        destructive={{ label: deleting ? 'Deleting...' : 'Delete', onClick: handleDelete, loading: deleting }}
        primary={isDraft ? undefined : { label: exporting ? 'Exporting...' : 'Export', onClick: handleExport, loading: exporting }}
      />

      <div className="max-w-2xl mx-auto p-4">
        {isDraft && (
          <div className="flex items-center gap-2 mb-4">
            <span className="text-base bg-yellow-100 text-yellow-800 px-4 py-2 rounded-full font-medium">
              Draft
            </span>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm p-6 mb-4">
          <div className="flex justify-between items-start mb-4">
            <h1 className="text-2xl font-bold text-gray-900 flex-1">
              {event.title || 'Untitled Memory'}
            </h1>
          </div>

          {displayDate && (
            <p className="text-gray-600 mb-2">{formatDate(displayDate)}</p>
          )}

          {event.place && (
            <p className="text-gray-500 mb-4">{event.place}</p>
          )}

          {event.summary && (
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">{event.summary}</p>
            </div>
          )}

          {isDraft && (
            <div className="space-y-3">
              <button
                type="button"
                onClick={() => navigate(`/interview/${event.id}`)}
                disabled={deleting}
                className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50"
              >
                Continue to Interview
              </button>
              <button
                type="button"
                onClick={handleRecordAgain}
                disabled={deleting}
                className="w-full py-3 bg-gray-200 text-gray-700 rounded-lg font-medium disabled:opacity-50"
              >
                Record Again
              </button>
            </div>
          )}
        </div>

        {event.recordings && event.recordings.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Recordings ({event.recordings.length})
            </h2>
            <div className="space-y-3">
              {event.recordings.map((recording) => (
                <div
                  key={recording.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {recording.recording_type === 'initial_story'
                        ? 'Initial Story'
                        : 'Follow-up Answer'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatDate(recording.created_at)}
                      {recording.duration_seconds &&
                        ` · ${formatDuration(recording.duration_seconds)}`}
                    </p>
                    {recording.transcript && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {recording.transcript}
                      </p>
                    )}
                  </div>
                  {recording.audio_url && (
                    <button
                      type="button"
                      onClick={() => playAudio(recording)}
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        playingRecordingId === recording.id
                          ? 'bg-red-600 text-white'
                          : 'bg-blue-600 text-white'
                      }`}
                      aria-label={
                        playingRecordingId === recording.id ? 'Pause' : 'Play recording'
                      }
                    >
                      {playingRecordingId === recording.id ? (
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      )}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <ConfirmDialog
          open={showDeleteDialog}
          onClose={() => setShowDeleteDialog(false)}
          onConfirm={handleConfirmDelete}
          title="Delete Memory"
          message="Are you sure you want to delete this memory? This cannot be undone."
          confirmLabel="Delete"
          cancelLabel="Cancel"
          destructive
          loading={deleting}
        />

        <ConfirmDialog
          open={showRecordAgainDialog}
          onClose={() => setShowRecordAgainDialog(false)}
          onConfirm={handleConfirmRecordAgain}
          title="Record Again"
          message="Are you sure you want to record a new story? This will delete the current draft."
          confirmLabel="Record Again"
          cancelLabel="Cancel"
          destructive
          loading={deleting}
        />
      </div>
    </div>
  )
}
