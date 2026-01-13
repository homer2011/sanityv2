from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sanity.db.models import Base, TimestampMixin
from sanity.modules.bingo.board.models import Board


class EventType(str, Enum):
    TRADITIONAL = "TRADITIONAL"
    LEVELS = "LEVELS"


class EventStatus(str, Enum):
    SCHEDULED = "SCHEDULED"  # Editable
    ACTIVE = "ACTIVE"  # Moderation only
    COMPLETED = "COMPLETED"  # Read only


class Event(Base, TimestampMixin):
    __tablename__ = "event"
    __table_args__ = (CheckConstraint("ends_at > starts_at", name="event_schedule_valid"),)

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

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
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
