import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from db.client import get_supabase_client

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
