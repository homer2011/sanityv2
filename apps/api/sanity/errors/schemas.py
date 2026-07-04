from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """
    Standard error payload returned by exception handlers.
    """

    timestamp: str
    code: int
    message: str
    path: str


BadRequestResponse: dict[str, Any] = {
    "description": "Bad Request",
    "model": ErrorResponse,
}

UnauthorisedResponse: dict[str, Any] = {
    "description": "Unauthorised",
    "model": ErrorResponse,
}

ForbiddenResponse: dict[str, Any] = {
    "description": "Forbidden",
    "model": ErrorResponse,
}

ResourceNotFoundResponse: dict[str, Any] = {
    "description": "Resource Not Found",
    "model": ErrorResponse,
}

ResourceAlreadyExistsResponse: dict[str, Any] = {
    "description": "Resource Already Exists",
    "model": ErrorResponse,
}

ServiceUnavailableResponse: dict[str, Any] = {
    "description": "Service Unavailable",
    "model": ErrorResponse,
}
