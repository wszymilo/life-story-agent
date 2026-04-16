from supabase import create_client, AsyncClient
from config import get_settings

settings = get_settings()


async def get_supabase_client() -> AsyncClient:
    """Get async Supabase client for database operations."""
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_sync_supabase_client():
    """Get sync Supabase client for storage operations."""
    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_service_key)
