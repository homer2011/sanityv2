from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sanity.db.models.base import Base, TimestampMixin


class Boss(Base, TimestampMixin):
    __tablename__ = "boss"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    ehb: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    items: Mapped[list["Item"]] = relationship(
        back_populates="boss",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Item(Base, TimestampMixin):
    __tablename__ = "item"
    __table_args__ = (UniqueConstraint("boss_id", "name"),)

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    boss_id: Mapped[int] = mapped_column(
        ForeignKey("boss.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    point_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    drop_rate: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    boss: Mapped["Boss"] = relationship(
        back_populates="items",
    )
