from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sanity.common.utils import utc_now
from sanity.db.models import RecordModel

from .enums import EventStatus

if TYPE_CHECKING:
    from ..board.model import Board


# TODO: consider persisted lifecycle
# TODO: consider soft-delete
class Event(RecordModel):
    __tablename__ = "events"

    name: Mapped[str] = mapped_column(
        CITEXT,
        unique=True,
        nullable=False,
        index=True,
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    board: Mapped["Board"] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def status(self) -> EventStatus:
        if self.starts_at is None or self.ends_at is None:
            return EventStatus.DRAFT

        now = utc_now()
        if now < self.starts_at:
            return EventStatus.SCHEDULED

        if now < self.ends_at:
            return EventStatus.LIVE

        return EventStatus.ENDED
