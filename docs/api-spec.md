# API Specification: Life Story Preservation Agent

## Base URL

| Environment | URL |
|-------------|-----|
| Local Dev | `http://localhost:8000` |
| Production | `https://life-story-agent-production.up.railway.app` |

All API routes (except `/health`, `/health/ready`, `/auth/me`) are prefixed with `/api`.

---

## Authentication

All protected endpoints require a Supabase JWT token in the `Authorization` header.

```http
Authorization: Bearer <supabase_jwt_token>
```

The token is obtained via Supabase Auth magic link flow. The backend validates the token on every request using Supabase JWKS with 1-hour TTL caching.

### Auth Errors

| Status | Body | When |
|--------|------|------|
| `401` | `{"detail": "Not authenticated"}` | Missing or invalid token |
| `403` | `{"detail": "Admin access only"}` | Non-admin accessing admin endpoint |

---

## Rate Limiting

Rate limiting is applied via `slowapi` to the following endpoints:

| Endpoint | Limit |
|----------|-------|
| `POST /api/events/{id}/analyze` | 5/minute |
| `POST /api/events/{id}/follow-up` | 5/minute |
| `POST /api/tts/generate` | 20/minute |

When exceeded, the API returns:

```http
429 Too Many Requests
```

---

## Health & Status

### `GET /health`

Deployment health check.

**Auth:** None

**Response:**
```json
{
  "status": "ok"
}
```

---

### `GET /health/ready`

Readiness check including database connectivity.

**Auth:** None

**Response (healthy):**
```json
{
  "status": "ready",
  "database": "connected",
  "user_count": 42
}
```

**Response (unhealthy):**
```json
{
  "status": "not_ready",
  "database": "error",
  "error": "connection timeout"
}
```

---

### `GET /auth/me`

Get current authenticated user ID and email.

**Auth:** Required (Bearer JWT)

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

---

## Users

### `GET /api/users/me`

Get current user profile with relatives.

**Auth:** Required

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | User ID |
| `email` | string | User email |
| `name` | string \| null | Display name |
| `birth_date` | date \| null | Birth date (YYYY-MM-DD) |
| `country_of_origin` | string \| null | Country of origin |
| `preferred_language` | string | Language code (default: "pl") |
| `created_at` | datetime | Account creation timestamp |
| `relatives` | RelativeResponse[] | List of relatives |
| `is_admin` | boolean | True if user email matches ADMIN_EMAIL |

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "Maria",
  "birth_date": "1945-03-15",
  "country_of_origin": "Poland",
  "preferred_language": "pl",
  "created_at": "2026-04-20T10:00:00Z",
  "relatives": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Jan Kowalski",
      "relationship": "brother",
      "created_at": "2026-04-20T10:05:00Z"
    }
  ],
  "is_admin": false
}
```

---

### `PUT /api/users/me`

Update current user profile.

**Auth:** Required

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | No | min_length=1 |
| `birth_date` | date | No | YYYY-MM-DD format |
| `country_of_origin` | string | No | min_length=1 |
| `preferred_language` | string | No | ISO 639-1, 2 chars |

```json
{
  "name": "Maria",
  "birth_date": "1945-03-15",
  "country_of_origin": "Poland",
  "preferred_language": "pl"
}
```

**Response:** Same as `GET /api/users/me` with updated fields.

---

### `PUT /api/users/me/language`

Update preferred language for AI-generated content.

**Auth:** Required

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `preferred_language` | string | Yes | ISO 639-1, 2 chars |

```json
{
  "preferred_language": "en"
}
```

**Response:** Same as `GET /api/users/me`.

---

### `POST /api/users/me/relatives`

Add a relative to current user's profile.

**Auth:** Required

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | min_length=1, max_length=255 |
| `relationship` | string | Yes | min_length=1, max_length=100 |

```json
{
  "name": "Jan Kowalski",
  "relationship": "brother"
}
```

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Relative ID |
| `name` | string | Relative name |
| `relationship` | string | Relationship type |
| `created_at` | datetime | Creation timestamp |

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Jan Kowalski",
  "relationship": "brother",
  "created_at": "2026-04-20T10:05:00Z"
}
```

---

### `DELETE /api/users/me/relatives/{relative_id}`

Delete a relative from current user's profile.

