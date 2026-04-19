import { supabase } from '../lib/supabase'

async function getAuthHeader(): Promise<HeadersInit> {
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token
  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export async function fetchApi(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const headers = await getAuthHeader()
  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  })
  return response
}

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

export async function analyzeEvent(eventId: string): Promise<TranscriptAnalysis> {
  const response = await fetchApi(`/api/events/${eventId}/analyze`, {
    method: 'POST',
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to analyze event')
  }
  return response.json()
}

export async function generateFollowUp(eventId: string): Promise<FollowUpQuestion> {
  const response = await fetchApi(`/api/events/${eventId}/follow-up`, {
    method: 'POST',
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to generate follow-up')
  }
  return response.json()
}

export async function skipFollowUp(eventId: string, questionId: string): Promise<void> {
  const response = await fetchApi(
    `/api/events/${eventId}/follow-up/${questionId}/skip`,
    { method: 'POST' }
  )
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to skip question')
  }
}

export async function getEventWithQuestions(eventId: string): Promise<EventWithQuestions> {
  const response = await fetchApi(`/api/events/${eventId}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch event')
  }
  return response.json()
}

export async function listEvents(): Promise<EventWithQuestions[]> {
  const response = await fetchApi('/api/events')
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to list events')
  }
  return response.json()
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
    const error = await response.json()
    throw new Error(error.detail || 'Failed to generate TTS')
  }

  const audioBlob = await response.blob()
  const audioUrl = URL.createObjectURL(audioBlob)
  return { audio_url: audioUrl }
}