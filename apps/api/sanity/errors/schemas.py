from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """
    Standard error payload returned by exception handlers.
    """

    timestamp: str
    code: int
    message: str
    path: str
