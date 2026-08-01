# Local Development & Production Setup

> Date: 2026-07-29

> **Production path**: see [production-deployment.md](production-deployment.md) — VPS + Cloudflare + Caddy `:20146` + GitHub Actions deploy.

---

## Principles

1. **Single `vercel.json` for all environments** — Vercel's `routes` property supports `${VAR}` expansion from environment variables. The same `vercel.json` resolves `$API_URL` to the correct backend URL in local dev and production without manual changes.
2. **One `docker-compose.yml` for both local and production** — differences handled via `.env` overrides and a production-only `docker-compose.prod.yml`.
3. **`deploy/` directory groups deployment artifacts** — all backend deployment files (Dockerfile, compose files, Caddyfile) live under `deploy/backend/`. Root keeps only what must be there: `vercel.json` (Vercel requirement), `.env`, `.env.local`, and source directories.

---

## Directory Structure

```
/
├── vercel.json                      # Vercel config (must be at root)
├── .env                             # Backend env vars (gitignored)
├── .env.local                       # Frontend env vars for vercel dev (gitignored)
├── app/                             # Backend Python code
├── src/                             # Frontend React code
├── supabase/migrations/             # DB init SQL
└── deploy/
    ├── backend/
    │   ├── docker-compose.yml       # Main compose (local dev)
    │   ├── docker-compose.prod.yml  # Production overrides (Caddy)
    │   ├── Dockerfile               # Backend container build
    │   ├── Caddyfile                # Production reverse proxy config
    │   ├── .env.example             # Backend env vars template
    │   └── init-test-data.sql       # Optional seed data
    ├── frontend/
    │   └── .env.local.example       # Frontend env vars template
    └── scripts/
        ├── migrate-db.sh            # Supabase → local PG dump/restore
        └── migrate-storage.py       # Supabase → local FS audio transfer
```

---

## Architecture

```
          Local Machine                                    Docker (local)
  ┌─────────────────────────┐          ┌─────────────────────────────┐
  │  vercel dev (port 3000) │──/api/*──▶  backend (port 8000)       │
  │  - serves static files  │  ────────▶  postgres (port 5432)      │
  │  - applies vercel.json  │  HTTP     └─────────────────────────────┘
  │    routes ──────────────┘
  └─────────────────────────┘
```

No Caddy locally — `vercel dev` proxies directly to the backend container on port 8000. Caddy runs only on the VPS in production, terminating TLS for `api.lifestoryagent.uk`.

---

## Key File: `vercel.json` (environment-aware via `routes` + `env`)

Vercel's `routes` property (not `rewrites`) supports environment variable expansion in destinations. The `env` array whitelists which variables can be expanded at request time:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "routes": [
    {
      "src": "^/api/(.*)",
      "dest": "$API_URL/$1",
      "env": ["API_URL"]
    },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

How `$API_URL` is resolved:

| Environment | Source of `API_URL` | Value |
|-------------|---------------------|-------|
| `vercel dev` (local) | `.env.local` file | `http://localhost:8000` |
| Vercel Production deploy | Dashboard → Environment Variables → Production | `https://api.lifestoryagent.uk` |
| Vercel Preview deploy | Dashboard → Environment Variables → Preview | `https://preview-api.lifestoryagent.uk` |

**One `vercel.json`, no manual switching.** Vercel injects the correct `$API_URL` based on where the code runs.

---

## Files

### `/deploy/backend/docker-compose.yml` (committed to git)

```yaml
services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ../../supabase/migrations:/docker-entrypoint-initdb.d
      - ./init-test-data.sql:/docker-entrypoint-initdb.d/999-init-test-data.sql
    environment:
      POSTGRES_DB: life_story_agent
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  backend:
    build:
      context: ../..
      dockerfile: deploy/backend/Dockerfile
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - audio-data:/data/audio-recordings
      - ../../app:/app
    depends_on:
      postgres:
        condition: service_started
    env_file: ../../.env
    environment:
      DATABASE_URL: postgresql+asyncpg://app:${DB_PASSWORD}@postgres:5432/life_story_agent
      AUDIO_STORAGE_PATH: /data/audio-recordings
      CORS_ORIGINS: http://localhost:3000,http://localhost:5173

volumes:
  pgdata:
  audio-data:
```

Key design notes:
- **All paths relative to `deploy/backend/`**: repo root = `../..`, migrations = `../../supabase/migrations/`, build context = `../..`, app code = `../../app`.
- **Hot reload**: `../../app:/app` bind-mount enables live code changes (uvicorn picks them up with `--reload`). In production this volume is removed.
- **Init SQL**: Migration files auto-run from `../../supabase/migrations/`. Optional seed data at `init-test-data.sql`.
- **CORS**: Allows both `localhost:3000` (Vercel dev default) and `localhost:5173` (Vite default).

### `/deploy/backend/docker-compose.prod.yml` (committed to git)

```yaml
services:
  backend:
    build:
      context: ../..
      dockerfile: deploy/backend/Dockerfile
    volumes:
      - ../../app:/app        # REMOVED in production — code baked into image
    command: uvicorn main:app --host 0.0.0.0 --port 8000

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

volumes:
  caddy_data:
  caddy_config:
```

Combined:

```bash
docker compose -f deploy/backend/docker-compose.yml -f deploy/backend/docker-compose.prod.yml up -d
```

### `/deploy/backend/Dockerfile` (committed to git)

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY app/pyproject.toml app/uv.lock ./
RUN pip install uv && uv sync --frozen --no-install-project

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY app/ .
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `/deploy/backend/Caddyfile` (production only, committed to git)

