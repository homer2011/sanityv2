from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sanity.common.utils import utc_now

from .enums import EventStatus


def normalise_utc(dt: datetime | None, *, field_name: str) -> datetime | None:
    """Validate timezone awareness and normalise to UTC."""

    def is_tz_aware(dt: datetime) -> bool:
        """True if dt is timezone-aware."""
        return dt.tzinfo is not None and dt.utcoffset() is not None

    if dt is None:
        return

    if not is_tz_aware(dt):
        raise ValueError(f"{field_name} must be timezone-aware (e.g. 'Z' or '+00:00')")

    return dt.astimezone(UTC)


class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class EventPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_schedule(self):
        starts_at = normalise_utc(self.starts_at, field_name="starts_at")
        ends_at = normalise_utc(self.ends_at, field_name="ends_at")

        if starts_at is None and ends_at is None:
            return self  # allow schedule clearing

        if starts_at is None or ends_at is None:
            raise ValueError("starts_at and ends_at must be provided together")

        if starts_at < utc_now():
            raise ValueError("cannot schedule event in the past")

        if starts_at >= ends_at:
            raise ValueError("starts_at must precede ends_at")

        self.starts_at = starts_at
        self.ends_at = ends_at
        return self


class EventBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    status: EventStatus


class EventRead(EventBase):
    created_at: datetime
    updated_at: Optional[datetime]
