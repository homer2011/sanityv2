from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sanity.db.models import Base, TimestampMixin


class Board(Base, TimestampMixin):
    __tablename__ = "board"
    __table_args__ = (UniqueConstraint("event_id"),)

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey("event.id", ondelete="CASCADE"),
        nullable=False,
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

    tiles: Mapped[list["Tile"]] = relationship(
        uselist=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Tile.row_idx, Tile.col_idx",
    )


class TileType(str, Enum):
    KC = "KC"
    UNIQUE = "UNIQUE"
    POINTS = "POINTS"


class Tile(Base, TimestampMixin):
    __tablename__ = "tile"
    __table_args__ = (UniqueConstraint("board_id", "row_idx", "col_idx"),)

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    board_id: Mapped[int] = mapped_column(
        ForeignKey("board.id", ondelete="CASCADE"),
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
