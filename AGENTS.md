# AGENTS.md - Life Story Preservation Agent

## Project Overview

Conversational AI system that helps elderly users capture life memories through voice interaction. AI acts as oral historian - transcribes stories, generates follow-up questions, creates summaries.

**Primary user:** 80-year-old Polish-speaking person on Android smartphone.

**Key constraint:** Client-side AES-256-GCM encryption - backend never sees plaintext user content.

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI   │────▶│  Aurora    │
│   PWA       │     │   Backend   │     │  PostgreSQL│
│  (Vite)     │     │  (uvicorn)  │     │  (asyncpg) │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                    ┌─────▼─────┐     ┌─────────────┐
                    │    S3     │     │  Cognito    │
                    │  (audio)  │     │  (auth)     │
                    └───────────┘     └─────────────┘
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Python 3.12, FastAPI, Pydantic | ASGI with uvicorn |
| Database | Aurora PostgreSQL 16.4 | asyncpg driver, NOT Supabase |
| Auth | AWS Cognito | JWT validation, auto-create user on first login |
| Storage | AWS S3 (boto3) | Audio files, NOT Supabase Storage |
| LLM | OpenAI GPT-4o-mini | Structured outputs |
| STT | OpenAI Whisper | Polish + multilingual |
| TTS | OpenAI gpt-4o-mini-tts | Streaming audio |
| Observability | LangFuse, Sentry | Traces, costs, errors |
| Rate Limiting | slowapi | Per-endpoint limits |

---

## Project Structure

```
life-story-agent/
├── app/                          # Python FastAPI backend
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                # Settings (from env vars)
│   ├── api/
│   │   ├── deps.py              # Auth dependency (Cognito JWT)
│   │   ├── routes/
│   │   │   ├── events.py       # Event CRUD, recordings, complete
│   │   │   ├── interview.py     # Analyze, follow-up, questions
│   │   │   ├── users.py         # User profile, relatives
│   │   │   └── evaluations.py  # Admin dashboard stats
│   │   ├── schemas/             # Pydantic models
│   │   └── utils.py            # Shared helpers (require_data, etc.)
│   ├── db/
│   │   ├── client.py           # asyncpg pool, Secrets Manager
│   │   └── query.py            # Supabase-compatible query builder
│   ├── services/
│   │   ├── storage.py          # S3 operations (boto3)
│   │   ├── evaluation.py       # LLM-as-judge scoring
│   │   ├── recording_orchestrator.py  # Upload → transcribe → persist
│   │   ├── event_completion.py       # Generate summary
│   │   └── ...
│   └── tests/                   # pytest tests
├── aws/
│   ├── Dockerfile              # Production Docker image
│   └── (Terraform files)      # Infrastructure as Code
├── .github/workflows/
│   ├── backend.yml           # Build & Deploy to ECS (manual trigger)
│   ├── frontend.yml         # Deploy to S3/CloudFront (manual)
│   └── terraform.yml         # Apply Terraform (manual)
└── supabase/migrations/
    └── 001_aurora_schema.sql # Aurora schema (auto-seeded on startup)
```

---

## Migration Status

### Completed: Supabase → AWS

| Component | Status | Notes |
|-----------|--------|-------|
| Database | ✅ Done | asyncpg + Aurora PostgreSQL |
| Storage | ✅ Done | boto3 S3 |
| Auth | ✅ Done | Cognito JWT |
| Auto-create user | ✅ Done | First login creates Aurora user record |
| Schema auto-seed | ✅ Done | Backend runs migrations on startup |
| DB Query Layer | ✅ Done | `db/query.py` with Supabase-compatible interface |

### In Progress: Route Refactor

All route files refactored from `supabase.table()` to `db.table()` pattern:
- `api/routes/users.py` ✅
- `api/routes/evaluations.py` ✅
- `api/routes/events.py` ✅
- `api/routes/interview.py` ✅
- `services/evaluation.py` ✅
- `services/recording_orchestrator.py` ✅
- `services/event_completion.py` ✅
- `api/utils.py` ✅

---

## How to Run

### Backend (local development)

