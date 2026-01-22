from decimal import Decimal

from pydantic import computed_field

from ..boss.schemas import BossBase, BossRead
from ..item.schemas import ItemBase, ItemRead

"""
Combined Boss/Item DTOs located here to prevent circular importing.
"""


class BossReadWithItems(BossRead):
    items: list[ItemBase]


class ItemReadWithBoss(ItemRead):
    boss: BossBase

    @computed_field
    def hours_to_drop(self) -> Decimal:
        return Decimal(self.drop_rate) / self.boss.ehb
