# Backend AWS Migration Plan

## Objective

Replace Supabase backend services (database, storage, authentication) with AWS equivalents (Aurora PostgreSQL, S3, Cognito) in the FastAPI application.

## Migration Scope

| Component | Current (Supabase) | Target (AWS) |
|-----------|-------------------|--------------|
| Database | Supabase SDK + PostgreSQL | asyncpg + Aurora PostgreSQL |
| File Storage | Supabase Storage SDK | boto3 + S3 |
| Authentication | Supabase JWT validation | Cognito JWT validation |
| User Creation | Supabase auto-creates on confirm | Auto-create on first login via API |

---

## Phase 1: Core Infrastructure ✅ COMPLETE

| File | Status | Notes |
|------|---------|-------|
| `app/config.py` | ✅ | AWS/Cognito environment variables |
| `app/db/client.py` | ✅ | asyncpg pool, boto3 Secrets Manager |
| `app/api/deps.py` | ✅ | Cognito JWT validation, auto-create user |
| `app/services/storage.py` | ✅ | boto3 S3 instead of Supabase Storage |
| `app/main.py` | ✅ | Health checks use new DB pool |
| `app/pyproject.toml` | ✅ | Added asyncpg, boto3 |
| `aws/Dockerfile` | ✅ | Fixed CMD to use `uv run uvicorn` (uvicorn shebang issue fixed) |

---

## Phase 2: Full Supabase → asyncpg Refactor ✅ COMPLETE

### Approach: Supabase-Compatible Query Builder Wrapper

Create a lightweight wrapper (`db/query.py`) that provides the same `.table().select().eq().execute()` interface but translates to asyncpg SQL under the hood.

### Files Modified (Phase 2)

| File | Status |
|------|--------|
| `db/query.py` | Created |
| `api/routes/users.py` | Refactored |
| `api/routes/evaluations.py` | Refactored |
| `api/routes/events.py` | Refactored |
| `api/routes/interview.py` | Refactored |
| `api/utils.py` | Refactored |
| `services/evaluation.py` | Refactored |
| `services/recording_orchestrator.py` | Refactored |
| `services/event_completion.py` | Refactored |
| `api/deps.py` | Fixed `from __future__ import annotations` for forward refs |

### Verification

- [x] Backend imports successfully
- [x] All API routes registered correctly
- [ ] End-to-end with Aurora (requires deployment)

```python
# New db/query.py
class Database:
    def table(self, name: str) -> QueryBuilder:
        return QueryBuilder(name, self.pool)

class QueryBuilder:
    def select(self, columns: str = "*") -> QueryBuilder: ...
    def eq(self, column: str, value: Any) -> QueryBuilder: ...
    def insert(self, data: dict) -> InsertBuilder: ...
    def update(self, data: dict) -> UpdateBuilder: ...
    def delete(self) -> DeleteBuilder: ...
    async def execute(self) -> QueryResult: ...

# Usage: db.table("users").select("*").eq("id", "123").execute()
```

### Key Differences from Supabase SDK

| Supabase | asyncpg via QueryBuilder |
|----------|--------------------------|
| `supabase.table("x").select("*")` | `db.table("x").select("*")` |
| `supabase.table("x").insert(data).execute()` | `db.table("x").insert(data).execute()` |
| `result.data` | `result.rows` |
| `result.count` | `len(result.rows)` |
| `require_data()` helper | Direct exception raise |

### Files to Modify (Phase 2)

| File | Supabase Calls | Estimated Time |
|------|-----------------|-----------------|
| `db/query.py` | NEW | 2-3 hours |
| `api/routes/users.py` | ~10 | 1 hour |
| `api/routes/evaluations.py` | ~5 | 1 hour |
| `api/routes/events.py` | ~30 | 2-3 hours |
| `api/routes/interview.py` | ~15 | 1-2 hours |
| `api/utils.py` | ~5 | 1 hour |
| `services/evaluation.py` | ~5 | 1 hour |
| `services/recording_orchestrator.py` | ~10 | 1 hour |
| `services/event_completion.py` | ~10 | 1 hour |
| `tests/conftest.py` | SKIP | Will update later |
| **Total** | **~90 calls** | **12-15 hours** |

### Implementation Order

1. Create `db/query.py` - Supabase-compatible query builder
2. `api/routes/users.py` - Smallest, simplest
3. `api/routes/evaluations.py` - Small
4. `api/routes/events.py` - Largest
5. `api/routes/interview.py` - Medium
6. `services/evaluation.py`
7. `services/recording_orchestrator.py`
8. `services/event_completion.py`
9. `api/utils.py`

### Sample Transformation

```python
# OLD (Supabase)
supabase.table("users").select("*").eq("id", str(user_id)).execute()
# Result: result.data[0]

# NEW (asyncpg via QueryBuilder)
db.table("users").select("*").eq("id", user_id).execute()
# Result: result.rows[0]
```

---

## Phase 3: Testing ✅ COMPLETE

| Item | Status |
|------|--------|
| Update `tests/conftest.py` | ✅ (async decorator added to test class) |
| Update `tests/test_helpers.py` | ✅ (4 tests fixed: async + await) |
| Run pytest | ✅ (139 passed, 4 skipped) |

### Verification Checklist (Post-Phase 3 - Testing)

- [x] All pytest tests pass ✅ (139 passed, 4 skipped)
- [x] Unit tests for db/query.py ✅ (29 tests for QueryBuilder, InsertBuilder, UpdateBuilder, DeleteBuilder, Database)
- [x] Integration tests for API routes ✅ (route existence tests in test_users.py pass)

### Remaining Deployment Verification

- [ ] User can authenticate via Cognito (requires deployment)
- [ ] First login auto-creates user in Aurora users table (requires deployment)
- [ ] Subsequent logins find existing user (requires deployment)
- [ ] Audio upload/download works via S3 (requires deployment)
- [ ] All existing API endpoints work (requires deployment)

---

## Environment Variables

| Variable | Source | Description |
|----------|---------|-------------|
| `COGNITO_REGION` | GitHub Variables | AWS region (eu-west-1) |
| `COGNITO_USER_POOL_ID` | GitHub Variables | Cognito User Pool ID |
| `COGNITO_CLIENT_ID` | GitHub Variables | Cognito App Client ID |
| `AURORA_ENDPOINT` | GitHub Variables | Aurora cluster endpoint |
| `AUDIO_BUCKET` | GitHub Variables | S3 bucket for audio |
| `DB_CREDENTIALS_ARN` | GitHub Variables | Secrets Manager ARN for DB password |
| `SSM_PARAMETER_PATH` | GitHub Variables | SSM parameter path prefix |

---

## Auto-Create User Flow

```
1. User authenticates via Cognito
2. Backend receives JWT token
3. JWT validated successfully
4. Extract sub (user_id) and email from token
5. Query Aurora: SELECT * FROM users WHERE id = sub
6. If user NOT found:
   INSERT INTO users (id, email, created_at) VALUES (sub, email, NOW())
7. Return CurrentUser with id and email
```

---

## Cognito JWT Claims Available

| Claim | Description |
|-------|-------------|
| `sub` | Unique user ID (UUID) |
| `email` | User's email address |
| `email_verified` | Boolean confirming email verification |
| `cognito:username` | Username in user pool |

---

## Verification Checklist (Post-Phase 2)

- [x] Backend starts without Supabase env vars ✅
- [x] All API routes registered correctly ✅
- [x] Health endpoint works with Aurora ✅ (verified 2026-04-27 via ALB)
- [x] Service deployed and running on ECS ✅ (task RUNNING, count=1)

---

*Document version: 3.2 | Updated: 2026-04-27*