```bash
cd app
uv venv                    # Create virtual environment
uv sync                    # Install dependencies
uv run uvicorn main:app --reload
```

### Required Environment Variables

```bash
# AWS / Cognito
COGNITO_REGION=eu-west-1
COGNITO_USER_POOL_ID=eu-west-1_xxxxx
COGNITO_CLIENT_ID=xxxxx
COGNITO_ISSUER=https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_xxxxx

# Aurora / Database
AURORA_ENDPOINT=life-story-agent-aurora.cluster-xxx.eu-west-1.rds.amazonaws.com
DB_CREDENTIALS_ARN=arn:aws:secretsmanager:eu-west-1:xxx:secret:life-story-agent/production/db-password-xxx
DB_NAME=life_story_agent

# S3 Audio Storage
AUDIO_BUCKET=life-story-agent-audio

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini

# Optional
LANGFUSE_PUBLIC_KEY=xxx
LANGFUSE_SECRET_KEY=xxx
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

---

## Testing

```bash
cd app && uv run pytest
```

Lint:
```bash
cd app && uv run ruff check .
```

---

## Deployment

### Backend Deploy (GitHub Actions)

1. Go to GitHub → Actions → "Deploy Backend" → "Run workflow"
2. Select `dev` branch
3. Workflow:
   - Builds Docker image
   - Pushes to ECR (`603047573807.dkr.ecr.eu-west-1.amazonaws.com/life-story-agent/fastapi`)
   - Forces new ECS deployment
   - Waits for stability
   - Runs health check

### ECS Service

- Cluster: `life-story-agent-cluster`
- Service: `life-story-agent-fastapi-service`
- Tasks run in VPC with access to Aurora, S3, Cognito

### Frontend Deploy

1. Go to GitHub → Actions → "Deploy Frontend" → "Run workflow"
2. Select `dev` branch

---

## Key Files

### `app/db/query.py` - Database Query Layer

Provides Supabase-compatible interface using asyncpg:

```python
db = await get_db()
result = db.table("users").select("*").eq("id", user_id).execute()
# result.data → list[dict]
# result.rows → list[asyncpg.Record]
```

Classes:
- `Database` - main entry point
- `QueryBuilder` - SELECT queries with filters
- `InsertBuilder` - INSERT queries
- `UpdateBuilder` - UPDATE queries
- `DeleteBuilder` - DELETE queries
- `QueryResult` - wraps asyncpg results with `.data` property

### `app/api/deps.py` - Authentication

- Cognito JWT validation via JWKS
- Auto-creates user in Aurora on first login
- Returns `CurrentUser` with `id: uuid.UUID` and `email: str`

### `app/services/storage.py` - S3 Storage

- `upload(key, data, content_type)` → public URL
- `download(key)` → bytes
- `remove(key)` → None
- `remove_many(keys)` → None

---

## Important Conventions

1. **Never commit to any branch unless specifically tasked** - Always confirm with user before any git operations
2. **No Supabase SDK** - All DB access via `db/query.py`, NOT `supabase` client
2. **UUID vs string** - Use `uuid.UUID` objects, not strings, for IDs where possible
3. **Async only** - All DB operations are async with `asyncpg`
4. **Environment variables** - All config via `config.py`, no hardcoding
5. **Client encryption** - Backend only stores encrypted content; never decrypts
6. **Schema auto-seed** - Backend runs migrations on startup if tables don't exist

---

## Rollback Strategy

ECR images are immutable. If deployment fails:

1. Identify last good commit SHA
2. Re-run "Deploy Backend" workflow with that SHA
3. Or manually push the good image tag and update ECS task

Image tags:
- `:dev` - latest dev branch build
- `:latest` - most recent build (any branch)
- `:5a8c4e1` - specific commit SHA

---

## Known Issues / Technical Debt

1. **mypy module resolution** - `api.schemas.evaluation` found twice under different module names (pre-existing)
2. **Tests deferred** - Test suite updates pending after full deployment verification
3. **No offline support** - PWA shell caches static assets only

---

## Contacts

- Owner: @wszymilo
- Repository: https://github.com/wszymilo/life-story-agent
