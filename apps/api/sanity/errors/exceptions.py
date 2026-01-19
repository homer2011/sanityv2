class SanityException(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class BadRequest(SanityException):
    def __init__(self, status_code: int = 400, message: str = "Bad request") -> None:
        super().__init__(status_code, message)


class Unauthorised(SanityException):
    def __init__(self, status_code: int = 401, message: str = "Unauthorised") -> None:
        super().__init__(status_code, message)


class Forbidden(SanityException):
    def __init__(self, status_code: int = 403, message: str = "Forbidden") -> None:
        super().__init__(status_code, message)


class ResourceNotFound(SanityException):
    def __init__(self, status_code: int = 404, message: str = "Resource not found") -> None:
        super().__init__(status_code, message)


class ResourceAlreadyExists(SanityException):
    def __init__(self, status_code: int = 409, message: str = "Resource already exists") -> None:
        super().__init__(status_code, message)


class InternalServerError(SanityException):
    def __init__(self, status_code: int = 500, message: str = "Internal Server Error") -> None:
        super().__init__(status_code, message)
