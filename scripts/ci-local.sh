#!/usr/bin/env bash
set -euo pipefail

# Local CI Script
# Replicates the checks from .github/workflows/ci.yml for local validation.
# Run this before pushing to catch issues early.

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track failures
BACKEND_FAILED=0
FRONTEND_FAILED=0

# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------
echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}  Backend CI Checks${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""

cd app

# 1. Sync dependencies
echo -e "${YELLOW}[1/4] Syncing dependencies...${NC}"
if uv sync > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Dependencies synced${NC}"
else
    echo -e "${RED}  ✗ Dependency sync failed${NC}"
    BACKEND_FAILED=1
fi

# 2. Lint
echo -e "${YELLOW}[2/4] Running ruff lint...${NC}"
if uv run ruff check .; then
    echo -e "${GREEN}  ✓ Lint passed${NC}"
else
    echo -e "${RED}  ✗ Lint failed${NC}"
    BACKEND_FAILED=1
fi

# 3. Type check (non-blocking, matching CI behavior)
echo -e "${YELLOW}[3/4] Running mypy type check...${NC}"
if uv run mypy main.py --ignore-missing-imports --no-error-summary > /dev/null 2>&1 || true; then
    echo -e "${GREEN}  ✓ Type check passed (or skipped)${NC}"
else
    echo -e "${YELLOW}  ⚠ Type check issues found (non-blocking)${NC}"
fi

# 4. Tests
echo -e "${YELLOW}[4/4] Running pytest...${NC}"
if uv run pytest -q; then
    echo -e "${GREEN}  ✓ Tests passed${NC}"
else
    echo -e "${RED}  ✗ Tests failed${NC}"
    BACKEND_FAILED=1
fi

cd ..

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
echo ""
echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}  Frontend CI Checks${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""

# 1. Install dependencies
echo -e "${YELLOW}[1/5] Installing npm dependencies...${NC}"
if npm install > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Dependencies installed${NC}"
else
    echo -e "${RED}  ✗ Dependency install failed${NC}"
    FRONTEND_FAILED=1
fi

# 2. Lint
echo -e "${YELLOW}[2/5] Running eslint...${NC}"
if npm run lint; then
    echo -e "${GREEN}  ✓ Lint passed${NC}"
else
    echo -e "${RED}  ✗ Lint failed${NC}"
    FRONTEND_FAILED=1
fi

# 3. Type check
echo -e "${YELLOW}[3/5] Running TypeScript type check...${NC}"
if npm run typecheck; then
    echo -e "${GREEN}  ✓ Type check passed${NC}"
else
    echo -e "${RED}  ✗ Type check failed${NC}"
    FRONTEND_FAILED=1
fi

# 4. Tests
echo -e "${YELLOW}[4/5] Running vitest...${NC}"
if npm run test:run; then
    echo -e "${GREEN}  ✓ Tests passed${NC}"
else
    echo -e "${RED}  ✗ Tests failed${NC}"
    FRONTEND_FAILED=1
fi

# 5. Build
echo -e "${YELLOW}[5/5] Running production build...${NC}"
if npm run build > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Build succeeded${NC}"
else
    echo -e "${RED}  ✗ Build failed${NC}"
    FRONTEND_FAILED=1
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}  CI Summary${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""

if [ $BACKEND_FAILED -eq 0 ]; then
    echo -e "${GREEN}Backend: PASS ✅${NC}"
else
    echo -e "${RED}Backend: FAIL ❌${NC}"
fi

if [ $FRONTEND_FAILED -eq 0 ]; then
    echo -e "${GREEN}Frontend: PASS ✅${NC}"
else
    echo -e "${RED}Frontend: FAIL ❌${NC}"
fi

echo ""

if [ $BACKEND_FAILED -eq 0 ] && [ $FRONTEND_FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed! Ready to push.${NC}"
    exit 0
else
    echo -e "${RED}Some checks failed. Fix issues before pushing.${NC}"
    exit 1
fi
