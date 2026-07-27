# Supabase Removal Plan

> Date: 2026-07-27
> Status: Refined — VPS migration + local filesystem

---

## Context: Grand Plan

Supabase removal is part of a larger migration: **all backend infrastructure moves from managed services (Railway + Supabase) to a single VPS** (e.g. mikr.us) running Docker Compose. The frontend remains on Vercel.

| Before | After |
|--------|-------|
| **Backend** — Railway (FastAPI) | Backend — VPS, Docker container |
| **Database** — Supabase (managed PostgreSQL) | PostgreSQL 15 — VPS, Docker container, persistent volume |
| **File storage** — Supabase Storage (audio bucket) | Local filesystem — VPS, Docker volume, served through backend |
| **Auth** — Firebase (stays) | Firebase (stays) |
| **Frontend** — Vercel (stays) | Vercel (stays) |

---

## 1. Supabase Usage Catalog

### 1.1 PostgreSQL Database (Primary Usage)

Six tables with full schema:

| Table | Purpose | Columns | Files Using It |
|-------|---------|---------|----------------|
| `users` | User profiles | `id TEXT PK`, `email`, `name`, `birth_date`, `country_of_origin`, `preferred_language`, `created_at`, `updated_at` | `deps.py`, `users.py`, `main.py` |
| `relatives` | Family members | `id UUID PK`, `user_id TEXT FK`, `name`, `relationship`, `created_at` | `users.py` |
| `events` | Memory stories | `id UUID PK`, `user_id TEXT FK`, `title`, `time_anchor`, `time_anchor_date`, `place`, `status(enum)`, `summary`, `source_event_ids(JSON)`, `trace_id`, `created_at`, `updated_at` | `events.py`, `interview.py`, `api/utils.py` |
| `audio_recordings` | Audio files | `id UUID PK`, `event_id UUID FK`, `user_id TEXT`, `sequence_order`, `audio_url`, `transcript`, `recording_type(enum)`, `duration_seconds`, `created_at` | `events.py`, `recording_orchestrator.py` |
| `follow_up_questions` | AI questions | `id UUID PK`, `event_id UUID FK`, `sequence_order`, `question_text`, `was_answered`, `audio_url`, `created_at` | `interview.py`, `recording_orchestrator.py` |
| `evaluation_results` | Quality scores | `id UUID PK`, `event_id UUID FK`, `eval_type`, `factual_accuracy`, `coherence`, `completeness`, `overall_score`, `evaluator_model`, `created_at` | `evaluations.py`, `evaluation.py` |

**DB operations**: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `ORDER`, `LIMIT`, `eq/is_` filters, `count(exact)`. Standard CRUD — nothing exotic.

**API style used**:
```python
supabase = await get_supabase_client()
result = supabase.table("events").select("*").eq("user_id", uid).order("time_anchor_date").execute()
data = result.data  # list[dict]
```

**Config env vars consumed by backend**: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`

### 1.2 Supabase Storage (File Storage)

**1 bucket**: `audio-recordings` (private)

Operations from `services/storage.py`:
- `storage.from_(BUCKET).download(path)` — stream audio for playback
- `storage.from_(BUCKET).upload(path, data, opts)` — upload new recordings
- `storage.from_(BUCKET).get_public_url(path)` — get URL for DB storage
- `storage.from_(BUCKET).remove([paths])` — delete on event deletion

URL pattern:
```
https://<project>.supabase.co/storage/v1/object/public/audio-recordings/<user_id>/<event_id>/<uuid>.webm
```

**Critical finding**: The `audio_url` field in the DB is an **opaque identifier only**. The frontend never accesses it as an HTTP URL. All audio flows through `GET /api/events/{id}/recordings/{rid}/audio` which resolves the path to bytes server-side. This makes local filesystem storage viable.

### 1.3 Supabase Auth (Legacy / Dead Code)

- **Original plan**: Supabase Auth for magic links + RLS policies
- **Current reality**: Migration `007` disables RLS; Firebase Auth is used instead
- **Remnant**: `DebugScreen.tsx` calls `supabase.auth.getSession()` — unused in production
- **Frontend lib**: `src/lib/supabase.ts` creates a Supabase client — only used in DebugScreen and test mocks
- **Env vars**: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` — only consumed by DebugScreen

**Supabase Auth can be removed with zero production impact.**

---

## 2. Replacement Services

| Current Service | Replacement | What It Provides |
|----------------|-------------|------------------|
| Supabase PostgreSQL | **PostgreSQL 15** (Docker) | All structured data (6 tables), persistent Docker volume |
| Supabase Storage (audio) | **Local filesystem** (Docker volume) | Audio files stored at `/data/audio-recordings/`, served through backend |
| Supabase Auth | **Removed** (no replacement) | Firebase Auth covers all auth needs |
| Railway (hosting) | **VPS** (Docker Compose host) | Runtime for backend + PostgreSQL + audio volume |

