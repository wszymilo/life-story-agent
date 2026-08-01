# Production Deployment Guide

> Date: 2026-07-30
> Companion to `local-and-production-setup.md` — this covers the VPS production path only.

---

## 1. Architecture

```
User browser
    │  HTTPS
    ▼
Cloudflare  (xapi.lifestoryagent.uk, proxied / orange cloud, SSL mode Full)
    │  HTTPS → [VPS IPv6]:20146
    ▼
Caddy (host networking, listens :20146)
    │  reverse_proxy localhost:8000
    ▼
backend (uvicorn, no reload, loopback :8000)
    │
    ▼
postgres (compose network only — no host port)
```

- **Public ingress**: the single port **20146** on the VPS IPv6.
- **Caddy** uses `network_mode: host` so it binds `:20146` directly on the host network stack (most reliable for IPv6-only hosts; no Docker IPv6 port-proxy in the path).
- **backend** publishes only to `127.0.0.1:8000` — never publicly reachable; **postgres** publishes **no host port** in production (reached only via the compose network using the `postgres` service name). Admin access: `docker compose exec postgres psql -U app life_story_agent`.
- **Ports are defined in the environment override files, not the base compose** — Docker Compose v2 *appends* `ports` across override files, so defining them in both the base and an override would duplicate the bind and fail with "address already in use". Local ports live in `docker-compose.local.yml`; prod ports in `docker-compose.prod.yml`.
- **Code sync**: `git pull` on the VPS updates the bind-mounted `app/` (no image rebuild needed for code changes). Rebuilds happen only when dependencies change (`--build`).

---

## 2. VPS Details

| Property | Value |
|----------|-------|
| Host | `eve146.mikrus.xyz` |
| SSH port | `10146` |
| Service (public) port | `20146` |
| User | `lsa` |
| App path | `/home/lsa/life-story-agent` |
| Network | IPv6 (AAAA record) |

---

## 3. One-Time VPS Bootstrap

Run the semi-automated script as root/sudo:

```bash
sudo APP_USER=lsa GITHUB_REPO=your-org/life-story-agent \
  bash deploy/scripts/setup-vps.sh
```

The script installs Docker + Compose, adds `lsa` to the `docker` group, generates a GitHub deploy key for `git pull`, clones the repo, and prints the remaining manual steps.

### Manual steps after the script

1. **`.env`** — fill `/home/lsa/life-story-agent/.env` with production secrets:
   - `DB_PASSWORD` (strong value), `OPENAI_API_KEY`, `FIREBASE_CREDENTIALS`, `FIREBASE_PROJECT_ID`, `ADMIN_EMAIL`
   - `CORS_ORIGINS=https://www.lifestoryagent.uk`
   - `ENVIRONMENT=production`
   (These two are also forced in `docker-compose.prod.yml` as a guard.)

2. **GitHub deploy key** — add the generated `~/.ssh/github_deploy_key.pub` as a **read-only deploy key** on the repo (Settings → Deploy keys). This lets `git pull` work on the VPS.

3. **CI deploy SSH key** — on your laptop, generate a dedicated key with no passphrase:
   ```bash
   ssh-keygen -t ed25519 -N "" -f ci_deploy_key
   ```
   Append `ci_deploy_key.pub` to `/home/lsa/.ssh/authorized_keys` on the VPS. Store the private key (`ci_deploy_key`) as the `VPS_SSH_KEY` GitHub secret.

4. **Cloudflare** — see §4.

5. **Firewall** — ensure inbound TCP **20146** is allowed.

---

## 4. Cloudflare Configuration

| Setting | Value |
|---------|-------|
| AAAA record `xapi.lifestoryagent.uk` | → VPS IPv6, **proxied** (orange cloud) |
| Origin destination port | **20146** (via Origin Rules / destination port override) |
| SSL/TLS mode | **Full** |
| Origin cert | SSL/TLS → Origin Server → Create Certificate |

**Origin CA certificate** (one-time):
- Dashboard → **SSL/TLS → Origin Server → Create Certificate**
- Hostnames: `xapi.lifestoryagent.uk` (or `*.lifestoryagent.uk`)
- Validity: 15 years
- Download and place on the VPS:
  ```
  Origin_Certificate.pem → /home/lsa/life-story-agent/deploy/backend/certs/fullchain.pem
  Origin_Key.pem         → /home/lsa/life-story-agent/deploy/backend/certs/privkey.pem
  ```
- The `certs/` directory is gitignored — never commit these.

---

## 5. TLS Notes

Caddy terminates TLS on the origin using the Cloudflare Origin CA certificate:

```caddyfile
xapi.lifestoryagent.uk:20146 {
    tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem
    reverse_proxy localhost:8000
}
```

- The `tls` directive with explicit files disables Caddy auto-HTTPS (which would otherwise try Let's Encrypt HTTP-01 on port 80 — not reachable here).
- Cloudflare "Full" mode accepts the Origin CA cert; it is also valid under "Full (strict)" if you upgrade later.
- Caddy is host-networked, so it proxies to `localhost:8000` (the backend's loopback publish) instead of the Docker DNS name.

---

## 6. Continuous Delivery (GitHub Actions)

`.github/workflows/ci.yml`:

```
backend (unit: uv sync → ruff → mypy → pytest)
        │
frontend (unit: npm ci → lint → typecheck → test:run → build)
        │
        ▼  (only on push to main, after both pass)
deploy → SSH → VPS → git pull + docker compose ... up -d --build
```

Deploy job uses `appleboy/ssh-action` with the following **GitHub secrets**:

| Secret | Value |
|--------|-------|
| `VPS_HOST` | `eve146.mikrus.xyz` |
| `VPS_SSH_PORT` | `10146` |
| `VPS_USER` | `lsa` |
| `VPS_SSH_KEY` | private key matching a public key in `lsa`'s `authorized_keys` (dedicated CI key, **no passphrase**) |

Manual deploy from the VPS:

```bash
cd /home/lsa/life-story-agent
./deploy/backend/deploy.sh
```

---

## 7. Relevant Files

| File | Purpose |
|------|---------|
| `deploy/backend/docker-compose.yml` | Base stack (shared local + prod) |
| `deploy/backend/docker-compose.prod.yml` | Prod overrides: loopback binds, host-net Caddy, no reload, prod env |
| `deploy/backend/Caddyfile` | `:20146` + origin cert + proxy to `localhost:8000` |
| `deploy/backend/Dockerfile` | Backend image (PATH + PYTHONPATH set for prod command) |
| `deploy/backend/deploy.sh` | VPS deploy: git pull + compose up --build |
| `deploy/backend/up.local.sh` | Local dev: compose up (hot-reload) |
| `deploy/scripts/setup-vps.sh` | One-time VPS bootstrap |
| `.github/workflows/ci.yml` | CI (unit+unit) + SSH deploy |
| `vercel.json` | Frontend routing via `$API_URL` (prod value: `https://xapi.lifestoryagent.uk`) |
