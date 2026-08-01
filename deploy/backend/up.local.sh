#!/usr/bin/env bash
# Start the local dev stack (postgres + backend with hot-reload).
# Usage: ./deploy/backend/up.local.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ ! -f .env ]; then
  echo "Missing .env — create it first:"
  echo "  cp deploy/backend/.env.example .env"
  echo "  # then fill in real secrets"
  exit 1
fi

docker compose --env-file .env \
  -f deploy/backend/docker-compose.yml \
  -f deploy/backend/docker-compose.local.yml up -d
