from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sanity.db.models import RecordModel

from .enums import BoardType

if TYPE_CHECKING:
    from ..event.model import Event
    from ..tile.model import Tile


class Board(RecordModel):
    __tablename__ = "boards"
    __table_args__ = (
        CheckConstraint("rows > 0 AND rows < 11", name="board_rows_range"),  # range 1 - 10
        CheckConstraint("cols > 0 AND cols < 11", name="board_cols_range"),  # range 1 - 10
    )

    type: Mapped[BoardType] = mapped_column(
        Enum(BoardType, name="board_type"),
        nullable=False,
        default=BoardType.TRADITIONAL,
        index=True,
    )

    rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    cols: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )

    event: Mapped["Event"] = relationship(
        back_populates="board",
    )

    tiles: Mapped[list["Tile"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Tile.row, Tile.col",
    )
