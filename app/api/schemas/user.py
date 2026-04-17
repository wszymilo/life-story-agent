import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    birth_date: date | None = None
    country_of_origin: str | None = Field(default=None, min_length=1)


class RelativeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    relationship: str = Field(min_length=1, max_length=100)


class RelativeResponse(BaseModel):
    id: uuid.UUID
    name: str
    relationship: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    birth_date: date | None
    country_of_origin: str | None
    created_at: datetime
    relatives: list[RelativeResponse] = []

    model_config = {"from_attributes": True}