### Storage Decision: Local Filesystem over MinIO

The `audio_url` in the database is never used as a direct HTTP URL by the frontend. It serves only as:
- An opaque path identifier to resolve bytes server-side
- A cross-reference key between `audio_recordings` and `follow_up_questions` tables
- A truthiness flag ("does this recording have audio?")

The backend proxies all audio through `GET /api/events/{id}/recordings/{rid}/audio`, which calls `StorageService.download(audio_url)` → reads bytes → streams to client. No public URL, pre-signed URL, or HTTP serving from storage is needed.

**Local filesystem** is the simplest solution:
- Write: `open(storage_root / path, 'wb').write(data)`
- Read: `open(storage_root / path, 'rb').read()`
- Delete: `os.remove(storage_root / path)`
- Docker volume at `/data/audio-recordings/` for persistence
- Zero additional containers, zero network overhead

MinIO would add an entire S3-compatible service for what amounts to three filesystem calls. Not justified in a single-instance VPS deployment.

---

## 3. What Changes vs. What Stays

| Layer | Changes | Stays |
|-------|---------|-------|
| **DB client** (`db/client.py`) | Full rewrite — Supabase SDK → asyncpg | Interface shape (async connection pool) |
| **DB helpers** (`api/utils.py`) | Rewrite — 4 helpers accept new DB client type | Logic (query patterns) unchanged |
| **Auth dependency** (`api/deps.py`) | Rewrite — user lookup via raw SQL | Auth flow (Firebase token → DB lookup) unchanged |
| **Route files** (5 files) | Partial rewrite — DB calls change style | Route structure, params, responses unchanged |
| **Service files** (3 files) | Partial rewrite — DB/storage calls change | Business logic unchanged |
| **Storage** (`services/storage.py`) | Rewrite — Supabase Storage → local filesystem `open/read/write/remove` | Interface (download/upload/remove) unchanged |
| **Storage** (`services/transcription.py`) | Minor — URL pattern check removed, downloads via new storage | Transcription logic unchanged |
| **Config** (`config.py`) | Replace 4 Supabase vars → `DATABASE_URL` + `AUDIO_STORAGE_PATH` | Other settings unchanged |
| **Main** (`main.py`) | Minor — health check queries change | App lifecycle unchanged |
| **pyproject.toml** | Remove `supabase`, add `asyncpg` | Other deps unchanged |
| **Docker** | New `Dockerfile` + `docker-compose.yml` for VPS | — |
| **CI/CD** | Railway deploys → deploy scripts for VPS | — |
| **Frontend** | Minimal — remove `lib/supabase.ts`, update test mocks | All other frontend code unchanged |
| **Tests** (`conftest.py`) | Rewrite — mock DB client replaces MockSupabaseClient | Test coverage targets unchanged |

---

## 4. Files Requiring Changes

### Backend Python Files

| File | Change Type | Notes |
|------|-------------|-------|
| `app/db/client.py` | Full rewrite | `asyncpg.create_pool()` + `init_pool()` / `close_pool()` lifecycle |
| `app/config.py` | Change env vars | Replace `SUPABASE_*` with `DATABASE_URL`, `AUDIO_STORAGE_PATH` |
| `app/main.py` | Minor | Health/ready check queries rewritten |
| `app/api/deps.py` | Rewrite | User lookup via raw SQL |
| `app/api/utils.py` | Rewrite (4 helpers) | `get_next_sequence_order`, `get_event_for_user`, `get_user_language` — raw SQL |
| `app/api/routes/events.py` | Partial rewrite | ~30 DB calls + 2 storage calls |
| `app/api/routes/interview.py` | Partial rewrite | ~8 DB calls |
| `app/api/routes/users.py` | Partial rewrite | ~12 DB calls |
| `app/api/routes/evaluations.py` | Partial rewrite | ~4 DB calls |
| `app/services/recording_orchestrator.py` | Partial rewrite | ~6 DB calls, storage upload path changes |
| `app/services/evaluation.py` | Partial rewrite | ~6 DB calls |
| `app/services/event_completion.py` | Partial rewrite | ~2 DB calls |
| `app/services/storage.py` | Full rewrite | Local FS `open/read/write/remove` instead of Supabase Storage SDK |
| `app/services/transcription.py` | Minor | Remove Supabase URL check, use new storage download |
| `app/tests/conftest.py` | Full rewrite | Replace `MockSupabaseClient` with mock DB service |

**Total**: ~85+ individual DB query sites across the codebase.

### Frontend Files

| File | Change Type |
|------|-------------|
| `src/lib/supabase.ts` | Delete |
| `src/components/DebugScreen.tsx` | Remove Supabase auth reference; keep Firebase token debugging |
| `src/test/mocks.ts` | Remove `@supabase/supabase-js` mock |
| Test files mocking `lib/supabase` (4 files) | Update mocks |

