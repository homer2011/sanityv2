from typing import Annotated, Sequence

from fastapi import Query
from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """
    Request schema for any paged API.
    """

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)


PageQueryParams = Annotated[PageParams, Query()]  # type alias


class PageResponse[T](BaseModel):
    """
    Response schema for any paged API.
    """

    offset: int
    limit: int
    total: int
    items: Sequence[T]


class ListResponse[T](BaseModel):
    """
    Response schema for any list API.
    """

    total: int
    items: Sequence[T]
