from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Numeric
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sanity.db.models import RecordModel

if TYPE_CHECKING:
    from ..item.model import Item


class Boss(RecordModel):
    __tablename__ = "bosses"
    __table_args__ = (CheckConstraint("ehb > 0", name="boss_ehb_gt_0"),)

    name: Mapped[str] = mapped_column(
        CITEXT,
        unique=True,
        nullable=False,
        index=True,
    )

    ehb: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    uniques: Mapped[list["Item"]] = relationship(
        back_populates="boss",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
