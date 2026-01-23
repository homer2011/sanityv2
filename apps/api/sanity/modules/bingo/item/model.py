from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sanity.db.models import RecordModel

if TYPE_CHECKING:
    from ..boss.model import Boss


class Item(RecordModel):
    __tablename__ = "items"
    __table_args__ = (UniqueConstraint("boss_id", "name"),)

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    drop_rate: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    point_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    boss_id: Mapped[int] = mapped_column(
        ForeignKey("bosses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    boss: Mapped["Boss"] = relationship(
        back_populates="items",
    )

    @property
    def hours_to_drop(self) -> Decimal:
        return Decimal(self.drop_rate) / self.boss.ehb
