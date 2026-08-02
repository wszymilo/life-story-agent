<p align="center">
  <img src="./public/splash.png" alt="Life Story Preservation Agent" width="480">
</p>

<h1 align="center">Life Story Preservation Agent</h1>

<p align="center">
  <strong>An AI oral historian that helps elderly users capture, organize, and preserve their life memories through natural voice interaction.</strong>
</p>

<p align="center">
  <a href="https://github.com/wszymilo/life-story-agent/actions/workflows/ci.yml">
    <img src="https://github.com/wszymilo/life-story-agent/workflows/CI/badge.svg" alt="CI">
  </a>
  <img src="https://img.shields.io/badge/python-3.12-blue.svg?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/node-20-green.svg?logo=node.js&logoColor=white" alt="Node 20">
  <img src="https://img.shields.io/badge/react-18-61DAFB.svg?logo=react&logoColor=white" alt="React 18">
  <img src="https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
</p>

---

## Table of Contents

- [What is this?](#what-is-this)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Screens](#screens)
- [Architecture Highlights](#architecture-highlights)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Deployment](#deployment)
- [Roadmap & Known Limitations](#roadmap--known-limitations)
- [Documentation](#documentation)
- [License](#license)

---

## What is this?

The **Life Story Preservation Agent** is a conversational AI system designed to support elderly individuals in gathering and preserving their life stories. The system acts as a patient, curious, and respectful oral historian who treats every life as worthy of documentation.

This project was built as a **bootcamp demo** with a deeply personal design driver: the primary user is an **80-year-old Polish-speaking mother** using an Android smartphone. Every design decision — from large touch targets and voice-first interaction to warm and empathetic AI responses - was made with her in mind.

Users speak their memories naturally. The system transcribes, asks intelligent follow-up questions, anchors stories to a chronological timeline, and ultimately produces shareable legacy documents that families can keep forever.

---

## Key Features

- **Voice-first recording** — One-tap audio capture via MediaRecorder API, transcribed by OpenAI Whisper with Polish language support
- **AI-powered follow-up questions** — GPT-4o-mini generates gentle, contextual questions to deepen stories (sensory details, emotions, people, places)
- **Text-to-speech for questions** — Follow-ups are spoken aloud via streaming TTS, so users never need to read small text
- **Timeline visualization** — All memories organized chronologically with time anchors extracted by AI
- **Generator-Reviewer pattern** — Two-step AI validation ensures summaries are strictly grounded in source transcripts, preventing hallucinations in family legacy documents
- **Client-side encryption** — All user content encrypted in the browser with AES-256-GCM before reaching the backend
- **Meta-story generation** — Combine multiple events into a single flowing narrative with source attribution
- **ZIP export** — Download complete stories as markdown + original audio/text sources, generated entirely in the browser
- **Magic link authentication** — No passwords to remember; Firebase Auth sends email magic links or supports Google sign-in
- **LLM observability** — LangFuse traces track every AI interaction with token usage, cost, and quality scores
- **LLM-as-judge evaluation** — Automated factual accuracy, coherence, and completeness scoring on a sample of generations

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | React, TypeScript, Vite, Tailwind CSS | React 18, Vite 6, TS 5.6, Tailwind 3.4 |
| **Backend** | Python, FastAPI, Pydantic, asyncpg | Python 3.12, FastAPI 0.115 |
| **Database** | PostgreSQL (self-hosted) | 15, via Docker + asyncpg |
| **Auth** | Firebase Auth | Magic links + Google OAuth, Firebase ID tokens |
| **Storage** | Local filesystem (Docker volume) | Audio stored under `/data/audio-recordings` |
| **LLM** | OpenAI GPT-4o-mini | Structured outputs, function calling |
| **STT** | OpenAI Whisper | Polish + multilingual |
| **TTS** | OpenAI gpt-4o-mini-tts | Streaming audio |
| **Observability** | LangFuse, Sentry | Traces, costs, scores |
| **Rate Limiting** | slowapi | Per-endpoint limits |
| **Testing** | pytest (backend), Vitest + RTL (frontend) | 141 backend tests |

---

## Screens

The PWA follows a linear user flow designed for minimal cognitive load:

1. **Login** — Email input, magic link sent via Firebase Auth (or Google sign-in)
2. **Onboarding** — Capture name, birth date, and country of origin
3. **Timeline** — Chronological view of all life events; tap to explore, tap + to add
4. **Recording** — Large record button, real-time audio visualization, automatic upload
5. **Interview** — AI asks follow-up questions via TTS; user records answers or skips
6. **Summary** — Review the AI-generated grounded summary; listen via TTS
7. **Event Detail** — View full event with transcripts, Q&A, and audio playback
8. **Dashboard** — Admin-only evaluation metrics and quality scores

---

## Architecture Highlights

### Progressive Web App (PWA)

Built as a PWA instead of a native app — no app store submission, single codebase, automatic updates. Works on any modern mobile browser with access to MediaRecorder API for audio capture.

### Client-Side Encryption

All user-generated text (titles, summaries, transcripts) is encrypted in the browser with AES-256-GCM via the Web Crypto API before transmission. The backend never sees plaintext user content. Meta-story generation uses a "Dance Flow" pattern: decrypt on client, send plaintext to backend for AI processing, receive result, encrypt, store.

### Generator-Reviewer Pattern

The most critical AI component. Instead of a single LLM call for summaries:

1. **Generator** creates a narrative from transcripts and Q&A
2. **Reviewer** validates every claim against source material using structured outputs (`response_format=GroundingValidation`)
3. **Retry loop** with feedback (max 2 retries) if hallucinations are detected
4. **Title + time anchor** extracted in separate validated calls

This ensures that a fabricated detail never makes it into a family legacy document.

### LangFuse Observability

Every user session is traced end-to-end: transcript analysis, follow-up generation, summary creation, TTS calls, and evaluation scoring. Token usage and estimated costs are attached to each trace. Question quality scores (relevance, specificity, open-endedness, diversity, expected richness) are logged for continuous improvement.

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.12+ with `uv` (for backend tests / dev)
- Node.js 20+ with npm
- OpenAI API key
- Firebase project (Web + service account credentials)

### 1. Clone & Configure

```bash
git clone https://github.com/wszymilo/life-story-agent.git
cd life-story-agent

# Create backend env file and fill in secrets
cp deploy/backend/.env.example .env
```

### 2. Start the Backend Stack (Docker)

```bash
./deploy/backend/up.local.sh
```

This starts **PostgreSQL 15** and the **FastAPI backend** as containers. The backend runs at `http://localhost:8000` with hot-reload (bind-mounted source, polling-based reloader). Health check: `http://localhost:8000/health`.

The database schema is applied automatically on the first run from `deploy/backend/init.sql`.

### 3. Frontend

In a new terminal (from project root):

```bash
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`. Vite auto-proxies `/api/*` to `http://localhost:8000`.

### 4. Running the backend without Docker (optional)

```bash
cd app
uv sync
uv run uvicorn main:app --reload
```

Requires a reachable PostgreSQL and a `DATABASE_URL` env var.

---

## Environment Variables

### Backend (`.env` in project root)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (asyncpg) |
| `DB_PASSWORD` | Yes (Docker) | PostgreSQL password used by docker-compose |
| `AUDIO_STORAGE_PATH` | No | Audio file directory (default: `/data/audio-recordings`) |
| `FIREBASE_CREDENTIALS` | Yes | Firebase service account JSON (escaped string) |
| `FIREBASE_PROJECT_ID` | Yes | Firebase project ID |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_MODEL` | No | LLM model (default: `gpt-4o-mini`) |
| `TTS_MODEL` | No | TTS model (default: `gpt-4o-mini-tts`) |
| `ENVIRONMENT` | No | `development` or `production` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `MAX_META_STORY_SELECT` | No | Max events for meta-story (default: `10`) |
| `ADMIN_EMAIL` | No | Email for admin dashboard access |
| `SENTRY_DSN` | No | Sentry error tracking DSN |
| `LANGFUSE_PUBLIC_KEY` | No | LangFuse public key for tracing |
| `LANGFUSE_SECRET_KEY` | No | LangFuse secret key for tracing |
| `LANGFUSE_BASE_URL` | No | LangFuse host (default: `https://cloud.langfuse.com`) |
| `EVAL_ENABLED` | No | Enable LLM-as-judge evaluation (`true`/`false`) |
| `EVAL_SAMPLE_RATE` | No | Fraction of sessions to evaluate (default: `0.1`) |

### Frontend (Vite — in `.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_FIREBASE_API_KEY` | Yes | Firebase API key |
| `VITE_FIREBASE_AUTH_DOMAIN` | Yes | Firebase auth domain |
| `VITE_FIREBASE_PROJECT_ID` | Yes | Firebase project ID |
| `VITE_FIREBASE_APP_ID` | Yes | Firebase app ID |
| `API_URL` | No | Backend URL used by `vercel.ts` routing (default: `http://localhost:8000`) |

---

## Testing

### Backend

```bash
cd app
uv run pytest
```

**141 tests** covering routes, services, AI pipelines, auth, rate limiting, LangFuse integration, and evaluation. Run before every commit.

### Frontend

```bash
npm run test:run        # Run once
npm run test            # Watch mode
```

Tests use Vitest + React Testing Library for components and hooks.

### Lint & Type Check

```bash
# Backend
cd app && uv run ruff check .
cd app && uv run mypy main.py --ignore-missing-imports --no-error-summary

# Frontend
npm run lint
npm run typecheck
```

---

## Deployment

There are two deployment paths:

### Local (Docker Compose, hot-reload)

```bash
./deploy/backend/up.local.sh
```

### Production (VPS + Cloudflare + Caddy)

- **Backend**: FastAPI in Docker on a VPS (`eve146.mikrus.xyz`, IPv6), served via **Caddy** on the public port `:20146`, TLS terminated with a Cloudflare Origin CA certificate. PostgreSQL and backend containers publish only to loopback.
- **Database**: self-hosted PostgreSQL 15 in Docker (persistent volume).
- **Storage**: local Docker volume (`/data/audio-recordings`).
- **Frontend**: React PWA on Vercel. `vercel.ts` routes `/api/*` to the `API_URL` environment variable (production: `https://xapi.lifestoryagent.uk`) and falls back to `index.html` for SPA routing.
- **CI/CD**: GitHub Actions runs unit tests (backend + frontend), then SSH-deploys to the VPS on pushes to `main` (`git pull` + `docker compose up -d --build`).

See [`docs/supabase-removal/production-deployment.md`](docs/supabase-removal/production-deployment.md) for the full production guide.

---

## Roadmap & Known Limitations

This is an MVP built as a bootcamp demo. Known gaps and planned improvements:

| Area | Current State | Future |
|------|--------------|--------|
| **Offline support** | PWA shell caches static assets; no offline recording | Background sync for recordings, offline transcript queue |
| **Push notifications** | Not implemented | Reminders to continue a story, weekly memory prompts |
| **Contextual enrichment** | User-provided context only | Wikipedia integration for historical facts matching event dates (world + Poland) |
| **Map integration** | Places stored but not visualized | Interactive map of life events |
| **Multi-language** | Polish + English (188 keys) | Full i18n with user language selection |
| **Accessibility** | Large text/buttons, voice-first | Screen reader optimization, high contrast mode |
| **Audio storage** | Local filesystem Docker volume | Compression, lifecycle policies, CDN delivery |
| **Evaluation** | 10% sample rate, async | Real-time quality gates, A/B testing for prompts |
| **Native app** | PWA only | Capacitor wrapper for app store distribution |

---

## Documentation

| Document | Purpose |
|----------|---------|
| [`docs/system-design.md`](./docs/system-design.md) | Full architecture: data flow, encryption, generator-reviewer pattern, Mermaid diagrams |
| [`docs/supabase-removal/local-and-production-setup.md`](./docs/supabase-removal/local-and-production-setup.md) | Local dev + production setup, environment strategy, deployment |
| [`docs/supabase-removal/production-deployment.md`](./docs/supabase-removal/production-deployment.md) | Production VPS deployment guide (Cloudflare, Caddy, CI/CD) |
| [`docs/supabase-removal/plan.md`](./docs/supabase-removal/plan.md) | Historical Supabase removal + migration plan |

---

## License

[MIT](./LICENSE)

---

<p align="center">
  Built with care for the stories that matter most.
</p>
