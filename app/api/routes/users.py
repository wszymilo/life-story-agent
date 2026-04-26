import uuid
from typing import Any

from api.deps import CurrentUser, get_current_user
from api.schemas.user import (
    LanguageUpdate,
    RelativeCreate,
    RelativeResponse,
    UserResponse,
    UserUpdate,
)
from api.utils import require_data, serialize_update_data
from config import get_settings
from db.query import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status

settings = get_settings()


router = APIRouter(prefix="/users", tags=["users"])


async def get_user_with_relatives(request: Request, user_id: uuid.UUID) -> UserResponse:
    """Fetch user profile with their relatives."""
    user_data: dict[str, Any] | None = getattr(request.state, "user_data", None)

    if user_data is None or str(user_data.get("id")) != str(user_id):
        db = await get_db()
        user_response = db.table("users").select("*").eq("id", user_id).execute()
        user_data = require_data(user_response, "User not found")

    db = await get_db()
    relatives_response = (
        db.table("relatives").select("*").eq("user_id", user_id).execute()
    )
    relatives = [RelativeResponse(**r) for r in relatives_response.data]

    is_admin = user_data.get("email") == settings.admin_email

    return UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        name=user_data.get("name"),
        birth_date=user_data.get("birth_date"),
        country_of_origin=user_data.get("country_of_origin"),
        preferred_language=user_data.get("preferred_language", "pl"),
        created_at=user_data["created_at"],
        relatives=relatives,
        is_admin=is_admin,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get current user profile with relatives."""
    return await get_user_with_relatives(request, current_user.id)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    request: Request,
    user_update: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update current user profile."""
    db = await get_db()

    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data:
        return await get_user_with_relatives(request, current_user.id)

    serialize_update_data(update_data)

    response = db.table("users").update(update_data).eq("id", current_user.id).execute()
    require_data(response, "User not found")

    return await get_user_with_relatives(request, current_user.id)


@router.post("/me/relatives", response_model=RelativeResponse, status_code=status.HTTP_201_CREATED)
async def add_relative(
    relative_create: RelativeCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Add a relative to current user's profile."""
    db = await get_db()

    relative_data = {
        "user_id": str(current_user.id),
        "name": relative_create.name,
        "relationship": relative_create.relationship,
    }

    response = db.table("relatives").insert(relative_data).execute()
    require_data(response, "Failed to create relative")

    return RelativeResponse(**response.data[0])


@router.delete("/me/relatives/{relative_id}", status_code=status.HTTP_200_OK)
async def delete_relative(
    relative_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a relative from current user's profile."""
    db = await get_db()

    existing = (
        db.table("relatives")
        .select("id")
        .eq("id", relative_id)
        .eq("user_id", current_user.id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relative not found")

    db.table("relatives").delete().eq("id", relative_id).execute()

    return {"success": True}


@router.put("/me/language", response_model=UserResponse)
async def update_language(
    language_update: LanguageUpdate,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update preferred language for AI-generated content."""
    db = await get_db()

    response = (
        db.table("users")
        .update({"preferred_language": language_update.preferred_language})
        .eq("id", current_user.id)
        .execute()
    )
    require_data(response, "User not found")

    return await get_user_with_relatives(request, current_user.id)
