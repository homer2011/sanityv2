from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from sanity.common.utils import utc_now
from sanity.db.models import RecordModel

from .enums import EventStatus


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
