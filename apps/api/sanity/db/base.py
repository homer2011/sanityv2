from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sanity.common.utils import utc_now


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    docs: https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.DeclarativeBase
    """

    __abstract__ = True


class IdModel(Base):
    """
    Base model to include support for an integer-based primary key.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )


class TimestampModel(Base):
    """
    Base model to include support for UTC auditing timestamps.

    - `created_at` is set once on INSERT
    - `updated_at` is automatically bumped on UPDATE
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        onupdate=utc_now,
    )


class RecordModel(IdModel, TimestampModel):
    """
    Base model to include support for both an integer-based primary key
    and UTC auditing timestamp fields.
    """

    __abstract__ = True
