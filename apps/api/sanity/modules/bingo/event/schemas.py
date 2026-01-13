from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from sanity.modules.bingo.board.schemas import BoardReadWithTiles

from .enums import EventStatus, EventType


class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: EventType = EventType.TRADITIONAL
    starts_at: datetime
    ends_at: datetime


class EventUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    type: Optional[EventType] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: EventType
    status: EventStatus
    starts_at: datetime
    ends_at: datetime
    created_at: datetime
    updated_at: Optional[datetime]


class EventReadList(BaseModel):
    items: List[EventRead]
    total: int


class EventReadWithBoard(EventRead):
    board: "BoardReadWithTiles"
