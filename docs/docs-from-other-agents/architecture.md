# Complete Architecture Specification

## 1.1 System Overview

The Life Story Preservation Agent is a mobile-first web application that enables elderly users to record, preserve, and export their life stories through AI-assisted voice interviews.

### High-Level Architecture

text

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER                                        │
│                         (Mobile Browser)                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vercel)                                │
│                         React 18 PWA                                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Login   │ │Onboard  │ │Timeline │ │Record/  │ │Event    │           │
│  │ Screen  │ │ Screen  │ │ Screen  │ │Interview│ │Detail   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Services: API Client | Audio Recorder | Auth | State (TanStack) │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (Railway)                                │
│                         FastAPI + Python 3.12                            │
│                                                                          │
│  ┌──────────────────────── API Routes ─────────────────────────────┐    │
│  │  /auth/*  │  /users/*  │  /events/*  │  /tts  │  /publish      │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌──────────────────────── Services ───────────────────────────────┐    │
│  │                                                                  │    │
│  │  ┌─────────────────┐    ┌─────────────────┐                     │    │
│  │  │  Transcription  │    │   TTS Service   │                     │    │
│  │  │    Service      │    │                 │                     │    │
│  │  │  (Whisper API)  │    │  (OpenAI TTS)   │                     │    │
│  │  └─────────────────┘    └─────────────────┘                     │    │
│  │                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │              Interview Agent (OpenAI Agents SDK)         │    │    │
│  │  │  ┌─────────────────┐  ┌─────────────────────────────┐   │    │    │
│  │  │  │ analyze_        │  │ generate_follow_up_question │   │    │    │
│  │  │  │ transcript      │  │                             │   │    │    │
│  │  │  └─────────────────┘  └─────────────────────────────┘   │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │         Summary Generator (Generator-Reviewer)           │    │    │
│  │  │  ┌──────────────┐    ┌──────────────┐                   │    │    │
│  │  │  │  Generator   │───►│   Reviewer   │──► Final Summary  │    │    │
│  │  │  │   (LLM)      │    │    (LLM)     │                   │    │    │
│  │  │  └──────────────┘    └──────────────┘                   │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  ┌─────────────────┐    ┌─────────────────┐                     │    │
│  │  │ Timeline Service│    │  Export Service │                     │    │
│  │  │                 │    │   (Zip Builder) │                     │    │
│  │  └─────────────────┘    └─────────────────┘                     │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                                  │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │    Supabase     │  │     OpenAI      │  │   Observability │         │
│  │                 │  │                 │  │                 │         │
│  │  • PostgreSQL   │  │  • gpt-4o-mini  │  │  • Sentry       │         │
│  │  • Auth         │  │  • Whisper API  │  │  • LangFuse     │         │
│  │  • Storage      │  │  • TTS API      │  │                 │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1.2 Component Specifications

### 1.2.1 Frontend Components

#### Screens

|Screen|Route|Purpose|Key Components|
| --- | --- | --- | --- |
|**LoginScreen**|/login|User authentication|Email input, magic link button|
|**OnboardingScreen**|/onboarding|First-time user setup|Multi-step form (name, birth date, country, relatives)|
|**TimelineScreen**|/ (home)|Main dashboard|Timeline visualization, event cards, "Add Memory" FAB|
|**RecordingScreen**|/record|Initial story capture|Large record button, live waveform, transcript preview|
|**InterviewScreen**|/interview/:eventId|Follow-up Q&A loop|Question display, TTS playback, record/skip buttons|
|**SummaryScreen**|/summary/:eventId|Review before save|Summary text, TTS playback, confirm button|
|**EventDetailScreen**|/event/:eventId|View saved event|Summary, audio player, transcript, delete button|
|**ExportScreen**|/export|Download content|Event selector, generate button, download link|

#### Shared Components

|Component|Purpose|Props|
| --- | --- | --- |
|AudioRecorder|Capture voice input|onRecordingComplete(blob)|
|AudioPlayer|Play audio files|src: string, autoPlay?: boolean|
|Timeline|Visual timeline display|events: Event[], onEventClick(id)|
|EventCard|Event summary card|event: Event, onClick()|
|LoadingSpinner|Loading state|`size?: 'sm'|
|BigButton|Accessible large button|children, onClick, variant|
|ConfirmDialog|Confirmation modal|title, message, onConfirm, onCancel|

#### State Management

typescript

```
// TanStack Query - Server State
const useEvents = () => useQuery(['events'], fetchEvents);
const useEvent = (id: string) => useQuery(['event', id], () => fetchEvent(id));
const useCreateEvent = () => useMutation(createEvent);
const useCompleteEvent = () => useMutation(completeEvent);
const useDeleteEvent = () => useMutation(deleteEvent);

// React Context - Session State
interface SessionContextType {
  currentEventId: string | null;
  recordings: RecordingData[];
  questions: QuestionData[];
  addRecording: (recording: RecordingData) => void;
  addQuestion: (question: QuestionData) => void;
  clearSession: () => void;
}
```

---

### 1.2.2 Backend Services

#### Transcription Service

|Aspect|Details|
| --- | --- |
|**Purpose**|Convert audio recordings to text|
|**Input**|Audio file (webm/mp3/wav)|
|**Output**|{ transcript: string, duration: float }|
|**External API**|OpenAI Whisper API|
|**Error Handling**|Retry 2x, then return partial/empty with error flag|

python

```
# Interface
class TranscriptionService:
    async def transcribe(self, audio_file: UploadFile) -> TranscriptionResult:
        """
        Transcribe audio file using Whisper API.
        
        Args:
            audio_file: Uploaded audio file
            
        Returns:
            TranscriptionResult with transcript text and duration
        """
        pass
```

#### TTS Service

|Aspect|Details|
| --- | --- |
|**Purpose**|Convert text to speech|
|**Input**|Text string, optional voice setting|
|**Output**|Audio file URL (stored in Supabase)|
|**External API**|OpenAI TTS API|
|**Voice**|alloy (warm, neutral)|

python

```
# Interface
class TTSService:
    async def synthesize(self, text: str, voice: str = "alloy") -> TTSResult:
        """
        Generate speech audio from text.
        
        Args:
            text: Text to convert to speech
            voice: Voice selection (default: alloy)
            
        Returns:
            TTSResult with audio_url
        """
        pass
```

#### Interview Agent

|Aspect|Details|
| --- | --- |
|**Purpose**|Analyze transcripts and generate follow-up questions|
|**Framework**|OpenAI Agents SDK|
|**Model**|gpt-4o-mini|
|**Tools**|analyze_transcript, generate_follow_up_question|

python

```
# Agent Configuration
interview_agent = Agent(
    name="LifeStoryInterviewer",
    model="gpt-4o-mini",
    instructions="""
    You are a warm, patient oral historian helping an elderly person 
    preserve their life stories. You treat every memory as precious 
    and worthy of documentation.
    
    When analyzing transcripts:
    - Identify time references (dates, seasons, ages, life periods)
    - Identify places mentioned
    - Identify people mentioned (especially family members)
    - Identify sub-events or details worth exploring
    
    When generating follow-up questions:
    - Be gentle and curious, never interrogating
    - Ask open-ended questions that invite storytelling
    - Focus on sensory details, emotions, and connections
    - Respect if topics seem sensitive
    - One question at a time
    """,
    tools=[analyze_transcript, generate_follow_up_question]
)

# Tool: analyze_transcript
@tool
def analyze_transcript(transcript: str) -> AnalysisResult:
    """
    Analyze a story transcript to extract structured information.
    
    Returns:
        AnalysisResult:
            - has_time: bool
            - time_anchor: str | None
            - has_place: bool
            - place: str | None
            - people_mentioned: list[str]
            - subjects_to_explore: list[str]
    """
    pass

# Tool: generate_follow_up_question
@tool
def generate_follow_up_question(
    transcript: str,
    previous_questions: list[str],
    subjects_to_explore: list[str]
) -> FollowUpQuestion:
    """
    Generate a thoughtful follow-up question to deepen the story.
    
    Returns:
        FollowUpQuestion:
            - question_text: str
            - target_subject: str (what this question explores)
    """
    pass
```

#### Summary Generator (Generator-Reviewer Pattern)

|Aspect|Details|
| --- | --- |
|**Purpose**|Create grounded summaries from session artifacts|
|**Pattern**|Generator-Reviewer with retry|
|**Model**|gpt-4o-mini|
|**Max Retries**|2|

python

```
# Generator-Reviewer Flow
class SummaryGenerator:
    async def generate_summary(self, event_id: str) -> SummaryResult:
        """
        Generate a grounded summary using Generator-Reviewer pattern.
        
        Flow:
        1. Gather all artifacts (transcripts, Q&A)
        2. Generator creates initial summary
        3. Reviewer validates grounding
        4. If rejected, regenerate with feedback (max 2 retries)
        5. Return final summary with grounding score
        """
        pass

# Generator Prompt
GENERATOR_PROMPT = """
Create a warm, narrative summary of this life story based on the following 
transcripts and Q&A exchanges. 

Rules:
- Include ONLY information present in the source material
- Do not invent or embellish any details
- Preserve the person's voice and perspective
- Organize chronologically if possible
- Be respectful and dignified in tone

Source Material:
{transcripts}

Q&A Exchanges:
{qa_exchanges}
"""

# Reviewer Prompt
REVIEWER_PROMPT = """
Review this summary for factual grounding. Check that every claim 
in the summary can be traced to the source transcripts.

Summary to review:
{summary}

Source Material:
{transcripts}

For each claim in the summary:
1. Verify it exists in source material
2. Flag any fabricated or embellished details

Return:
- is_grounded: bool (true if all claims are supported)
- issues: list[str] (specific problems found)
- suggestions: str (how to fix if not grounded)
"""
```

#### Timeline Service

|Aspect|Details|
| --- | --- |
|**Purpose**|Manage and query events on user's timeline|
|**Operations**|List events, sort by date, filter by status|

python

```
class TimelineService:
    async def get_user_events(
        self, 
        user_id: str, 
        status: EventStatus | None = None
    ) -> list[Event]:
        """Get all events for user, sorted by time_anchor_date."""
        pass
    
    async def get_event_with_details(self, event_id: str) -> EventWithDetails:
        """Get event with all recordings and questions."""
        pass
```

#### Export Service

|Aspect|Details|
| --- | --- |
|**Purpose**|Generate downloadable zip files|
|**Contents**|Markdown summary + audio files organized by event|

python

```
class ExportService:
    async def export_event(self, event_id: str) -> bytes:
        """
        Export single event as zip file.
        
        Structure:
        event_{id}/
        ├── summary.md
        ├── recordings/
        │   ├── 01_initial_story.webm
        │   ├── 02_followup_1.webm
        │   └── ...
        └── transcripts/
            ├── 01_initial_story.txt
            ├── 02_followup_1.txt
            └── ...
        """
        pass
    
    async def export_multiple_events(self, event_ids: list[str]) -> bytes:
        """Export multiple events (stretch goal)."""
        pass
```

---

## 1.3 Data Models (SQLAlchemy)

python

```
# models/user.py
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    birth_date: Mapped[date] = mapped_column(Date)
    country_of_origin: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    
    # Relationships
    relatives: Mapped[list["Relative"]] = relationship(back_populates="user")
    events: Mapped[list["Event"]] = relationship(back_populates="user")


# models/relative.py
class Relative(Base):
    __tablename__ = "relatives"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    relationship: Mapped[str] = mapped_column(String(100))  # mother, father, sibling, etc.
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="relatives")


# models/event.py
class EventStatus(str, Enum):
    DRAFT = "draft"
    COMPLETE = "complete"

class Event(Base):
    __tablename__ = "events"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)  # AI-generated
    time_anchor: Mapped[str | None] = mapped_column(String(255), nullable=True)  # "Spring 1956"
    time_anchor_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # Parsed for sorting
    place: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[EventStatus] = mapped_column(default=EventStatus.DRAFT)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="events")
    recordings: Mapped[list["AudioRecording"]] = relationship(back_populates="event", order_by="AudioRecording.sequence_order")
    follow_up_questions: Mapped[list["FollowUpQuestion"]] = relationship(back_populates="event", order_by="FollowUpQuestion.sequence_order")


# models/recording.py
class RecordingType(str, Enum):
    INITIAL_STORY = "initial_story"
    FOLLOW_UP_RESPONSE = "follow_up_response"

class AudioRecording(Base):
    __tablename__ = "audio_recordings"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    sequence_order: Mapped[int] = mapped_column(Integer)
    audio_url: Mapped[str] = mapped_column(String(1000))  # Supabase Storage URL
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    recording_type: Mapped[RecordingType] = mapped_column()
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    
    # Relationships
    event: Mapped["Event"] = relationship(back_populates="recordings")


# models/follow_up_question.py
class FollowUpQuestion(Base):
    __tablename__ = "follow_up_questions"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    sequence_order: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text)
    was_answered: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)  # TTS audio
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    
    # Relationships
    event: Mapped["Event"] = relationship(back_populates="follow_up_questions")
```

---

## 1.4 API Contracts (Detailed)

### Authentication

yaml

```
POST /api/auth/magic-link:
  description: Request magic link email
  request:
    body:
      email: string (required)
  response:
    200:
      success: boolean
      message: string
    400:
      error: "Invalid email format"

GET /api/auth/verify:
  description: Verify magic link token (handled by Supabase, redirects to app)
```

### Users

yaml

```
GET /api/users/me:
  description: Get current user profile with relatives
  auth: required
  response:
    200:
      user:
        id: uuid
        email: string
        name: string
        birth_date: date (ISO format)
        country_of_origin: string
        created_at: datetime
      relatives:
        - id: uuid
          name: string
          relationship: string

PUT /api/users/me:
  description: Update user profile
  auth: required
  request:
    body:
      name: string (optional)
      birth_date: date (optional)
      country_of_origin: string (optional)
  response:
    200:
      user: User

POST /api/users/me/relatives:
  description: Add a relative
  auth: required
  request:
    body:
      name: string (required)
      relationship: string (required)
  response:
    201:
      relative: Relative

DELETE /api/users/me/relatives/{relative_id}:
  description: Remove a relative
  auth: required
  response:
    200:
      success: boolean
```

### Events

yaml

```
GET /api/events:
  description: List all user events for timeline
  auth: required
  query:
    status: enum (draft, complete) (optional)
  response:
    200:
      events:
        - id: uuid
          title: string | null
          time_anchor: string | null
          time_anchor_date: date | null
          place: string | null
          status: enum
          summary: string | null (truncated to 200 chars)
          created_at: datetime

POST /api/events:
  description: Create new event (start session)
  auth: required
  response:
    201:
      event:
        id: uuid
        status: "draft"
        created_at: datetime

GET /api/events/{event_id}:
  description: Get event with all details
  auth: required
  response:
    200:
      event: Event
      recordings:
        - id: uuid
          sequence_order: int
          audio_url: string
          transcript: string | null
          recording_type: enum
          duration_seconds: float | null
      questions:
        - id: uuid
          sequence_order: int
          question_text: string
          was_answered: boolean
          audio_url: string | null

DELETE /api/events/{event_id}:
  description: Delete event and all associated data
  auth: required
  response:
    200:
      success: boolean

POST /api/events/{event_id}/complete:
  description: Complete session, generate summary
  auth: required
  response:
    200:
      event:
        id: uuid
        title: string (AI-generated)
        summary: string (AI-generated)
        status: "complete"
        # ... other fields

GET /api/events/{event_id}/export:
  description: Download event as zip file
  auth: required
  response:
    200:
      content-type: application/zip
      content-disposition: attachment; filename="event_{id}.zip"
      body: binary
```

### Recordings & Transcription

yaml

```
POST /api/events/{event_id}/recordings:
  description: Upload audio recording, get transcription
  auth: required
  request:
    content-type: multipart/form-data
    body:
      audio: file (required, webm/mp3/wav)
      recording_type: enum (initial_story, follow_up_response)
  response:
    201:
      recording:
        id: uuid
        sequence_order: int
        audio_url: string
        transcript: string
        recording_type: enum
        duration_seconds: float

GET /api/events/{event_id}/recordings/{recording_id}/audio:
  description: Stream audio file
  auth: required
  response:
    200:
      content-type: audio/webm (or appropriate)
      body: binary stream
```

### Interview Agent

yaml

```
POST /api/events/{event_id}/analyze:
  description: Analyze transcript(s) for event, determine what info is needed
  auth: required
  response:
    200:
      analysis:
        has_time: boolean
        time_anchor: string | null
        has_place: boolean
        place: string | null
        people_mentioned: string[]
        subjects_to_explore: string[]

POST /api/events/{event_id}/follow-up:
  description: Generate next follow-up question
  auth: required
  response:
    200:
      question:
        id: uuid
        question_text: string
        audio_url: string (TTS audio)

POST /api/events/{event_id}/follow-up/{question_id}/skip:
  description: Mark question as skipped
  auth: required
  response:
    200:
      success: boolean
```

### TTS

yaml

```
POST /api/tts:
  description: Generate speech from text
  auth: required
  request:
    body:
      text: string (required)
      voice: string (optional, default: "alloy")
  response:
    200:
      audio_url: string
```

### Publishing (Stretch)

yaml

```
POST /api/publish:
  description: Generate narrative from multiple events
  auth: required
  request:
    body:
      event_ids: uuid[] (required)
  response:
    200:
      narrative:
        text: string
        audio_url: string | null

POST /api/publish/export:
  description: Download published narrative as zip
  auth: required
  request:
    body:
      event_ids: uuid[]
  response:
    200:
      content-type: application/zip
      body: binary
```

---

## 1.5 File Structure (Finalized)

text

```
life-story-agent/
├── README.md
├── .gitignore
├── docker-compose.yml              # Local development
│
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Settings from env vars
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # Dependency injection (auth, db)
│   │   │   │
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── events.py
│   │   │   │   ├── recordings.py
│   │   │   │   ├── interview.py
│   │   │   │   ├── tts.py
│   │   │   │   └── export.py
│   │   │   │
│   │   │   └── schemas/
│   │   │       ├── __init__.py
│   │   │       ├── user.py         # Pydantic schemas
│   │   │       ├── event.py
│   │   │       ├── recording.py
│   │   │       └── interview.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── transcription.py
│   │   │   ├── tts.py
│   │   │   ├── interview_agent.py
│   │   │   ├── summary_generator.py
│   │   │   ├── timeline.py
│   │   │   └── export.py
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # SQLAlchemy Base
│   │   │   ├── user.py
│   │   │   ├── relative.py
│   │   │   ├── event.py
│   │   │   ├── recording.py
│   │   │   └── follow_up_question.py
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── session.py          # Database session management
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── audio.py            # Audio file handling
│   │       ├── date_parser.py      # Parse fuzzy dates to date objects
│   │       └── storage.py          # Supabase storage helpers
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py             # Pytest fixtures
│       ├── test_api/
│       │   ├── test_events.py
│       │   └── test_recordings.py
│       └── test_services/
│           ├── test_interview_agent.py
│           └── test_summary_generator.py
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── .env.example
│   │
│   ├── public/
│   │   ├── manifest.json           # PWA manifest
│   │   ├── sw.js                   # Service worker (basic)
│   │   └── icons/
│   │       ├── icon-192.png
│   │       └── icon-512.png
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css               # Tailwind imports
│       ├── vite-env.d.ts
│       │
│       ├── components/
│       │   ├── ui/                 # shadcn/ui components
│       │   │   ├── button.tsx
│       │   │   ├── input.tsx
│       │   │   ├── card.tsx
│       │   │   ├── dialog.tsx
│       │   │   └── ...
│       │   ├── AudioRecorder.tsx
│       │   ├── AudioPlayer.tsx
│       │   ├── Timeline.tsx
│       │   ├── EventCard.tsx
│       │   ├── BigButton.tsx
│       │   ├── LoadingSpinner.tsx
│       │   └── ConfirmDialog.tsx
│       │
│       ├── screens/
│       │   ├── LoginScreen.tsx
│       │   ├── OnboardingScreen.tsx
│       │   ├── TimelineScreen.tsx
│       │   ├── RecordingScreen.tsx
│       │   ├── InterviewScreen.tsx
│       │   ├── SummaryScreen.tsx
│       │   ├── EventDetailScreen.tsx
│       │   └── ExportScreen.tsx
│       │
│       ├── services/
│       │   ├── api.ts              # Axios/fetch API client
│       │   ├── auth.ts             # Supabase auth helpers
│       │   └── audio.ts            # MediaRecorder helpers
│       │
│       ├── hooks/
│       │   ├── useAuth.ts
│       │   ├── useRecorder.ts
│       │   ├── useEvents.ts
│       │   └── useAudioPlayer.ts
│       │
│       ├── context/
│       │   ├── AuthContext.tsx
│       │   └── SessionContext.tsx  # Current recording session state
│       │
│       ├── types/
│       │   └── index.ts            # TypeScript type definitions
│       │
│       └── utils/
│           ├── formatters.ts       # Date, time formatters
│           └── constants.ts
│
└── docs/
    ├── PROJECT_CONTEXT.md          # Your existing document
    ├── ARCHITECTURE.md             # This document
    └── API.md                      # API documentation
```

---

## 1.6 Environment Variables

### Backend (backend/.env.example)

bash

```
# ===================
# Supabase
# ===================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# ===================
# OpenAI
# ===================
OPENAI_API_KEY=sk-...

# ===================
# LangFuse (Observability)
# ===================
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com

# ===================
# Sentry (Error Tracking)
# ===================
SENTRY_DSN=https://...@sentry.io/...

# ===================
# Application
# ===================
ENVIRONMENT=development
LOG_LEVEL=info
CORS_ORIGINS=http://localhost:5173,https://your-app.vercel.app
```

### Frontend (frontend/.env.example)

bash

```
# ===================
# API
# ===================
VITE_API_URL=http://localhost:8000

# ===================
# Supabase
# ===================
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...

# ===================
# Sentry
# ===================
VITE_SENTRY_DSN=https://...@sentry.io/...
```