### New Files

| File | Purpose |
|------|---------|
| `/Dockerfile` | Build backend container from `app/` |
| `/docker-compose.yml` | Orchestrate postgres + backend + audio volume + Caddy |
| `/docker-compose.test.yml` | Test environment with postgres for integration tests |
| `/Caddyfile` | Reverse proxy config for `api.lifestoryagent.uk` |
| `/app/db/deps.py` | FastAPI dependency injectors for domain repositories |
| `/app/db/repositories/__init__.py` | Package init — exports all 4 repository classes |
| `/app/db/repositories/user_repo.py` | `UserRepository` — profiles, relatives |
| `/app/db/repositories/event_repo.py` | `EventRepository` — stories/events |
| `/app/db/repositories/recording_repo.py` | `RecordingRepository` — audio_recordings + follow_up_questions |
| `/app/db/repositories/evaluation_repo.py` | `EvaluationRepository` — evaluation_results |
| `/.env.example` | Template listing all required env vars |
| `/.github/workflows/ci.yml` | GitHub Actions workflow (unit → integration → deploy) |
| `/scripts/migrate-db.sh` | Dump Supabase PostgreSQL → restore to Docker PostgreSQL |
| `/scripts/migrate-storage.py` | Download audio from Supabase Storage → write to local FS volume |

---

## 5. Target Architecture

```
VPS (Docker Compose)                                      Vercel
├── caddy:2-alpine                                         ├── Frontend (React PWA)
│   ├── port 443 (HTTPS)            <─────────────┐        └── API calls ──→ api.lifestoryagent.uk
│   ├── TLS: api.lifestoryagent.uk                └──────────────────────────────┘    
│   ├── reverse_proxy → backend:8000     
│   └── volumes: caddy_data, caddy_config
│                                        
├── backend (FastAPI)
│   ├── port 8000 (internal, not exposed)
│   ├── reads/writes → postgres (localhost:5432)
│   ├── reads/writes → /data/audio-recordings/
│   ├── depends_on: [postgres]
│   └── env: DATABASE_URL, AUDIO_STORAGE_PATH, OPENAI_API_KEY, FIREBASE_*
│
├── postgres:15-alpine
│   ├── port 5432 (internal, not exposed)
│   └── volume: pgdata (persistent)
│
├── audio-storage (Docker volume)
│   └── /data/audio-recordings/{user_id}/{event_id}/{uuid}.webm
│
└── network: internal bridge (postgres and backend not exposed publicly)
```

### Key differences from Railway deployment

| Aspect | Railway | VPS (Docker Compose) |
|--------|---------|----------------------|
| File persistence | Ephemeral — audio lost on restart | Persistent Docker volume |
| DB connection | Remote Supabase URL | Local `postgres:5432` — no network latency |
| Storage I/O | HTTPS to Supabase Storage REST API | Local filesystem `open/read/write` — zero latency |
| Secrets | Railway dashboard | `.env` file on VPS |
| Deploy | `git push` to Railway | `docker compose pull && docker compose up -d` |
| HTTPS/TLS | Automatic Railway SSL | Reverse proxy (Caddy / nginx) on VPS |

---

## 6. Implementation Strategy

### Step 1: Database abstraction layer

Replace `db/client.py` (Supabase SDK → asyncpg). Set up a connection pool, domain repository classes, and a FastAPI dependency for injection.

```python
# app/db/client.py
import asyncpg
from typing import AsyncGenerator

pool: asyncpg.Pool | None = None

async def init_pool(dsn: str) -> None:
    """Initialize the connection pool. Called once at startup."""
    global pool
    pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)

async def close_pool() -> None:
    """Close the connection pool. Called once at shutdown."""
    global pool
    if pool:
        await pool.close()
        pool = None

async def get_pool() -> asyncpg.Pool:
    """Get the connection pool (asserts initialized)."""
    assert pool is not None, "Database pool not initialized"
    return pool
```

```python
# app/db/deps.py (new)
from typing import AsyncGenerator
from fastapi import Request
from app.db.repositories import UserRepository, EventRepository, RecordingRepository, EvaluationRepository

async def get_user_repo(request: Request) -> UserRepository:
    return UserRepository(request.app.state.pool)

async def get_event_repo(request: Request) -> EventRepository:
    return EventRepository(request.app.state.pool)

async def get_recording_repo(request: Request) -> RecordingRepository:
    return RecordingRepository(request.app.state.pool)

async def get_evaluation_repo(request: Request) -> EvaluationRepository:
    return EvaluationRepository(request.app.state.pool)
```

