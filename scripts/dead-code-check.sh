#!/usr/bin/env bash
set -euo pipefail

# Dead Code Detection Script
# Run locally to find unused code, exports, and dependencies

echo "=================================="
echo "  Dead Code Detection"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ---------------------------------------------------------------------------
# Backend (Python)
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Backend${NC}"
echo "--------"

cd app

# 1. Unused imports (ruff F401, F811)
echo ""
echo "1. Unused imports (ruff)..."
uv run ruff check --select F401,F811 . 2>/dev/null || true

# 2. Dead code via vulture
echo ""
echo "2. Potentially dead code (vulture)..."
if command -v uv &> /dev/null && uv run vulture --version &> /dev/null; then
    uv run vulture . \
        --exclude "tests/,test_*,*_test.py,conftest.py,alembic/,migrations/,\.venv/" \
        --min-confidence 70 \
        2>/dev/null | grep -v "\.venv/lib" | grep -v "site-packages" || true
else
    echo "   vulture not installed. Install with: uv add --dev vulture"
fi

cd ..

# ---------------------------------------------------------------------------
# Frontend (TypeScript)
# ---------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}Frontend${NC}"
echo "---------"

# 3. Unused exports (ts-prune)
echo ""
echo "3. Potentially unused exports (ts-prune)..."
if npx ts-prune --version &> /dev/null; then
    npx ts-prune -p tsconfig.json 2>/dev/null || true
else
    echo "   ts-prune not installed. Install with: npm install -D ts-prune"
fi

# 4. ESLint unused vars
echo ""
echo "4. Unused variables (eslint)..."
npm run lint 2>/dev/null || true

# 5. Unused dependencies (depcheck)
echo ""
echo "5. Potentially unused dependencies (depcheck)..."
if npx depcheck --version &> /dev/null; then
    npx depcheck --ignores="@types/*,vitest,jsdom,autoprefixer,postcss,tailwindcss,globals,typescript-eslint" 2>/dev/null || true
else
    echo "   depcheck not installed. Install with: npm install -D depcheck"
fi

echo ""
echo "=================================="
echo -e "${GREEN}Done.${NC} Review findings above."
echo "Note: Tools may report false positives."
echo "      Always verify before removing code."
echo "=================================="
