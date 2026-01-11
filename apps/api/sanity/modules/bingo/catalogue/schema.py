from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BossCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    ehb: Decimal = Field(gt=0)


class BossUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    ehb: Optional[Decimal] = Field(default=None, gt=0)


class BossRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ehb: Decimal
    created_at: datetime
    updated_at: Optional[datetime]


class BossReadWithItems(BossRead):
    items: list["ItemRead"]


class ItemCreate(BaseModel):
    boss_id: int
    name: str = Field(min_length=1, max_length=255)
    point_value: int = Field(ge=0)
    drop_rate: int = Field(gt=0)


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    point_value: Optional[int] = Field(default=None, ge=0)
    drop_rate: Optional[int] = Field(default=None, gt=0)


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    boss_id: int
    name: str
    point_value: int
    drop_rate: int
    created_at: datetime
    updated_at: Optional[datetime]
