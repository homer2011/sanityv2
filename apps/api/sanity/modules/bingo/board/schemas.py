from pydantic import BaseModel

from .enums import BoardType


class BoardCreate(BaseModel):
    type: BoardType
    rows: int
    cols: int


class BoardBase(BaseModel):
    type: BoardType
    rows: int
    cols: int


class BoardRead(BoardBase):
    pass