```python
# app/db/repositories/__init__.py (new package)

# UserRepository — profiles, relatives
class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def fetch_by_email(self, email: str) -> dict | None: ...
    async def upsert(self, id: str, email: str, preferred_language: str = "pl") -> dict: ...
    async def update_profile(self, user_id: str, data: dict) -> None: ...
    async def fetch_language(self, user_id: str) -> str: ...
    async def fetch_relatives(self, user_id: str) -> list[dict]: ...
    async def insert_relative(self, user_id: str, name: str, relationship: str) -> dict: ...
    async def delete_relative(self, relative_id: str, user_id: str) -> None: ...

# EventRepository — stories/events
class EventRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def fetch_by_id(self, event_id: str, user_id: str) -> dict | None: ...
    async def fetch_all_by_user(self, user_id: str) -> list[dict]: ...
    async def create(self, data: dict) -> dict: ...
    async def update(self, event_id: str, data: dict) -> None: ...
    async def delete(self, event_id: str) -> None: ...
    async def fetch_trace_id(self, event_id: str) -> str | None: ...

# RecordingRepository — audio_recordings + follow_up_questions
class RecordingRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def fetch_by_event(self, event_id: str) -> list[dict]: ...
    async def fetch_by_id(self, recording_id: str) -> dict | None: ...
    async def insert(self, data: dict) -> dict: ...
    async def update_transcript(self, recording_id: str, transcript: str) -> None: ...
    async def fetch_url(self, recording_id: str, event_id: str) -> str | None: ...
    async def fetch_urls_by_event(self, event_id: str) -> list[str]: ...
    async def next_sequence_order(self, table: str, event_id: str) -> int: ...
    # Follow-up questions
    async def fetch_unanswered_question(self, event_id: str) -> dict | None: ...
    async def mark_answered(self, question_id: str, audio_url: str) -> None: ...
    async def insert_question(self, data: dict) -> dict: ...
    async def delete_unanswered(self, event_id: str) -> None: ...

# EvaluationRepository — evaluation_results
class EvaluationRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def insert(self, data: dict) -> None: ...
    async def fetch_recent(self, eval_type: str | None, limit: int = 10) -> list[dict]: ...
    async def count(self, eval_type: str | None) -> int: ...
```

Each route file injects the required repository via FastAPI `Depends`:
```python
from app.db.deps import get_event_repo

@router.get("/events")
async def list_events(repo: EventRepository = Depends(get_event_repo)):
    return await repo.fetch_all_by_user(...)
```

### Step 2: Storage layer rewrite

Replace `services/storage.py` with local filesystem operations using `aiofiles`:

```python
# services/storage.py
from pathlib import Path
import aiofiles

STORAGE_ROOT = Path("/data/audio-recordings")

class StorageService:
    def __init__(self, storage_root: Path = STORAGE_ROOT):
        self.root = storage_root

    async def upload(self, file_path: str, data: bytes, content_type: str = "audio/webm") -> str:
        """Write audio bytes to local filesystem. Returns the path string (not a URL)."""
        full_path = self.root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)
        return file_path

    async def download(self, audio_path: str) -> bytes:
        """Read audio bytes from local filesystem by path."""
        full_path = self.root / audio_path
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def remove(self, audio_path: str) -> None:
        """Delete a single audio file."""
        (self.root / audio_path).unlink(missing_ok=True)

    async def remove_many(self, audio_paths: list[str]) -> None:
        """Delete multiple audio files."""
        for path in audio_paths:
            await self.remove(path)
```

### Pool lifecycle in main.py

The connection pool must be initialized on startup and closed on shutdown:

```python
# app/main.py (changes)
from db.client import init_pool, close_pool
from config import get_settings

settings = get_settings()

@app.on_event("startup")
async def startup():
    init_sentry()
    init_langfuse()
    await init_pool(settings.database_url)  # new
    # ... firebase init unchanged ...

@app.on_event("shutdown")
async def shutdown():
    await close_pool()  # new
```

The pool is stored in `app.state.pool` so the FastAPI dependency can reach it.

### pyproject.toml changes

```diff
 dependencies = [
     "fastapi>=0.115.0",
     ...
-    "supabase>=2.0.0",
+    "asyncpg>=0.30",
+    "aiofiles>=24.1.0",
 ]
```

**`audio_url` column meaning changes**: from full Supabase URL to path string like `{user_id}/{event_id}/{uuid}.webm`. Existing data needs a one-time migration (strip Supabase URL prefix, keep path portion — `_parse_storage_path` already does this).

### Transcription URL logic

The current `transcribe_audio_url()` in `services/transcription.py` checks for Supabase Storage URL pattern:

```python
# Before (Supabase)
if "/storage/v1/object/" in audio_url:
    storage = StorageService()
    audio_content = await storage.download(audio_url)
    return await transcribe_audio_data(audio_content, language)
# Fallback: try direct HTTP download
async with httpx.AsyncClient() as client:
    response = await client.get(audio_url)
```

After migration, `audio_url` is a plain path (e.g. `user_abc/evt_456/rec_789.webm`). The logic becomes:

