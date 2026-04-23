import { fetchApi, fetchJson } from './api'

export interface FollowUpQuestion {
  id: string
  event_id: string
  question_text: string
  question_type?: string
  context?: string
  target_area?: string
  was_answered: boolean
  audio_url?: string | null
  sequence_order: number
  created_at: string
}

export interface EventWithQuestions {
  id: string
  title: string | null
  time_anchor: string | null
  time_anchor_date: string | null
  place: string | null
  status: string
  summary: string | null
  created_at: string
  follow_up_questions: FollowUpQuestion[]
}

export interface TranscriptAnalysis {
  extracted_time: string | null
  extracted_place: string | null
  people: string[]
  key_events: string[]
  themes: string[]
  summary: string
}

export async function analyzeEvent(eventId: string, transcript: string): Promise<TranscriptAnalysis> {
  return fetchJson<TranscriptAnalysis>(`/api/events/${eventId}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript }),
  })
}

export async function generateFollowUp(
  eventId: string,
  transcript: string,
  existingQuestions: string[] = []
): Promise<FollowUpQuestion> {
  return fetchJson<FollowUpQuestion>(`/api/events/${eventId}/follow-up`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript, existing_questions: existingQuestions }),
  })
}

export async function createQuestion(
  eventId: string,
  question: {
    question_text: string
    question_type?: string
    context?: string
    target_area?: string
  }
): Promise<FollowUpQuestion> {
  return fetchJson<FollowUpQuestion>(`/api/events/${eventId}/questions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(question),
  })
}

export async function skipFollowUp(eventId: string, questionId: string): Promise<{ status: string; question_id: string }> {
  return fetchJson<{ status: string; question_id: string }>(
    `/api/events/${eventId}/follow-up/${questionId}/skip`,
    { method: 'POST' }
  )
}

export async function getEventWithQuestions(eventId: string): Promise<EventWithQuestions> {
  return fetchJson<EventWithQuestions>(`/api/events/${eventId}`)
}

export async function generateTTS(
  text: string,
  voice: string = 'nova',
  model: string = 'gpt-4o-mini-tts'
): Promise<{ audio_url: string }> {
  const response = await fetchApi('/api/tts/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice, model }),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Failed to generate TTS')
  }

  const audioBlob = await response.blob()
  const audioUrl = URL.createObjectURL(audioBlob)
  return { audio_url: audioUrl }
}
