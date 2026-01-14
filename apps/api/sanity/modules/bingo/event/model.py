from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sanity.db.models import RecordModel

from .enums import EventStatus, EventType

if TYPE_CHECKING:
    from ..board.model import Board


class Event(RecordModel):
    __tablename__ = "events"
    __table_args__ = (CheckConstraint("ends_at > starts_at", name="event_schedule_valid"),)

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    type: Mapped[EventType] = mapped_column(
        SAEnum(EventType, name="event_type"),
        nullable=False,
        default=EventType.TRADITIONAL,
        index=True,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=None,
        index=True,
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=None,
        index=True,
    )

    @property
    def status(self) -> EventStatus:
        """
        Derived status enum based on persisted scheduling timestamps.
        """
        now = datetime.now(UTC)
        if now < self.starts_at:
            return EventStatus.SCHEDULED
        if now <= self.ends_at:
            return EventStatus.ACTIVE

        return EventStatus.COMPLETED

    board: Mapped["Board"] = relationship(
        "Board",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