```python
# After (local filesystem)
# audio_url is a plain path like "user_abc/evt_456/rec_789.webm"
# No HTTP fallback needed — all audio is local
storage = StorageService()
audio_content = await storage.download(audio_url)
return await transcribe_audio_data(audio_content, language)
```

The HTTP fallback branch is removed entirely.

### Step 3: Config and env vars

```
# Before (Supabase)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=xxxx
SUPABASE_SERVICE_KEY=xxxx
SUPABASE_JWT_SECRET=xxxx

# After (VPS)
# ── Database ───────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://app:your_db_password@postgres:5432/life_story_agent
AUDIO_STORAGE_PATH=/data/audio-recordings

# ── AI / OpenAI ────────────────────────────────────
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
TTS_MODEL=gpt-4o-mini-tts

# ── Auth (Firebase) ────────────────────────────────
FIREBASE_CREDENTIALS={"type":"service_account",...}
FIREBASE_PROJECT_ID=your-firebase-project

# ── CORS ───────────────────────────────────────────
CORS_ORIGINS=https://www.lifestoryagent.uk,http://localhost:5173

# ── Observability ──────────────────────────────────
SENTRY_DSN=https://...
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com

# ── Application ────────────────────────────────────
ENVIRONMENT=production
LOG_LEVEL=info
ADMIN_EMAIL=your@email.com
EVAL_ENABLED=false
EVAL_SAMPLE_RATE=0.1
MAX_META_STORY_SELECT=10
```

Note: `DB_PASSWORD` is a Compose-level variable used in `docker-compose.yml` to set postgres credentials. It's referenced as `${DB_PASSWORD}` in the compose file and must be in the `.env` file as well.

### CORS_ORIGINS

The config defaults to `http://localhost:5173`. In production it must include the frontend domain:

```python
# config.py
cors = os.getenv("CORS_ORIGINS", "http://localhost:5173")
# After VPS migration, set:
# CORS_ORIGINS=https://www.lifestoryagent.uk,http://localhost:5173
```

### Step 4: Docker setup

```dockerfile
# Dockerfile — optimized for layer caching
FROM python:3.12-slim AS builder
WORKDIR /app
COPY app/pyproject.toml app/uv.lock ./
RUN pip install uv && uv sync --frozen --no-install-project
# ^ dep layer: only re-runs when pyproject.toml or uv.lock changes

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY app/ .
# ^ code layer: cached as long as deps haven't changed
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The builder stage installs dependencies first (cached until `pyproject.toml`/`uv.lock` change), then the final stage copies the pre-built `.venv` + application code. A code-only change skips the `uv sync` step entirely — seconds instead of minutes on deploy.

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./supabase/migrations:/docker-entrypoint-initdb.d
    environment:
      POSTGRES_DB: life_story_agent
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d life_story_agent"]
      interval: 5s

  backend:
    build: .
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - audio-data:/data/audio-recordings
    depends_on:
      postgres:
        condition: service_healthy
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://app:${DB_PASSWORD}@postgres/life_story_agent
      AUDIO_STORAGE_PATH: /data/audio-recordings

volumes:
  pgdata:
  audio-data:
```

### Step 5: Reverse proxy (Caddy)

Your existing domain setup:

```
User ──→ www.lifestoryagent.uk ──→ Vercel (frontend)
                              ├── serves HTML/JS at /
                              └── rewrites /api/* → api.lifestoryagent.uk
                                                       │
                                       Cloudflare DNS ─┤
                                                       │
                              Currently: → Railway
                              After VPS:  → VPS IP
```

The VPS needs to accept `https://api.lifestoryagent.uk` and forward to the backend container. **Caddy as a Docker container** is the cleanest approach — it handles TLS (auto-letsencrypt), lives in the same Compose network, and references the backend by service name.

```yaml
# docker-compose.yml (added to the services block)
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on: [backend]
    # Caddy auto-provisions TLS for api.lifestoryagent.uk via Let's Encrypt

volumes:
  pgdata:
  audio-data:
  caddy_data:
  caddy_config:
```

```caddyfile
# Caddyfile
api.lifestoryagent.uk {
    reverse_proxy backend:8000
}
```

**No Cloudflare changes needed** — only the DNS A/AAAA record for `api.lifestoryagent.uk` changes from Railway's IP to the VPS IP. Vercel, Cloudflare, and `www.lifestoryagent.uk` remain untouched.

**Alternative (no container)**: Install Caddy directly on the VPS host. Same Caddyfile, same behavior. The container approach is preferred because:
- Single source of truth (`docker compose up -d`)
- Caddy version pinned in Compose, not left to the host's package manager
- All logs go through Docker, not syslog

### Step 6: CI/CD