```caddyfile
api.lifestoryagent.uk {
    reverse_proxy backend:8000
}
```

### `/deploy/backend/.env.example` (committed to git)

```bash
# ── Database ───────────────────────────────────────
DB_PASSWORD=change-me

# ── AI ──────────────────────────────────────────────
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
TTS_MODEL=gpt-4o-mini-tts

# ── Auth (Firebase) ────────────────────────────────
FIREBASE_CREDENTIALS={"type":"service_account",...}
FIREBASE_PROJECT_ID=your-firebase-project

# ── CORS ───────────────────────────────────────────
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ── Observability ──────────────────────────────────
SENTRY_DSN=https://...
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com

# ── Application ────────────────────────────────────
ENVIRONMENT=development
LOG_LEVEL=info
ADMIN_EMAIL=your@email.com
EVAL_ENABLED=false
EVAL_SAMPLE_RATE=0.1
MAX_META_STORY_SELECT=10
```

Copy to `/.env` and fill in secrets (gitignored).

### `/deploy/frontend/.env.local.example` (committed to git)

```bash
# Copy to /.env.local — auto-loaded by vercel dev
# Production equivalents go in Vercel Dashboard → Environment Variables

VITE_FIREBASE_API_KEY=xxx
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-firebase-project
VITE_FIREBASE_APP_ID=xxx

# Used by vercel.json routes — points to local Docker backend
API_URL=http://localhost:8000
```

### `/deploy/backend/init-test-data.sql` (optional, NOT committed)

```sql
-- Seed data for manual testing. Mounted only when present.
-- Creates a test user:
INSERT INTO users (id, email, name, preferred_language)
VALUES ('test-user-id', 'test@example.com', 'Test User', 'en')
ON CONFLICT (id) DO NOTHING;
```

---

## Environment Variable Strategy

| Variable set | Scope | How it's supplied |
|-------------|-------|-------------------|
| `DB_PASSWORD`, `OPENAI_API_KEY`, etc. | Backend (Docker) | `/.env` → `env_file: .env` |
| `API_URL` | Vercel routing | Local: `/.env.local` → `vercel dev` picks up; Production: Vercel Dashboard → Environment Variables |
| `VITE_FIREBASE_*` | Frontend app | Local: `/.env.local`; Production: Vercel Dashboard |
| `CORS_ORIGINS` | Backend CORS | `/.env` — local origins in dev; `https://www.lifestoryagent.uk` in prod |

---

## Usage

### First-time setup

```bash
# 1. Copy env templates and fill secrets
cp deploy/backend/.env.example .env
cp deploy/frontend/.env.local.example .env.local
# Edit .env and .env.local with your secrets

# 2. Start Docker backend
docker compose -f deploy/backend/docker-compose.yml build
docker compose -f deploy/backend/docker-compose.yml up -d

# 3. Verify backend
curl http://localhost:8000/health/ready

# 4. Start frontend via Vercel CLI
npx vercel dev
# → http://localhost:3000
```

### Daily workflow

```bash
docker compose -f deploy/backend/docker-compose.yml up -d   # start backend + DB
npx vercel dev                                                # start frontend
docker compose -f deploy/backend/docker-compose.yml logs -f backend
docker compose -f deploy/backend/docker-compose.yml restart backend
docker compose -f deploy/backend/docker-compose.yml down
```

### Production deploy (VPS)

```bash
docker compose -f deploy/backend/docker-compose.yml -f deploy/backend/docker-compose.prod.yml up -d --build
```

---

## Vercel Dashboard Configuration

### Environment Variables

Set these in **Vercel Dashboard → Project → Settings → Environment Variables**:

| Name | Production value | Preview/Dev value |
|------|-----------------|-------------------|
| `API_URL` | `https://api.lifestoryagent.uk` | `http://localhost:8000` |
| `VITE_FIREBASE_API_KEY` | (production key) | (dev key) |
| `VITE_FIREBASE_AUTH_DOMAIN` | `lifestoryagent.uk` | (dev domain) |
| `VITE_FIREBASE_PROJECT_ID` | (production project) | (dev project) |
| `VITE_FIREBASE_APP_ID` | (production app) | (dev app) |

---

## Key Design Decisions

### `routes` + `env` over `rewrites`

`rewrites` does not support environment variable expansion. `routes` does, via the `env` property. This is the only way to have a single `vercel.json` work across local dev and production without manual edits or separate config files.

### Why `vercel dev` over `npm run dev`

`vercel dev` applies `vercel.json` routing locally, including the `routes` + `env` resolution. `npm run dev` (Vite) doesn't — you'd need a separate Vite proxy config. `vercel dev` gives a production-identical frontend environment.

### Why no Caddy locally

Caddy's primary job is TLS termination for `api.lifestoryagent.uk`, which requires a real domain and DNS. Locally, `vercel dev` proxying directly to `localhost:8000` over HTTP is simpler and sufficient. Caddy appears only in `docker-compose.prod.yml`.

### Hot reload for backend

`../../app:/app` bind-mount enables live code changes (uvicorn picks them up with `--reload`). In production this volume is removed — the Dockerfile copies the code instead.

### Why `deploy/` directory

Groups all deployment artifacts in one place. The root keeps only the files that must be there: `vercel.json` (Vercel requires it at root), plus `.env`, `.env.local`, and source directories. Docker Compose commands use `-f deploy/backend/docker-compose.yml`.

---

## Gitignore Updates

```gitignore
# Local env files
.env
.env.local

# Docker volumes (if any local data)
pgdata/
audio-data/

# Test seed data (not committed)
deploy/backend/init-test-data.sql
```
