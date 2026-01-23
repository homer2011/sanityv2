from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    drop_rate: int = Field(gt=0)
    point_value: int = Field(ge=0)


class ItemPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    drop_rate: Optional[int] = Field(default=None, gt=0)
    point_value: Optional[int] = Field(default=None, ge=0)


class ItemBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    drop_rate: int
    point_value: int


class ItemRead(ItemBase):
    created_at: datetime
    updated_at: Optional[datetime]


class ItemReadWithCtx(ItemRead):
    hours_to_drop: Decimal