**No webhook needed.** Deployment is the final step of a GitHub Actions workflow — after all tests pass, the workflow SSHes into the VPS and runs the deploy commands. Everything stays inside a single `.github/workflows/ci.yml` file.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: pip install uv
      - name: Install backend deps
        working-directory: app
        run: uv sync --frozen
      - name: Run backend unit tests
        working-directory: app
        run: uv run pytest tests/ -x -q --ignore=tests/integration
      - name: Install frontend deps
        run: npm ci
      - name: Run frontend unit tests
        run: npm test -- --run

  integration:
    needs: [unit]
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: life_story_agent_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
    steps:
      - uses: actions/checkout@v4
      - name: Init DB schema
        run: psql $DATABASE_URL < supabase/migrations/001_initial_schema.sql
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/life_story_agent_test
      - name: Install uv
        run: pip install uv
      - name: Install deps
        working-directory: app
        run: uv sync --frozen
      - name: Run integration tests
        working-directory: app
        run: uv run pytest tests/integration/ -x -q

  deploy:
    needs: [integration]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/life-story-agent
            git pull
            docker compose up -d --build
```

**GitHub secrets needed** (configured in repo Settings → Secrets and variables → Actions):

| Secret | Value |
|--------|-------|
| `VPS_HOST` | IP or hostname of the VPS |
| `VPS_USER` | SSH username |
| `VPS_SSH_KEY` | Private SSH key (deploy key) added to VPS `authorized_keys` |

**VPS prerequisites**: `git`, `docker`, `docker compose` installed; project cloned at `/opt/life-story-agent`; SSH key in `~/.ssh/authorized_keys`.

### Step 7: Frontend API URL update

Vercel env var `VITE_API_URL` changes from `https://life-story-agent-production.up.railway.app` to `https://api.lifestoryagent.uk`. No code changes needed — the frontend already uses a relative `/api/*` proxy in dev and an env var for production.

---

## 7. Data Migration

### 7.1 PostgreSQL

**Your assumption is correct** — `pg_dump` captures the fully-migrated state of the Supabase database including all schema changes (DDL) and data. The restored database is immediately ready: no migrations need to run on top of it. The Supabase SQL migrations in `supabase/migrations/` are only needed when bootstrapping a fresh (empty) database.

The dump can be produced either via `pg_dump` directly or the Supabase CLI:

```bash
# Option A: pg_dump (direct, no Supabase CLI needed)
pg_dump --no-owner --no-acl \
  "postgresql://$SUPABASE_USER:$SUPABASE_PASS@$SUPABASE_HOST:5432/postgres" \
  > supabase_dump.sql

# Option B: supabase CLI (if you have it linked to the Supabase project)
supabase db dump --remote -f supabase_dump.sql
```

Restore to the Docker PostgreSQL:

```bash
docker compose exec -T postgres psql -U app life_story_agent < supabase_dump.sql
```

Then transform `audio_url` values from full Supabase Storage URLs to plain paths (one-time):

```bash
docker compose exec -T postgres psql -U app life_story_agent <<SQL
UPDATE audio_recordings SET audio_url = split_part(audio_url, '/audio-recordings/', 2);
UPDATE follow_up_questions SET audio_url = split_part(audio_url, '/audio-recordings/', 2) WHERE audio_url IS NOT NULL;
SQL
```

### 7.2 Audio file transfer

**Purpose**: Copy all existing audio files from Supabase Storage into the local Docker volume so no data is lost during the migration.

**How it works**: A one-shot Python script runs locally (or from a temporary container that has access to both Supabase and the target volume). It uses the existing Supabase client one final time to download every audio file, then writes it to the matching path under `/data/audio-recordings/`.

```python
# scripts/migrate_storage.py
# Run once after PostgreSQL data is restored to the new server.
# Reads audio_url paths from the (already migrated) database,
# downloads each file from Supabase Storage, writes to local volume.
#
# Requires: SUPABASE_URL, SUPABASE_SERVICE_KEY, AUDIO_STORAGE_PATH

import os, asyncio
from supabase import create_client
from services.storage import StorageService  # new local-fs version

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
storage = StorageService()  # reads/writes /data/audio-recordings/

async def migrate():
    result = supabase.table("audio_recordings").select("audio_url").neq("audio_url", None).execute()
    for row in result.data:
        path = row["audio_url"].split("/audio-recordings/")[1]  # strip Supabase URL prefix
        # Download from Supabase (last time)
        blob = supabase.storage.from_("audio-recordings").download(path)
        # Write to local volume
        await storage.upload(path, blob)
        print(f"migrated: {path}")

asyncio.run(migrate())
```

After this script completes, the Supabase Storage bucket can be deleted — all data lives on the local Docker volume.

---

## 8. Testing Strategy

### 8.1 Levels

| Level | Scope | Services Needed | Speed |
|-------|-------|----------------|-------|
| **Unit** | Individual functions, `DatabaseService` method, `StorageService` method | None (mocked) | ~30s |
| **Integration** | Route handlers against a real PostgreSQL | `postgres:15` container | ~1m |
| **E2E** | Full flow: frontend → backend → DB → storage | Entire `docker-compose` stack | ~5m |

