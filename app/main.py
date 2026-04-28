from api.deps import CurrentUser, get_current_user
from api.langfuse_config import init_langfuse
from api.logging_config import RequestLoggingMiddleware, configure_logging, get_logger
from api.rate_limit_config import limiter
from api.routes import events, interview, tts, users, evaluations
from api.sentry_config import init_sentry
from config import get_settings
from db.client import get_supabase_client
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

settings = get_settings()
configure_logging()
logger = get_logger()

app = FastAPI(
    title="Life Story Preservation Agent",
    description="AI oral historian for capturing elderly users' life stories",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment verification."""
    return {"status": "ok"}


async def _check_db_health():
    """Shared helper to verify database connectivity."""
    supabase = await get_supabase_client()
    try:
        result = supabase.table("users").select("count", count="exact").execute()
        return {"status": "connected", "user_count": result.count}
    except Exception as e:
        logger.error("db_check_failed", error=str(e))
        return {"status": "error", "error": str(e)}


@app.get("/health/ready")
async def health_ready_check():
    """Readiness check including database connectivity."""
    result = await _check_db_health()
    if result["status"] == "connected":
        return {
            "status": "ready",
            "database": "connected",
            "user_count": result["user_count"],
        }
    return {"status": "not_ready", "database": "error", "error": result.get("error")}


@app.get("/")
async def root():
    """Root endpoint returning app info."""
    return {
        "name": "Life Story Preservation Agent",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/db-check")
async def db_check():
    """Verify database connectivity."""
    return await _check_db_health()


@app.get("/auth/me")
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """Get current authenticated user."""
    return {"id": str(current_user.id), "email": current_user.email}


app.include_router(users.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
app.include_router(evaluations.router)


@app.on_event("startup")
async def startup():
    """Log application startup and init Sentry/LangFuse/Firebase."""
    init_sentry()
    init_langfuse()

    from services.firebase_auth import init_firebase
    if settings.firebase_credentials:
        try:
            init_firebase(settings.firebase_credentials)
            logger.info("firebase_auth_initialized", project_id=settings.firebase_project_id)
        except Exception as e:
            logger.error("firebase_init_failed", error=str(e))

    logger.info(
        "application_started",
        environment=settings.environment,
        version="0.1.0",
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Capture unhandled exceptions with Sentry."""
    from api.sentry_config import capture_exception
    capture_exception(exc, path=str(request.url.path))
    logger.error("unhandled_exception", error=str(exc), path=str(request.url.path))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.on_event("shutdown")
async def shutdown():
    """Log application shutdown."""
    logger.info("application_shutdown")
