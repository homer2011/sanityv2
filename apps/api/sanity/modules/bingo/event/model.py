from datetime import datetime
from enum import StrEnum

from apps.api.sanity.common.utils import utc_now
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from sanity.db.models import RecordModel


# TODO: consider persisted lifecycle
# TODO: consider soft-delete
class Event(RecordModel):
    class Status(StrEnum):
        DRAFT = "DRAFT"
        SCHEDULED = "SCHEDULED"
        LIVE = "LIVE"
        ENDED = "ENDED"

    __tablename__ = "events"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
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
    def status(self) -> Status:
        if self.starts_at is None or self.ends_at is None:
            return self.Status.DRAFT

        now = utc_now()
        if now < self.starts_at:
            return self.Status.SCHEDULED

        if now < self.ends_at:
            return self.Status.LIVE

        return self.Status.ENDED