**Auth:** Required

**Response:**
```json
{
  "success": true
}
```

**Errors:**
- `404` — Relative not found or not owned by user

---

## Events

### `GET /api/events`

List all events for the authenticated user, sorted by `time_anchor_date` ascending.

**Auth:** Required

**Response:** Array of EventResponse objects

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Event ID |
| `user_id` | UUID | Owner user ID |
| `title` | string \| null | Encrypted title (ciphertext) |
| `time_anchor` | string \| null | Human-readable time reference |
| `time_anchor_date` | date \| null | Parsed date for sorting |
| `place` | string \| null | Location of event |
| `status` | string | "draft" or "complete" |
| `summary` | string \| null | Encrypted summary (ciphertext) |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "encrypted_base64_ciphertext...",
    "time_anchor": "Spring 1956",
    "time_anchor_date": "1956-03-01",
    "place": "Warsaw",
    "status": "complete",
    "summary": "encrypted_base64_ciphertext...",
    "created_at": "2026-04-21T14:00:00Z",
    "updated_at": "2026-04-21T14:30:00Z"
  }
]
```

---

### `POST /api/events`

Create a new event (draft). Also creates a LangFuse trace for session observability.

**Auth:** Required

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `title` | string | Yes | min_length=1, max_length=255 |
| `time_anchor` | string | No | Human-readable time reference |
| `time_anchor_date` | date | No | YYYY-MM-DD |
| `place` | string | No | Location |

```json
{
  "title": "encrypted_ciphertext...",
  "time_anchor": "Spring 1956",
  "time_anchor_date": "1956-03-01",
  "place": "Warsaw"
}
```

**Response:** EventResponse (same schema as `GET /api/events` item)

**Status:** `201 Created`

---

### `GET /api/events/{event_id}`

Get an event by ID with its recordings.

**Auth:** Required

**Response:** EventWithRecordingsResponse

Extends EventResponse with:

| Field | Type | Description |
|-------|------|-------------|
| `recordings` | AudioRecordingResponse[] | List of audio recordings |

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "encrypted_ciphertext...",
  "time_anchor": "Spring 1956",
  "time_anchor_date": "1956-03-01",
  "place": "Warsaw",
  "status": "complete",
  "summary": "encrypted_ciphertext...",
  "created_at": "2026-04-21T14:00:00Z",
  "updated_at": "2026-04-21T14:30:00Z",
  "recordings": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "event_id": "770e8400-e29b-41d4-a716-446655440002",
      "sequence_order": 1,
      "audio_url": "https://storage.supabase.co/...",
      "transcript": "encrypted_ciphertext...",
      "recording_type": "initial_story",
      "duration_seconds": 120.5,
      "created_at": "2026-04-21T14:01:00Z"
    }
  ]
}
```

**Errors:**
- `404` — Event not found or not owned by user

---

### `PUT /api/events/{event_id}`

Update an event.

**Auth:** Required

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `title` | string | No | |
| `time_anchor` | string | No | |
| `time_anchor_date` | date | No | YYYY-MM-DD |
| `place` | string | No | |
| `status` | string | No | "draft" or "complete" |
| `summary` | string | No | |

```json
{
  "title": "new_encrypted_ciphertext...",
  "status": "complete"
}
```

**Response:** EventResponse

**Errors:**
- `404` — Event not found

---

### `DELETE /api/events/{event_id}`

Delete event and cascade delete recordings, questions, evaluation results, and audio files from storage.

**Auth:** Required

**Response:**

```json
{
  "status": "deleted",
  "event_id": "770e8400-e29b-41d4-a716-446655440002"
}
```

**Status:** `204 No Content` (body included for clarity)

---

### `POST /api/events/{event_id}/complete`

Complete an event session: generate summary from client-provided plaintext transcripts and Q&A.

