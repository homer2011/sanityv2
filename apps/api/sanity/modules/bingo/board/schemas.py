from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from ..tile.schemas import TileRead


class BoardUpdate(BaseModel):
    rows: Optional[int] = Field(default=None, ge=1, le=10)
    cols: Optional[int] = Field(default=None, ge=1, le=10)


class BoardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    rows: int
    cols: int
    created_at: datetime
    updated_at: Optional[datetime]


class BoardReadWithTiles(BoardRead):
    tiles: list["TileRead"]
