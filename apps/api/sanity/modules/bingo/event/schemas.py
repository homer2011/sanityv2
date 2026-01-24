from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class EventPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)


class EventBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]


class EventRead(EventBase):
    created_at: datetime
    updated_at: Optional[datetime]
