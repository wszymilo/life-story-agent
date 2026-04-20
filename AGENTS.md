# Life Story Preservation Agent - Agent Instructions

## Project Context
- **Primary user**: 80-year-old mother, Polish-speaking only, mobile-first (Android PWA)
- **10-day timeline**, solo developer
- **Language**: Polish (MVP), English (bootcamp demo)

## Key User Experience Requirements
- Large text (min 18px), large buttons (min 48x48px touch targets)
- Voice-primary interaction with obvious record button
- Handle "I don't remember/know" gracefully
- Max 2-3 taps to any function
- Warm, patient, empathetic responses (Catholic user - sensitive to faith topics)

## Tech Stack
- **Frontend**: React 18 PWA, Tailwind CSS + shadcn/ui, TanStack Query, MediaRecorder API
- **Backend**: Python 3.12, FastAPI, OpenAI Agents SDK, Supabase (PostgreSQL + Auth)
- **AI**: OpenAI GPT-5-nano (LLM), Whisper (STT), TTS

## Domain Concepts
- **Event**: Single memory/story on timeline (recording + transcript + Q&A + summary)
- **Session**: Transient process creating one Event (not persisted)
- **Timeline**: Chronological view of Events sorted by time_anchor_date
- **Follow-up Q**: AI-generated questions to deepen story (sensory, emotions, people, context)
- **Publishing**: Generate narrative from selected Events → markdown + sources zip

## Important Constraints
- Generator-Reviewer pattern for grounded summaries (no hallucination)
- All API routes require auth except `/auth/*`
- PWA must work on Android Chrome
- Audio format: webm via MediaRecorder API

## Dev Commands
- Backend: `cd app && uv run uvicorn main:app --reload`
- Frontend: `npm run dev` (Vite)
- Backend tests: `cd app && uv run pytest`
- Frontend tests: `npm test` (vitest) or `npm run test:run`
- Lint/Typecheck: Run per-stack (check package.json / pyproject.toml)

## Running Locally for Manual Testing

### Start Backend (Terminal 1)
```bash
cd app && uv run uvicorn main:app --reload
```
- Runs on: http://localhost:8000
- Health check: http://localhost:8000/health

### Start Frontend (Terminal 2)
```bash
npm run dev
```
- Runs on: http://localhost:5173
- Auto-proxies `/api/*` → http://localhost:8000

### Testing Flow
1. Open http://localhost:5173
2. Enter email on login screen → "Send Magic Link"
3. Check email for magic link → click it
4. Redirects to Timeline (protected route)

## Testing Requirements
- ALL new features must include tests
- Backend: pytest for API routes and services
- Frontend: Vitest + React Testing Library for components/hooks
- Run tests before committing

## Git Operations - IMPORTANT
- **DO NOT automatically commit and push changes**
- Always ask the user before committing: "Ready to commit - shall I proceed?"
- Wait for explicit confirmation before running git push
- Exception: Only if user explicitly asks to commit/push

## Important Notes
- Python imports require running from app/ directory (e.g., `cd app && uv run uvicorn main:app`)
- The project uses Supabase for PostgreSQL + Auth + Storage
- Use local `.env` for credentials (never commit to git)

## Critical Files
- `app/` - FastAPI backend (routes, services, models)
- `src/` - React frontend (screens, components, hooks)
- `supabase/` - migrations/schema

## What Makes This Project Unique
1. Target user is elderly - accessibility drives UI decisions
2. Polish language first-class support
3. Generator-Reviewer pattern for factual grounding
4. Contextual enrichment: Wikipedia historical facts for event timeframe (world + Poland)

## Design Documentation
- `docs/project-context1.md` - Source of truth for requirements, MVP scope, and demo script
- `docs/docs-from-other-agents/architecture.md` - Technical patterns (adapt, don't follow verbatim)

When implementing:
- Use `app/`/`src/` directory structure per this file (not `backend/`/`frontend/`)
- Use GPT-5-nano as LLM (not gpt-4o-mini from architecture.md)
- Reference architecture.md for service patterns and API contracts, but adapt to your decisions

## Coding Conventions
- Use DRY, KISS and SOLID principles while coding.
- Make sure the code is tested
- If unsure - **ASK**
- Beautiful is better than ugly.
- Explicit is better than implicit.
- Simple is better than complex.
- Complex is better than complicated.
- Flat is better than nested.
- Sparse is better than dense.
- Readability counts.
- Special cases aren't special enough to break the rules.
- Although practicality beats purity.
- In the face of ambiguity, refuse the temptation to guess.
- If the implementation is hard to explain, it's a bad idea.
- If the implementation is easy to explain, it may be a good idea.
