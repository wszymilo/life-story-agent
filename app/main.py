import structlog
from api.deps import CurrentUser, get_current_user
from api.routes import audio, events, interview, tts, users
from config import get_settings
from db.client import get_supabase_client
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = structlog.get_logger()
settings = get_settings()

app = FastAPI(
    title="Life Story Preservation Agent",
    description="AI oral historian for capturing elderly users' life stories",
    version="0.1.0",
)

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
    supabase = await get_supabase_client()
    try:
        result = supabase.table("users").select("count", count="exact").execute()
        return {
            "status": "connected",
            "user_count": result.count,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/auth/me")
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """Get current authenticated user."""
    return {"id": str(current_user.id), "email": current_user.email}


app.include_router(users.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
