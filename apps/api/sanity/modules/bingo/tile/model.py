from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sanity.db.models import RecordModel

from .enums import TileType

if TYPE_CHECKING:
    from ..board.model import Board


class Tile(RecordModel):
    __tablename__ = "tiles"
    __table_args__ = (
        UniqueConstraint("board_id", "row", "col"),
        CheckConstraint("row_idx >= 0", name="tile_row_idx_not_negative"),
        CheckConstraint("col_idx >= 0", name="tile_col_idx_not_negative"),
    )

    # TODO: allowed items for this tile --> must use snapshots to preserve item "at the time"
    # TODO: position cannot be out of bounds of board size

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    completion_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    row_idx: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    col_idx: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    type: Mapped[TileType] = mapped_column(
        Enum(TileType, name="board_type"),
        nullable=False,
        index=True,
    )

    # TODO: tile type -> allowed items/submissions/whatever

    board_id: Mapped[int] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    board: Mapped["Board"] = relationship(
        back_populates="tiles",
    )


class TileAccepts(RecordModel):
    __tablename__ = "tile_accepts"
