from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import TileType


class TileCreate(BaseModel):
    row_idx: int = Field(ge=0)
    col_idx: int = Field(ge=0)
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    tile_type: TileType
    target_value: int = Field(gt=0)
    reward_points: int = Field(gt=0)


class TileUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    tile_type: Optional[TileType] = None
    target_value: Optional[int] = Field(default=None, gt=0)
    reward_points: Optional[int] = Field(default=None, gt=0)


class TileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    board_id: int
    row_idx: int
    col_idx: int
    title: str
    description: Optional[str]
    tile_type: TileType
    target_value: int
    reward_points: int
    created_at: datetime
    updated_at: Optional[datetime]
