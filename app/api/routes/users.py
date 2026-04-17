import uuid
from datetime import datetime

from api.deps import CurrentUser, get_current_user
from api.schemas.user import (
    RelativeCreate,
    RelativeResponse,
    UserResponse,
    UserUpdate,
)
from db.client import get_supabase_client
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/users", tags=["users"])


async def get_user_with_relatives(user_id: uuid.UUID) -> UserResponse:
    """Fetch user profile with their relatives."""
    supabase = await get_supabase_client()

    user_response = await supabase.table("users").select("*").eq("id", str(user_id)).execute()
    if not user_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_data = user_response.data[0]

    relatives_response = (
        await supabase.table("relatives").select("*").eq("user_id", str(user_id)).execute()
    )
    relatives = [RelativeResponse(**r) for r in relatives_response.data]

    return UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        name=user_data.get("name"),
        birth_date=user_data.get("birth_date"),
        country_of_origin=user_data.get("country_of_origin"),
        created_at=user_data["created_at"],
        relatives=relatives,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUser = Depends(get_current_user)):
    """Get current user profile with relatives."""
    return await get_user_with_relatives(current_user.id)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update current user profile."""
    supabase = await get_supabase_client()

    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data:
        return await get_user_with_relatives(current_user.id)

    update_data["updated_at"] = datetime.utcnow().isoformat()

    response = (
        await supabase.table("users").update(update_data).eq("id", str(current_user.id)).execute()
    )

    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return await get_user_with_relatives(current_user.id)


@router.post("/me/relatives", response_model=RelativeResponse, status_code=status.HTTP_201_CREATED)
async def add_relative(
    relative_create: RelativeCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Add a relative to current user's profile."""
    supabase = await get_supabase_client()

    relative_data = {
        "user_id": str(current_user.id),
        "name": relative_create.name,
        "relationship": relative_create.relationship,
    }

    response = await supabase.table("relatives").insert(relative_data).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create relative"
        )

    return RelativeResponse(**response.data[0])


@router.delete("/me/relatives/{relative_id}", status_code=status.HTTP_200_OK)
async def delete_relative(
    relative_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a relative from current user's profile."""
    supabase = await get_supabase_client()

    existing = (
        await supabase.table("relatives")
        .select("id")
        .eq("id", str(relative_id))
        .eq("user_id", str(current_user.id))
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relative not found")

    await supabase.table("relatives").delete().eq("id", str(relative_id)).execute()

    return {"success": True}
