import uuid

from api.deps import CurrentUser, get_current_user
from api.schemas.user import (
    LanguageUpdate,
    RelativeCreate,
    RelativeResponse,
    UserResponse,
    UserUpdate,
)
from api.utils import serialize_update_data
from config import get_settings
from db.deps import get_user_repo
from db.repositories import UserRepository
from fastapi import APIRouter, Depends, HTTPException, Request, status

settings = get_settings()

router = APIRouter(prefix="/users", tags=["users"])


async def get_user_with_relatives(user_repo: UserRepository, user_id: str, current_user: CurrentUser | None = None) -> UserResponse:
    user_data = None
    if current_user and str(current_user.id) == str(user_id):
        user_data = {"id": current_user.id, "email": current_user.email}

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User data not available",
        )

    relatives = await user_repo.fetch_relatives(user_id)
    relatives_resp = [RelativeResponse(**r) for r in relatives]

    is_admin = user_data.get("email") == settings.admin_email
    user_data_full = await user_repo.fetch_by_email(user_data["email"])
    if not user_data_full:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(
        id=user_data_full["id"],
        email=user_data_full["email"],
        name=user_data_full.get("name"),
        birth_date=user_data_full.get("birth_date"),
        country_of_origin=user_data_full.get("country_of_origin"),
        preferred_language=user_data_full.get("preferred_language", "pl"),
        created_at=user_data_full["created_at"],
        relatives=relatives_resp,
        is_admin=is_admin,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    return await get_user_with_relatives(user_repo, current_user.id, current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    request: Request,
    user_update: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data:
        return await get_user_with_relatives(user_repo, current_user.id, current_user)

    serialize_update_data(update_data)
    await user_repo.update_profile(str(current_user.id), update_data)

    return await get_user_with_relatives(user_repo, current_user.id, current_user)


@router.post("/me/relatives", response_model=RelativeResponse, status_code=status.HTTP_201_CREATED)
async def add_relative(
    relative_create: RelativeCreate,
    current_user: CurrentUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    result = await user_repo.insert_relative(
        str(current_user.id),
        relative_create.name,
        relative_create.relationship,
    )
    return RelativeResponse(**result)


@router.delete("/me/relatives/{relative_id}", status_code=status.HTTP_200_OK)
async def delete_relative(
    relative_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    await user_repo.delete_relative(str(relative_id), str(current_user.id))
    return {"success": True}


@router.put("/me/language", response_model=UserResponse)
async def update_language(
    language_update: LanguageUpdate,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    await user_repo.update_profile(
        str(current_user.id),
        {"preferred_language": language_update.preferred_language},
    )
    return await get_user_with_relatives(user_repo, current_user.id, current_user)
