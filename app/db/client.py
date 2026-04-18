from typing import Union

from config import get_settings

from supabase import AsyncClient, Client, create_client
from supabase.lib.client_options import SyncClientOptions

settings = get_settings()


def create_storage_client(timeout: Union[int, float] = 120) -> Client:
    """Create a Supabase client with custom storage timeout."""
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key,
        options=SyncClientOptions(storage_client_timeout=timeout),
    )


async def get_supabase_client() -> AsyncClient:
    """Get async Supabase client for database operations."""
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_sync_supabase_client():
    """Get sync Supabase client for storage operations with default timeout."""
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key,
        options=SyncClientOptions(storage_client_timeout=120),
    )
