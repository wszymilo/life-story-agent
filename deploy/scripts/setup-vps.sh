#!/usr/bin/env bash
# One-time bootstrap for the production VPS.
# Run as root or with sudo on a fresh Debian/Ubuntu VPS.
# Some steps are interactive / require external actions — the script prints them.
#
# Prerequisites to have ready:
#   - GitHub repo access (to add a deploy key)
#   - Cloudflare dashboard access (origin cert + DNS + port override)
set -euo pipefail

APP_USER="${APP_USER:-lsa}"
APP_DIR="${APP_DIR:-/home/${APP_USER}/life-story-agent}"
GITHUB_REPO="${GITHUB_REPO:-wszymilo/life-story-agent}"

info() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
info "1/6  Installing Docker Engine + Compose plugin"
# ---------------------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  apt-get update
  apt-get install -y ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
else
  echo "docker already installed"
fi

# ---------------------------------------------------------------------------
info "2/6  Adding user '${APP_USER}' to the docker group"
# ---------------------------------------------------------------------------
if id "${APP_USER}" >/dev/null 2>&1; then
  usermod -aG docker "${APP_USER}"
  echo "Done. Log out/in as ${APP_USER} for the group to take effect (or run: su - ${APP_USER})"
else
  warn "User '${APP_USER}' does not exist — create it first or adjust APP_USER."
fi

# ---------------------------------------------------------------------------
info "3/6  Generating a GitHub deploy key for 'git pull'"
# ---------------------------------------------------------------------------
mkdir -p /home/${APP_USER}/.ssh
chmod 700 /home/${APP_USER}/.ssh
if [ ! -f /home/${APP_USER}/.ssh/github_deploy_key ]; then
  ssh-keygen -t ed25519 -N "" -f /home/${APP_USER}/.ssh/github_deploy_key
  cat >> /home/${APP_USER}/.ssh/config <<EOF

Host github.com
  HostName github.com
  User git
  IdentityFile /home/${APP_USER}/.ssh/github_deploy_key
  IdentitiesOnly yes
EOF
fi
chown -R ${APP_USER}:${APP_USER} /home/${APP_USER}/.ssh
chmod 600 /home/${APP_USER}/.ssh/github_deploy_key
echo "Public key to add as a READ-ONLY deploy key in GitHub:"
echo "  Repo: ${GITHUB_REPO} → Settings → Deploy keys → Add deploy key"
echo "  Key:"
cat /home/${APP_USER}/.ssh/github_deploy_key.pub

# ---------------------------------------------------------------------------
info "4/6  Cloning the repository"
# ---------------------------------------------------------------------------
if [ ! -d "${APP_DIR}/.git" ]; then
  read -r -p "Once the deploy key is added, press Enter to continue..."
  git clone "git@github.com:${GITHUB_REPO}.git" "${APP_DIR}"
else
  echo "repo already present at ${APP_DIR}"
fi

# ---------------------------------------------------------------------------
info "5/6  Creating .env from template"
# ---------------------------------------------------------------------------
if [ ! -f "${APP_DIR}/.env" ]; then
  cp "${APP_DIR}/deploy/backend/.env.example" "${APP_DIR}/.env"
  chown ${APP_USER}:${APP_USER} "${APP_DIR}/.env"
  warn "Edit ${APP_DIR}/.env now with real secrets:"
  echo "  DB_PASSWORD        (strong value)"
  echo "  OPENAI_API_KEY"
  echo "  FIREBASE_CREDENTIALS"
  echo "  FIREBASE_PROJECT_ID"
  echo "  ADMIN_EMAIL"
  echo "  CORS_ORIGINS=https://www.lifestoryagent.uk"
  echo "  ENVIRONMENT=production"
fi

# ---------------------------------------------------------------------------
info "6/6  Remaining manual steps (outside this script)"
# ---------------------------------------------------------------------------
cat <<EOF
A) CI deploy SSH access:
   1. On your laptop, generate a dedicated CI key:
        ssh-keygen -t ed25519 -N "" -f ci_deploy_key
   2. Append ci_deploy_key.pub to /home/${APP_USER}/.ssh/authorized_keys
   3. Store ci_deploy_key (private, no passphrase) as GitHub secret VPS_SSH_KEY.

B) GitHub Actions secrets (repo → Settings → Secrets → Actions):
   VPS_HOST=eve146.mikrus.xyz
   VPS_SSH_PORT=10146
   VPS_USER=${APP_USER}
   VPS_SSH_KEY=<content of ci_deploy_key>

C) Cloudflare (domain: xapi.lifestoryagent.uk):
   1. AAAA record → VPS IPv6, PROXIED (orange cloud)
   2. Destination port override → 20146
   3. SSL/TLS mode → Full
   4. SSL/TLS → Origin Server → Create Certificate
      Download cert+key to ${APP_DIR}/deploy/backend/certs/{fullchain.pem,privkey.pem}
      (this directory is gitignored)

D) Firewall: ensure inbound TCP 20146 is allowed (the only public ingress).

E) Test deploy manually:
   su - ${APP_USER}
   cd ${APP_DIR} && ./deploy/backend/deploy.sh
EOF