**Auth:** Required

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcripts` | string[] | Yes | Decrypted transcript strings |
| `questions_and_answers` | object[] | No | Array of `{question, answer}` objects |

```json
{
  "transcripts": [
    "I was born in Warsaw in 1945...",
    "My childhood was during the communist era..."
  ],
  "questions_and_answers": [
    {
      "question": "What did your mother look like?",
      "answer": "She had dark hair and always wore an apron..."
    }
  ]
}
```

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Event ID |
| `title` | string | Generated title (plaintext) |
| `summary` | string | Generated summary (plaintext) |
| `status` | string | "complete" |
| `time_anchor_date` | string \| null | Extracted date (YYYY-MM-DD) |
| `_eval_scores` | object \| null | Evaluation scores (if sampled) |

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "title": "Childhood in Communist Poland",
  "summary": "Maria was born in Warsaw in 1945...",
  "status": "complete",
  "time_anchor_date": "1945-01-01",
  "_eval_scores": {
    "factual_accuracy": 5,
    "coherence": 4,
    "completeness": 5,
    "overall_score": 5
  }
}
```

**Background:** If `EVAL_ENABLED=true` and sampled, evaluation runs asynchronously and stores scores in `evaluation_results` table + LangFuse trace.

**Errors:**
- `400` — Event already completed
- `500` — Summary generation failed

---

### `POST /api/events/meta-generate`

Generate a meta-story from multiple decrypted event sources.

**Auth:** Required

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `sources` | object[] | Yes | min=2, max=10 (configurable) |

Each source object:

| Field | Type | Required |
|-------|------|----------|
| `title` | string | No |
| `summary` | string | No |
| `date` | string | No |
| `transcripts` | string[] | No |

```json
{
  "sources": [
    {
      "title": "Childhood in Warsaw",
      "summary": "I grew up in Warsaw during the 1950s...",
      "date": "1950-01-01",
      "transcripts": ["I remember the cold winters..."]
    },
    {
      "title": "My Wedding Day",
      "summary": "I married in 1972...",
      "date": "1972-06-15",
      "transcripts": ["The church was beautiful..."]
    }
  ]
}
```

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Generated combined title |
| `summary` | string | Generated narrative with sources section |
| `_eval_scores` | object \| null | Evaluation scores (if sampled) |

```json
{
  "title": "A Life in Poland: From Childhood to Marriage",
  "summary": "Maria's life began in Warsaw in 1945...\n\n---\n\n## Sources\n1. Childhood in Warsaw (1950-01-01)\n2. My Wedding Day (1972-06-15)\n",
  "_eval_scores": {
    "factual_accuracy": 5,
    "coherence": 5,
    "completeness": 4,
    "overall_score": 5
  }
}
```

**Errors:**
- `400` — Less than 2 sources or more than max allowed
- `500` — Generation failed

---

## Recordings

### `POST /api/events/{event_id}/recordings`

Upload an audio recording to an event. Validates audio type, uploads to Supabase Storage, transcribes via Whisper, and persists the recording.

**Auth:** Required

**Content-Type:** `multipart/form-data`

