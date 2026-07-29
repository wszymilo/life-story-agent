#!/usr/bin/env bash
# Deploy to production VPS (run on the VPS, either manually or via GitHub Actions).
# Pulls latest code (bind-mounted into containers) and rebuilds when deps change.
# Usage: ./deploy/backend/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
git pull
docker compose -f deploy/backend/docker-compose.yml \
               -f deploy/backend/docker-compose.prod.yml \
               up -d --build
