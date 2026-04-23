import { fetchApi, fetchJson } from './api'

export interface RecordingError extends Error {
  audioUrl?: string
  recordingId?: string
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
  source_event_ids?: string[] | null
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
  return fetchJson<EventData>('/api/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function getEvent(eventId: string): Promise<EventData> {
  return fetchJson<EventData>(`/api/events/${eventId}`)
}

export async function updateEvent(eventId: string, data: Partial<EventData>): Promise<EventData> {
  return fetchJson<EventData>(`/api/events/${eventId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function streamAudio(eventId: string, recordingId: string): Promise<Blob> {
  const response = await fetchApi(`/api/events/${eventId}/recordings/${recordingId}/audio`)
  if (!response.ok) {
    throw new Error('Failed to load audio')
  }
  return response.blob()
}

export async function listEvents(): Promise<EventData[]> {
  return fetchJson<EventData[]>('/api/events')
}

export async function deleteEvent(eventId: string): Promise<void> {
  const response = await fetchApi(`/api/events/${eventId}`, { method: 'DELETE' })
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
  const formData = new FormData()
  formData.append('file', audioBlob, 'recording.webm')
  formData.append('recording_type', recordingType)
  if (durationSeconds !== undefined) {
    formData.append('duration_seconds', String(durationSeconds))
  }

  const response = await fetchApi(`/api/events/${eventId}/recordings`, {
    method: 'POST',
    body: formData,
  })

  const result = await response.json()
  if (!response.ok) {
    const error = new Error(result.detail || 'Failed to add recording')
    ;(error as RecordingError).audioUrl = result.audio_url
    ;(error as RecordingError).recordingId = result.id
    throw error
  }
  return result
}

export async function updateRecordingTranscript(
  recordingId: string,
  transcript: string
): Promise<AudioRecording> {
  return fetchJson<AudioRecording>(`/api/events/recordings/${recordingId}/transcript`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript }),
  })
}

export async function retryTranscribe(recordingId: string): Promise<AudioRecording> {
  return fetchJson<AudioRecording>(`/api/events/recordings/${recordingId}/transcribe`, {
    method: 'POST',
  })
}

export interface CompletedEvent {
  id: string
  title: string
  summary: string
  status: string
  time_anchor_date: string | null
}

export interface QuestionAnswer {
  question: string
  answer: string
}

export async function completeEvent(
  eventId: string,
  transcripts: string[],
  questionsAndAnswers: QuestionAnswer[]
): Promise<CompletedEvent> {
  return fetchJson<CompletedEvent>(`/api/events/${eventId}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcripts, questions_and_answers: questionsAndAnswers }),
  })
}

export interface MetaStorySource {
  title: string
  summary: string
  date: string
  transcripts: string[]
}

export interface MetaStoryResult {
  title: string
  summary: string
  _eval_payload?: {
    sources: MetaStorySource[]
    summary: string
  }
}

export async function generateMetaStory(sources: MetaStorySource[]): Promise<MetaStoryResult> {
  return fetchJson<MetaStoryResult>('/api/events/meta-generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sources }),
  })
}