**Form Fields:**

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `file` | File | Yes | — | audio/*, max 25MB |
| `recording_type` | string | No | "initial_story" | "initial_story" or "follow_up_response" |
| `duration_seconds` | float | No | null | Recording duration in seconds |

**Response:** AudioRecordingResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Recording ID |
| `event_id` | UUID | Parent event ID |
| `sequence_order` | int | Order in session |
| `audio_url` | string | Supabase Storage URL |
| `transcript` | string \| null | Transcript (plaintext on success, null on failure) |
| `recording_type` | string | "initial_story" or "follow_up_response" |
| `duration_seconds` | float \| null | Duration |
| `created_at` | datetime | Creation timestamp |
| `detail` | string \| null | Error message if transcription failed |

**Success (transcription OK):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "event_id": "770e8400-e29b-41d4-a716-446655440002",
  "sequence_order": 1,
  "audio_url": "https://storage.supabase.co/.../recording.webm",
  "transcript": "I was born in Warsaw...",
  "recording_type": "initial_story",
  "duration_seconds": 120.5,
  "created_at": "2026-04-21T14:01:00Z",
  "detail": null
}
```

**Partial success (transcription failed, audio saved):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "event_id": "770e8400-e29b-41d4-a716-446655440002",
  "sequence_order": 1,
  "audio_url": "https://storage.supabase.co/.../recording.webm",
  "transcript": null,
  "recording_type": "initial_story",
  "duration_seconds": 120.5,
  "created_at": "2026-04-21T14:01:00Z",
  "detail": "Transcription failed. Your recording is saved."
}
```

**Status:** `201 Created`

**Errors:**
- `400` — Invalid audio file type or file too large (>25MB)
- `500` — Upload or storage failure

---

### `GET /api/events/{event_id}/recordings`

Get all recordings for an event.

**Auth:** Required

**Response:** Array of AudioRecordingResponse

---

### `GET /api/events/{event_id}/recordings/{recording_id}/audio`

Stream audio file for a recording. Downloads from private Supabase Storage bucket and returns raw audio bytes.

**Auth:** Required

**Response:** Raw audio bytes (`audio/webm`)

**Headers:**
```http
Content-Disposition: inline; filename="recording_{recording_id}.webm"
```

**Errors:**
- `404` — Recording or audio file not found
- `500` — Failed to load audio from storage

---

### `POST /api/recordings/{recording_id}/transcribe`

Retry transcription for an existing recording.

**Auth:** Required

**Response:** AudioRecordingResponse (same as upload response)

**Errors:**
- `404` — Recording not found
- `400` — Recording has no audio file
- `500` — Transcription failed

---

### `PUT /api/recordings/{recording_id}/transcript`

Update the encrypted transcript for a recording. Used by the frontend after encrypting the plaintext transcript returned by the backend.

**Auth:** Required

**Request Body:**

| Field | Type | Required |
|-------|------|----------|
| `transcript` | string | Yes |

```json
{
  "transcript": "encrypted_base64_ciphertext..."
}
```

**Response:** AudioRecordingResponse

**Errors:**
- `404` — Recording not found

---

## Interview (Analysis & Questions)

### `POST /api/events/{event_id}/analyze`

Analyze a plaintext transcript to extract time, place, people, themes, and key events.

**Auth:** Required
**Rate Limit:** 5/minute

**Request Body:**

| Field | Type | Required |
|-------|------|----------|
| `transcript` | string | Yes |

```json
{
  "transcript": "I was born in Warsaw in 1945. My mother was a teacher..."
}
```

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `extracted_time` | string \| null | Time reference (e.g., "1945", "Spring 1956") |
| `extracted_place` | string \| null | Location mentioned |
| `people` | string[] | People mentioned |
| `key_events` | string[] | Key events/stories |
| `themes` | string[] | Main themes |
| `summary` | string | Brief summary |

```json
{
  "extracted_time": "1945",
  "extracted_place": "Warsaw",
  "people": ["mother", "father"],
  "key_events": ["birth", "childhood"],
  "themes": ["family", "war aftermath"],
  "summary": "The speaker describes being born in Warsaw in 1945..."
}
```

**Side Effects:** If `extracted_time` is parseable, updates `events.time_anchor_date` and `events.time_anchor`. If `extracted_place` is present, updates `events.place`.

**Errors:**
- `400` — Transcript is empty
- `500` — Analysis failed

---

### `POST /api/events/{event_id}/follow-up`

Generate a contextual follow-up question based on the transcript.

**Auth:** Required
**Rate Limit:** 5/minute

**Request Body:**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `transcript` | string | Yes | — |
| `existing_questions` | string[] | No | [] |

```json
{
  "transcript": "I was born in Warsaw in 1945...",
  "existing_questions": ["What did your mother look like?"]
}
```

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `question_text` | string | The generated question |
| `question_type` | string | Type: sensory, emotional, people, places, context, detail |

```json
{
  "question_text": "What do you remember about the street where you lived?",
  "question_type": "places"
}
```

**Background:** If `EVAL_ENABLED=true` and sampled, question quality evaluation runs asynchronously.

**Errors:**
- `400` — Transcript is empty
- `500` — Question generation failed

---

### `POST /api/events/{event_id}/questions`

Store an encrypted follow-up question. Deletes any previous unanswered question for the event first.

**Auth:** Required

**Request Body:**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `question_text` | string | Yes | — |
| `question_type` | string | No | null |
| `context` | string | No | null |
| `target_area` | string | No | null |

```json
{
  "question_text": "encrypted_ciphertext...",
  "question_type": "places",
  "context": "encrypted_ciphertext...",
  "target_area": "place"
}
```

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Question ID |
| `question_text` | string | Encrypted question text |
| `sequence_order` | int | Order in session |
| `was_answered` | boolean | Always false on creation |
| `created_at` | datetime | Creation timestamp |

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "question_text": "encrypted_ciphertext...",
  "sequence_order": 1,
  "was_answered": false,
  "created_at": "2026-04-21T14:10:00Z"
}
```

**Status:** `201 Created`

---

## TTS

### `POST /api/tts/generate`

Generate speech from text and return audio as streaming response.

**Auth:** Required
**Rate Limit:** 20/minute

**Request Body:**

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `text` | string | Yes | — | Non-empty |
| `voice` | string | No | "nova" | One of: alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse, marin, cedar |
| `model` | string | No | "gpt-4o-mini-tts" | One of: tts-1, tts-1-hd, gpt-4o-mini-tts |
| `response_format` | string | No | "mp3" | One of: mp3, opus, aac, flac, wav, pcm |

```json
{
  "text": "What do you remember about your childhood home?",
  "voice": "nova",
  "model": "gpt-4o-mini-tts",
  "response_format": "mp3"
}
```

**Response:** Streaming audio bytes (`audio/mpeg`)

**Headers:**
```http
Content-Disposition: inline
```

**Errors:**
- `400` — Invalid voice, model, or format
- `500` — TTS generation failed

---

## Evaluations

### `GET /api/evaluations/dashboard`

Get evaluation dashboard statistics (admin only).

**Auth:** Required (Admin only)

**Query Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `eval_type` | string | No | null (all types) |

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `total_evaluations` | int | Total number of evaluations |
| `avg_factual_accuracy` | float \| null | Average factual accuracy (1-5) |
| `avg_coherence` | float \| null | Average coherence (1-5) |
| `avg_completeness` | float \| null | Average completeness (1-5) |
| `avg_overall_score` | float \| null | Average overall score (1-5) |
| `recent_evaluations` | EvaluationResult[] | Last 10 evaluations |

```json
{
  "total_evaluations": 42,
  "avg_factual_accuracy": 4.5,
  "avg_coherence": 4.2,
  "avg_completeness": 4.7,
  "avg_overall_score": 4.5,
  "recent_evaluations": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "event_id": "770e8400-e29b-41d4-a716-446655440002",
      "eval_type": "summary",
      "factual_accuracy": 5,
      "coherence": 4,
      "completeness": 5,
      "overall_score": 5,
      "evaluator_model": "gpt-4o-mini",
      "created_at": "2026-04-21T15:00:00Z"
    }
  ]
}
```

**Errors:**
- `403` — Admin access only

---

### `POST /api/evaluations/scores`

Store pre-computed evaluation scores.

**Auth:** Required

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `event_id` | string | Yes | |
| `eval_type` | string | Yes | |
| `factual_accuracy` | int | Yes | 1-5 |
| `coherence` | int | Yes | 1-5 |
| `completeness` | int | Yes | 1-5 |
| `overall_score` | int | Yes | 1-5 |

```json
{
  "event_id": "770e8400-e29b-41d4-a716-446655440002",
  "eval_type": "meta_story",
  "factual_accuracy": 5,
  "coherence": 4,
  "completeness": 5,
  "overall_score": 5
}
```

**Response:**
```json
{
  "status": "stored"
}
```

---

## Client-Side Export (Not a Backend Endpoint)

ZIP export is generated entirely in the browser. The frontend:

1. Decrypts event data (title, summary, transcripts)
2. Fetches audio blobs via `GET /api/events/{id}/recordings/{rid}/audio`
3. Generates markdown using `JSZip`
4. Assembles the ZIP with this structure:

```
{safe_title}.zip
├── {safe_title}.md          # Markdown narrative
├── artifacts/
│   ├── {safe_title}.txt     # Initial story transcript
│   └── {safe_title}.webm    # Initial story audio
└── artifacts/additional/
    ├── follow_up_1.txt
    ├── follow_up_1.webm
    └── ...
```

5. Triggers browser download via `URL.createObjectURL()`

**No backend endpoint exists for export.**

---

## Common Error Responses

### Validation Errors (422)

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### Authentication Errors (401)

```json
{
  "detail": "Not authenticated"
}
```

### Not Found (404)

```json
{
  "detail": "Event not found"
}
```

### Server Error (500)

```json
{
  "detail": "Internal server error"
}
```

---

*Document version: 1.0 | Last updated: 2026-04-24*
