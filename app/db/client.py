import asyncio
import json
from typing import Any

import asyncpg
import boto3
from botocore.exceptions import ClientError

from config import get_settings

settings = get_settings()

_pool = None
_secrets_cache = None


async def get_db_pool() -> asyncpg.Pool:
    """Get or create asyncpg connection pool for Aurora."""
    global _pool
    if _pool is None:
        credentials = await _get_db_credentials()
        dsn = f"postgresql://{credentials['username']}:{credentials['password']}@{settings.aurora_endpoint}/life_story_agent"
        _pool = asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=10,
            command_timeout=60,
        )
    return _pool


async def _get_db_credentials() -> dict[str, str]:
    """Get DB credentials from AWS Secrets Manager."""
    global _secrets_cache
    if _secrets_cache is not None:
        return _secrets_cache

    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=settings.cognito_region,
    )

    try:
        response = client.get_secret_value(SecretId=settings.db_credentials_arn)
        _secrets_cache = json.loads(response["SecretString"])
        return _secrets_cache
    except ClientError as e:
        raise RuntimeError(f"Failed to get DB credentials: {e}")


async def execute_query(
    query: str,
    *args: Any,
    fetch: bool = True,
    single: bool = False,
) -> list[asyncpg.Record] | asyncpg.Record | None:
    """Execute a query using the connection pool."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        if fetch:
            if single:
                return await conn.fetchrow(query, *args)
            return await conn.fetch(query, *args)
        return await conn.execute(query, *args)


async def execute_single(query: str, *args: Any) -> asyncpg.Record | None:
    """Execute a query and return a single row."""
    return await execute_query(query, *args, fetch=True, single=True)


async def close_db_pool() -> None:
    """Close the connection pool (call on shutdown)."""
    global _pool, _secrets_cache
    if _pool is not None:
        _pool.close()
        _pool = None
        _secrets_cache = None


def create_storage_client(timeout: int | float = 120) -> Any:
    """Placeholder - storage now handled by boto3 S3 client."""
    raise NotImplementedError("Use boto3 S3 client instead of Supabase storage")


async def get_supabase_client() -> Any:
    """Placeholder - Supabase client removed."""
    raise NotImplementedError("Use asyncpg pool via get_db_pool() instead")
