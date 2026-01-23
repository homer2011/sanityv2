from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..item.schemas import ItemBase

if TYPE_CHECKING:
    from ..item.schemas import ItemBase


class BossCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    ehb: Decimal = Field(gt=0)


class BossPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    ehb: Optional[Decimal] = Field(default=None, gt=0)


class BossBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ehb: Decimal = Field(examples=["50.00"])


class BossRead(BossBase):
    created_at: datetime
    updated_at: Optional[datetime]


class BossReadWithItems(BossRead):
    items: list["ItemBase"]