### 8.2 Unit Tests (PR/commit gate)

The existing `conftest.py` mock infrastructure is replaced: `MockSupabaseClient` becomes `MockDatabaseService` (same pattern, different name). All current test patterns stay the same — mock a class, assert calls, return canned data.

`StorageService` is tested with `tempfile.TemporaryDirectory` instead of a real volume:

```python
def test_storage_upload_download(tmp_path):
    svc = StorageService(storage_root=tmp_path)
    path = svc.upload("user/a/b.webm", b"audio data")
    assert svc.download(path) == b"audio data"
```

**No external services needed for unit tests.** They run in CI with just `pytest`.

### 8.3 Integration Tests (optional, before deploy)

Spin up a test environment with `docker-compose.test.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: life_story_agent_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"  # different port to avoid conflict with dev
    volumes:
      - ./supabase/migrations:/docker-entrypoint-initdb.d

  backend:
    build: .
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql+asyncpg://test:test@postgres:5432/life_story_agent_test
      AUDIO_STORAGE_PATH: /tmp/test-audio
```

Run against the live DB/storage but with known fixtures. Useful for testing route handlers end-to-end.

### 8.4 CI/CD (GitHub Actions)

```yaml
# .github/workflows/test.yml
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: pip install uv
      - name: Install deps
        working-directory: app
        run: uv sync --frozen
      - name: Run unit tests
        working-directory: app
        run: uv run pytest tests/ -x -q --ignore=tests/integration
      - name: Run frontend tests
        run: npm test -- --run

  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: life_story_agent_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
    steps:
      - uses: actions/checkout@v4
      - name: Init DB schema
        run: psql $DATABASE_URL < supabase/migrations/001_initial_schema.sql
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/life_story_agent_test
      - name: Run integration tests
        working-directory: app
        run: uv run pytest tests/integration/ -x -q
```

The `integration` job uses GitHub Actions' built-in `services:` feature to run a PostgreSQL container alongside the test runner. The `backend` service from `docker-compose` is not needed — tests instantiate the Python `DatabaseService` directly against the service container's port, which is faster and avoids Docker-in-Docker complexity.

E2E tests (if added later) would spin up the full `docker-compose` stack inside a self-hosted runner or a dedicated CI job with Docker Compose installed.

### 8.5 Local Development

```bash
# Run unit tests (no infra needed)
cd app && uv run pytest

# Run integration tests (auto-starts postgres via testcontainers-pytest or manual docker compose)
docker compose -f docker-compose.test.yml up -d postgres
DATABASE_URL=postgresql://test:test@localhost:5433/life_story_agent_test \
  uv run pytest tests/integration/
docker compose -f docker-compose.test.yml down

# Run full stack for manual testing
docker compose up -d
# Backend at localhost:8000, DB at localhost:5432
```

---

## 9. Schema Notes

The `pg_dump` from Supabase captures the fully migrated schema — no raw migration files need to be re-interpreted. Differences from the initial Supabase template that are already reflected in the dump:

* RLS policies and Supabase Auth triggers — **absent** (removed in migration `007`)
* Storage bucket policies — **absent** (never part of the PG schema)
* `users.id` column — **`TEXT` type** (not `UUID`, changed in migration `007`)
* `source_event_ids` and `trace_id` columns on `events` — **present** (added in `002`, `006`)
* `audio_url` values — stored as **full Supabase Storage URLs**; see §7.1 for the one-time conversion to plain paths after restore

---

## 10. System Design Document Updates

The following sections in `docs/system-design.md` refer to Supabase or Railway and must be updated to reflect the new architecture.

### 10.1 Section 2 — High-Level System Architecture

**Mermaid diagram** — replace the `External["Managed Services"]` subgraph:

```diff
     subgraph External["Managed Services"]
-        T[(Supabase PostgreSQL)]
         U[Firebase Auth]
-        V[Supabase Storage]
+        T[(PostgreSQL 15 — VPS Docker volume)]
+        V[Local filesystem — VPS Docker volume]
     end

-    J --> T
-    J --> V
+    J --> T   (asyncpg)
+    J --> V   (aiofiles)
```

**Component Responsibilities table** — update two rows:

| Database | ~~Supabase PostgreSQL~~ → **PostgreSQL 15 (Docker on VPS)** | User profiles, events, recordings, questions, evaluations |
| Storage | ~~Supabase Storage~~ → **Local filesystem (Docker volume on VPS)** | Private audio bucket for webm recordings |

### 10.2 Section 3.5 — Firebase Auth + Supabase Storage

Rename and update:

```diff
-### 3.5 Firebase Auth + Supabase Storage
+### 3.5 Firebase Auth + Self-Hosted PostgreSQL
```

