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

async function fetchApi(url: string, options: RequestInit = {}): Promise<Response> {
  const authHeaders = await getAuthHeader()
  return fetch(url, {
    ...options,
    headers: { ...authHeaders, ...options.headers },
    credentials: 'include',
  })
}

export interface CreateEventInput {
  title: string
  time_anchor?: string
  time_anchor_date?: string
  place?: string
}

export interface EventData {
  id: string
  user_id: string
  title: string | null
  time_anchor: string | null
  time_anchor_date: string | null
  place: string | null
  status: string
  summary: string | null
  created_at: string
  updated_at: string
  recordings?: AudioRecording[]
}

export interface AudioRecording {
  id: string
  event_id: string
  sequence_order: number
  audio_url: string | null
  transcript: string | null
  recording_type: string
  duration_seconds: number | null
  created_at: string
  detail?: string
}

export async function createEvent(data: CreateEventInput): Promise<EventData> {
  const response = await fetchApi('/api/events/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error('Failed to create event')
  }
  return response.json()
}

export async function getEvent(eventId: string): Promise<EventData> {
  const response = await fetchApi(`/api/events/${eventId}/`)
  if (!response.ok) {
    throw new Error('Failed to fetch event')
  }
  return response.json()
}

export async function updateEvent(eventId: string, data: Partial<EventData>): Promise<EventData> {
  const response = await fetchApi(`/api/events/${eventId}/`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error('Failed to update event')
  }
  return response.json()
}

export async function streamAudio(eventId: string, recordingId: string): Promise<Blob> {
  const authHeaders = await getAuthHeader()
  const response = await fetch(`/api/events/${eventId}/recordings/${recordingId}/audio`, {
    method: 'GET',
    headers: authHeaders,
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to load audio')
  }
  return response.blob()
}

export async function uploadAudio(audioBlob: Blob, eventId: string): Promise<{ audio_url: string }> {
  const authHeaders = await getAuthHeader()
  const formData = new FormData()
  formData.append('file', audioBlob, 'recording.webm')
  formData.append('event_id', eventId)

  const response = await fetch('/api/audio/upload', {
    method: 'POST',
    headers: authHeaders,
    body: formData,
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to upload audio')
  }
  return response.json()
}

export async function listEvents(): Promise<EventData[]> {
  const response = await fetchApi('/api/events/')
  if (!response.ok) {
    throw new Error('Failed to list events')
  }
  return response.json()
}

export async function deleteEvent(eventId: string): Promise<void> {
  const response = await fetchApi(`/api/events/${eventId}/`, { method: 'DELETE' })
  if (!response.ok) {
    throw new Error('Failed to delete event')
  }
}

export async function addRecording(
  eventId: string,
  audioBlob: Blob,
  recordingType: string = 'initial_story',
  durationSeconds?: number
): Promise<AudioRecording> {
  const authHeaders = await getAuthHeader()
  const formData = new FormData()
  formData.append('file', audioBlob, 'recording.webm')
  formData.append('recording_type', recordingType)
  if (durationSeconds !== undefined) {
    formData.append('duration_seconds', String(durationSeconds))
  }

  const response = await fetch(`/api/events/${eventId}/recordings/`, {
    method: 'POST',
    headers: authHeaders,
    body: formData,
    credentials: 'include',
  })

  const result = await response.json()
  if (!response.ok) {
    const error = new Error(result.detail || 'Failed to add recording')
    ;(error as any).audioUrl = result.audio_url
    ;(error as any).recordingId = result.id
    throw error
  }
  return result
}

export async function retryTranscribe(recordingId: string): Promise<AudioRecording> {
  const response = await fetchApi(`/api/events/recordings/${recordingId}/transcribe/`, {
    method: 'POST',
  })
  if (!response.ok) {
    const result = await response.json()
    throw new Error(result.detail || 'Failed to retry transcription')
  }
  return response.json()
}

export interface CompletedEvent {
  id: string
  title: string
  summary: string
  status: string
}

export async function completeEvent(eventId: string): Promise<CompletedEvent> {
  const response = await fetchApi(`/api/events/${eventId}/complete/`, {
    method: 'POST',
  })
  if (!response.ok) {
    const result = await response.json()
    throw new Error(result.detail || 'Failed to complete event')
  }
  return response.json()
}