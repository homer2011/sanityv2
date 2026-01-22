class SanityException(Exception):
    status_code: int
    default_message: str

    def __init__(self, custom_message: str) -> None:
        self.message = custom_message or self.default_message
        super().__init__(self.message)


class BadRequest(SanityException):
    status_code = 400
    default_message = "Bad request"


class Unauthorised(SanityException):
    status_code = 401
    default_message = "Unauthorised"


class Forbidden(SanityException):
    status_code = 403
    default_message = "Forbidden"


class ResourceNotFound(SanityException):
    status_code = 404
    default_message = "Resource not found"


class ResourceAlreadyExists(SanityException):
    status_code = 409
    default_message = "Resource already exists"


class ServiceUnavailable(SanityException):
    status_code = 503
    default_message = "Service unavailable"
