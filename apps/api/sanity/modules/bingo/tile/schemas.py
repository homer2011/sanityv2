from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .enums import TileType


class TileCreate(BaseModel):
    name: str
    description: Optional[str]
    row_idx: int
    col_idx: int
    point_value: int
    type: TileType


class TilePatch(BaseModel):
    name: Optional[str]
    description: Optional[str]
    col_idx: Optional[int]
    row_idx: Optional[int]
    point_value: Optional[int]
    type: Optional[TileType]


class TileBase(BaseModel):
    name: str
    description: Optional[str]
    col_idx: int
    row_idx: int
    point_value: int
    type: TileType


class TileRead(TileBase):
    created_at: datetime
    updated_at: Optional[datetime]
