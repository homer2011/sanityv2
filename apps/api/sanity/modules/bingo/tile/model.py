from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from sanity.db.models import RecordModel

from .enums import TileType


class Tile(RecordModel):
    __tablename__ = "tile"
    __table_args__ = (UniqueConstraint("board_id", "row_idx", "col_idx"),)

    board_id: Mapped[int] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    row_idx: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    col_idx: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tile_type: Mapped[TileType] = mapped_column(
        SAEnum(TileType, name="tile_type"),
        nullable=False,
        index=True,
    )

    target_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reward_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
