from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sanity.db.models import RecordModel

from ..tile.model import Tile


class Board(RecordModel):
    __tablename__ = "boards"
    __table_args__ = (UniqueConstraint("event_id"),)

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
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
