#!/usr/bin/env bash
# Start the local dev stack (postgres + backend with hot-reload).
# Usage: ./deploy/backend/up.local.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
docker compose -f deploy/backend/docker-compose.yml up -d
