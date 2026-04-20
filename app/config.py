import os
from functools import lru_cache

from dotenv import find_dotenv, load_dotenv

# Load env from project root
load_dotenv(find_dotenv())


class Settings:
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    tts_model: str = "gpt-4o-mini-tts"
    environment: str = "development"
    log_level: str = "info"
    cors_origins: list[str] = ["http://localhost:5173"]
    max_meta_story_select: int = 10

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.tts_model = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "info")
        cors = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        self.cors_origins = [s.strip() for s in cors.split(",")]
        self.max_meta_story_select = int(os.getenv("MAX_META_STORY_SELECT", "10"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
