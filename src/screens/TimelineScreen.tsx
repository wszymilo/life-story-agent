import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { supabase } from '../lib/supabase'
import { Timeline } from '../components/Timeline'
import { EventCard } from '../components/EventCard'
import { TopBar } from '../components/TopBar'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { LoadingScreen } from '../components/LoadingScreen'
import { ErrorFallback } from '../components/ErrorFallback'
import { listEvents, getEvent, createEvent, updateEvent, generateMetaStory, EventData } from '../services/events'
import { storeEvaluationScores } from '../services/evaluation'
import { useAuth } from '../context/AuthContext'
import { updatePreferredLanguage } from '../services/user'
import { LANGUAGE_OPTIONS } from '../services/constants'
import { useEventSelection } from '../hooks/useEventSelection'
import { useEncryption } from '../hooks/useEncryption'
import { encrypt, decrypt } from '../lib/crypto'
import { extractErrorMessage } from '../lib/errors'

export function TimelineScreen() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { profile, refreshProfile } = useAuth()
  const { key, isReady } = useEncryption()
  const [events, setEvents] = useState<EventData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [generating, setGenerating] = useState(false)
  const [changingLanguage, setChangingLanguage] = useState(false)
  const [showLogoutDialog, setShowLogoutDialog] = useState(false)
  const [logoutLoading, setLogoutLoading] = useState(false)
  const {
    multiSelectMode,
    selectedIds,
    toggleSelection,
    clearSelection,
    enterSelectionMode,
  } = useEventSelection()

  const handleLanguageChange = async (lang: string) => {
    if (changingLanguage || !profile) return
    setChangingLanguage(true)
    try {
      await updatePreferredLanguage(lang)
      await i18n.changeLanguage(lang)
      await refreshProfile()
    } catch (err) {
      setError(extractErrorMessage(err, t('timeline.languageError')))
    } finally {
      setChangingLanguage(false)
    }
  }

  const handleLogout = () => {
    setShowLogoutDialog(true)
  }

  const handleConfirmLogout = async () => {
    setLogoutLoading(true)
    await supabase.auth.signOut()
    navigate('/login')
  }

  const handleEventClick = (event: EventData) => {
    if (multiSelectMode) return
    navigate(`/event/${event.id}`)
  }

  const handleSelectToggle = (eventId: string) => {
    toggleSelection(eventId)
  }

  const handleCombineStories = async () => {
    if (selectedIds.size < 2 || generating || !key) return

    setGenerating(true)
    try {
      // 1. Fetch and decrypt selected events
      const eventIds = Array.from(selectedIds)
      const eventsData = await Promise.all(
        eventIds.map(async (id) => {
          const event = await getEvent(id)
          const decryptedTitle = event.title ? await decrypt(event.title, key) : null
          const decryptedSummary = event.summary ? await decrypt(event.summary, key) : null
          const decryptedTranscripts = await Promise.all(
            (event.recordings || [])
              .filter((r): r is typeof r & { transcript: string } => !!r.transcript)
              .map(async (r) => (r.transcript ? await decrypt(r.transcript, key) : ''))
          )
          return {
            title: decryptedTitle || 'Untitled Memory',
            summary: decryptedSummary || '',
            date: event.time_anchor_date || event.time_anchor || event.created_at?.slice(0, 10) || '',
            transcripts: decryptedTranscripts,
          }
        })
      )

      // 2. Generate meta-story with decrypted sources
      const { title, summary, _eval_scores } = await generateMetaStory(eventsData)

      // 3. Encrypt result
      const encryptedTitle = await encrypt(title, key)
      const encryptedSummary = await encrypt(summary, key)

      // 4. Create event with encrypted data
      const today = new Date().toISOString().split('T')[0]
      const newEvent = await createEvent({
        title: encryptedTitle,
        time_anchor_date: today,
      })

      // 5. Store encrypted summary and source_event_ids
      await updateEvent(newEvent.id, {
        summary: encryptedSummary,
        status: 'complete',
        source_event_ids: eventIds,
      })

      // 6. Store pre-computed evaluation scores (fire-and-forget)
      if (_eval_scores) {
        storeEvaluationScores(newEvent.id, 'meta_story', _eval_scores).catch(() => {
          // Silently ignore evaluation store errors
        })
      }

      // 7. Navigate to new event
      clearSelection()
      navigate(`/event/${newEvent.id}`)
    } catch (err) {
      alert(extractErrorMessage(err, t('timeline.combineError') || 'Failed to generate meta-story'))
    } finally {
      setGenerating(false)
    }
  }

  const handleRetry = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await listEvents()
      setEvents(data)
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load events'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!isReady) return

    const loadEvents = async () => {
      try {
        setLoading(true)
        setError('')
        const data = await listEvents()

        // Decrypt titles and summaries if encryption key is available
        if (key) {
          const decryptedEvents = await Promise.all(
            data.map(async (event) => ({
              ...event,
              title: event.title ? await decrypt(event.title, key) : null,
              summary: event.summary ? await decrypt(event.summary, key) : null,
            }))
          )
          setEvents(decryptedEvents)
        } else {
          setEvents(data)
        }
      } catch (err) {
      setError(extractErrorMessage(err, t('timeline.loadError')))
      } finally {
        setLoading(false)
      }
    }
    loadEvents()
  }, [key, isReady, t])

  if (!isReady || loading) {
    return <LoadingScreen message={t('timeline.loadingMemories')} />
  }

  if (error) {
    return <ErrorFallback message={error} onRetry={handleRetry} />
  }

  const completedCount = events.filter(e => e.status === 'complete').length

  const currentLanguage = profile?.preferred_language || 'pl'

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar
        title=""
        secondary={
          multiSelectMode
            ? { label: t('common.done'), onClick: clearSelection }
            : { label: t('common.logout'), onClick: handleLogout }
        }
        primary={
          completedCount >= 2 && !multiSelectMode
            ? { label: t('common.select'), onClick: enterSelectionMode }
            : undefined
        }
        tertiaryLeft={
          !multiSelectMode && (
            <div className="flex items-center gap-2">
              <select
                value={currentLanguage}
                onChange={(e) => handleLanguageChange(e.target.value)}
                disabled={changingLanguage || !profile}
                className="px-3 py-2 text-base min-h-10 border border-gray-300 rounded-lg bg-white text-gray-700 disabled:opacity-50"
              >
                {LANGUAGE_OPTIONS.map((opt) => (
                  <option key={opt.code} value={opt.code}>
                    {opt.label}
                  </option>
                ))}
              </select>
              {profile?.is_admin && (
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-3 py-2 text-base min-h-10 text-gray-600 hover:text-gray-800"
                  title={t('timeline.adminDashboard')}
                  aria-label={t('timeline.adminDashboard')}
                >
                  📊
                </button>
              )}
            </div>
          )
        }
      />

      <div className="max-w-2xl mx-auto p-4">
        {multiSelectMode && selectedIds.size >= 2 && (
          <button
            onClick={handleCombineStories}
            disabled={generating}
            className="w-full mb-4 py-4 min-h-14 bg-blue-600 hover:bg-blue-700 text-white text-lg rounded-lg font-medium disabled:opacity-50"
          >
            {generating ? t('timeline.combining') : t('timeline.combineButton', { count: selectedIds.size })}
          </button>
        )}

        {events.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">
              {t('timeline.emptyTitle')}
            </p>
            <button
              type="button"
              onClick={() => navigate('/record')}
              disabled={loading || generating}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50"
            >
              {t('timeline.recordFirst')}
            </button>
          </div>
        ) : (
          <Timeline>
            {events.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                onClick={handleEventClick}
                multiSelectMode={multiSelectMode}
                selected={selectedIds.has(event.id)}
                onSelect={handleSelectToggle}
                language={currentLanguage}
              />
            ))}
          </Timeline>
        )}

        {events.length > 0 && (
          <>
            <button
              type="button"
              onClick={() => navigate('/record')}
              className="fixed bottom-6 right-6 w-16 h-16 bg-blue-600 rounded-full shadow-lg flex items-center justify-center hover:bg-blue-700 transition-colors"
              aria-label={t('timeline.addMemory')}
            >
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </button>

            <ConfirmDialog
              open={showLogoutDialog}
              onClose={() => setShowLogoutDialog(false)}
              onConfirm={handleConfirmLogout}
          title={t('timeline.logoutConfirmTitle')}
          message={t('timeline.logoutConfirmMessage')}
          confirmLabel={t('common.signOut')}
          cancelLabel={t('common.cancel')}
              destructive
              loading={logoutLoading}
            />
          </>
        )}
      </div>
    </div>
  )
}