Update rationale:

```diff
- **Decision**: Use Firebase Authentication with Supabase for database and storage.
+ **Decision**: Use Firebase Authentication with self-hosted PostgreSQL and local filesystem.

 **Rationale**:
 - Firebase provides reliable magic link + Google OAuth authentication
 - Backend verifies Firebase ID tokens directly (no Supabase Auth JWT)
-- Supabase managed PostgreSQL with backups for structured data
-- Supabase Storage for audio files
-- Free tiers sufficient for MVP
+- PostgreSQL 15 in Docker with persistent volume for structured data
+- Local filesystem Docker volume for audio files (lower latency, no network hop)
+- Single VPS eliminates dependency on external managed services

 **Trade-off**: Two separate auth systems (Firebase for auth, Supabase for data) vs. a unified Supabase Auth approach.
+**Updated trade-off**: Operating the database requires VPS maintenance (backups, upgrades) vs. a fully managed service.
```

### 10.3 Section 4 — Core User Journey

**Sequence diagram** — rename participants:

```diff
-    participant DB as Supabase DB
-    participant S3 as Supabase Storage
+    participant DB as PostgreSQL (VPS)
+    participant FS as Local Filesystem (VPS)
```

Label changes in the diagram:

```diff
-    BE->>S3: Upload audio.webm
-    S3-->>BE: public_url
+    BE->>FS: Write audio.webm
+    FS-->>BE: file_path
```

### 10.4 Section 6 — Client-Side Encryption & Dance Flow

**Encryption flowchart** — update the Backend and Database subgraphs:

```diff
     subgraph Backend["Backend (FastAPI)"]
         E[API Routes]
-        F[Supabase Client]
+        F[asyncpg + repositories]
     end

-    subgraph Database["Supabase"]
+    subgraph Database["PostgreSQL (Docker on VPS)"]
         G[(PostgreSQL)]
-        H[Storage Bucket]
+        H[Local audio volume]
     end
```

**Dance Flow diagram** — rename participant:

```diff
-    participant DB as Supabase
+    participant DB as PostgreSQL
```

### 10.5 Section 7 — Technology Stack

Update the table rows:

| Technology | ~~Version~~ | ~~Purpose~~ | Change |
|-----------|------------|------------|--------|
| Database ORM | ~~Supabase Python SDK 2~~ → **asyncpg 0.30+** | PostgreSQL client | Replace row |
| Object Storage | ~~Supabase Storage~~ → **Local filesystem (Docker volume)** | Private audio bucket | Replace row |
| Hosting (BE) | ~~Railway~~ → **VPS (Docker Compose)** | Container deployment | Replace row |
| Async HTTP | ~~httpx — Supabase client, external APIs~~ → **httpx — external APIs only** | Update description | |

Add new row:

| Technology | Version | Purpose |
|-----------|---------|---------|
| Async File I/O | aiofiles 24.1+ | Local filesystem audio read/write |

### 10.6 Section 9 — Deployment Architecture

**Mermaid diagram** — replace the entire diagram:

```diff
-    subgraph Railway["Railway (Container)"]
-        D[FastAPI Backend]
-        E[Python 3.12 Runtime]
-    end
+    subgraph VPS["VPS (Docker Compose)"]
+        D[Caddy Reverse Proxy :443]
+        E[FastAPI Backend :8000]
+    end

-    subgraph Supabase["Supabase Project"]
-        F[(PostgreSQL)]
-        G[Storage Bucket]
-        H[PostgREST API]
-    end
+    subgraph VPS_Data["VPS (Docker Volumes)"]
+        F[(PostgreSQL 15)]
+        G[Audio Files Volume]
+    end
```

Update arrows:

```diff
-    D -->|Supabase SDK| F
-    D -->|Supabase Storage| G
-    D -->|HTTP/JSON| H
+    E -->|asyncpg| F
+    E -->|aiofiles| G
```

**Environment Configuration table**:

| Service | Local Dev | Production |
|---------|-----------|------------|
| Backend | `http://localhost:8000` | `https://api.lifestoryagent.uk` |
| Database | ~~Supabase managed PostgreSQL~~ → **PostgreSQL 15 Docker container** | PostgreSQL 15 Docker container (same VPS) |
| Storage | ~~Supabase (shared)~~ → **Local Docker volume** | Local Docker volume (same VPS) |

### 10.7 Section 10 — Security & Privacy

Update Data Protection:

```diff
- **Private Storage**: Audio bucket is private; all playback goes through authenticated streaming endpoints.
+ **Private Storage**: Audio files stored on local Docker volume; all playback goes through authenticated streaming endpoints. The volume is not directly exposed to the internet.
```

### 10.8 Section 13 — API Contract Summary

Bump document version:

```
- *Document version: 1.4 | Last updated: 2026-05-18*
+ *Document version: 2.0 | Last updated: 2026-07-27*
```
