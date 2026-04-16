# Life Story Preservation Agent

An AI-assisted oral history app for capturing elderly users' life stories through voice interviews.

## Quick Start

### Prerequisites
- Python 3.12+ with `uv`
- Node.js 18+ with npm
- Docker (for local PostgreSQL)

### Local Development

**Backend:**
```bash
cd app
uv venv
uv sync
uv run uvicorn app.main:app --reload
```

**Frontend:**
```bash
npm install
npm run dev
```

**Local Postgres (optional):**
```bash
docker-compose up
```

## Tech Stack

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS
- **Backend**: Python 3.12, FastAPI, SQLAlchemy
- **Database**: PostgreSQL (via Supabase)
- **AI**: OpenAI (GPT-5-nano, Whisper, TTS)

## Project Structure

```
app/          - Backend (FastAPI)
src/          - Frontend (React)
supabase/     - Database migrations
docs/         - Design documentation
```